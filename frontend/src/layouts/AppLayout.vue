<template>
  <div class="app-layout">
    <aside class="sidebar">
      <div class="logo">
        <el-icon :size="24" color="#3B82F6"><Briefcase /></el-icon>
        <span>面试助手</span>
      </div>
      <nav class="nav-menu">
        <router-link
          v-for="item in menuItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: route.path === item.path }"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <span>{{ item.label }}</span>
          <el-badge
            v-if="item.badge && unreadCount > 0"
            :value="unreadCount > 99 ? '99+' : unreadCount"
            :max="99"
            class="nav-badge"
          />
        </router-link>
      </nav>
      <div class="sidebar-footer">
        <UserSidebarMenu />
      </div>
    </aside>
    <main class="main-content">
      <router-view />
    </main>
    <LoginDialog />
    <RegisterDialog />
    <ProfileEditDialog
      :model-value="store.showProfileEditDialog"
      @update:model-value="(v: boolean) => (store.showProfileEditDialog = v)"
      @saved="onProfileSaved"
    />
  </div>
</template>

<script setup lang="ts">
import { onMounted, onUnmounted, computed, watch } from 'vue'
import { consumeFlashNotice } from '@/utils/flashNotice'
import { useRoute } from 'vue-router'
import { Briefcase, Document, Share, User, Bell } from '@element-plus/icons-vue'
import { useUserStore } from '@/stores/user'
import LoginDialog from '@/components/auth/LoginDialog.vue'
import RegisterDialog from '@/components/auth/RegisterDialog.vue'
import UserSidebarMenu from '@/components/layout/UserSidebarMenu.vue'
import ProfileEditDialog from '@/components/profile/ProfileEditDialog.vue'

const route = useRoute()
const store = useUserStore()
const unreadCount = computed(() => store.unreadCount)

const menuItems = [
  { path: '/interviews', label: '面试复盘', icon: Briefcase },
  { path: '/resumes', label: '简历管理', icon: Document },
  { path: '/share', label: '面试分享', icon: Share },
  { path: '/profile', label: '我的主页', icon: User },
  { path: '/messages', label: '消息中心', icon: Bell, badge: true },
]

function onVisibilityChange() {
  if (document.visibilityState === 'visible' && store.isLoggedIn()) {
    void store.refreshUnread()
  }
}

onMounted(async () => {
  consumeFlashNotice()
  document.addEventListener('visibilitychange', onVisibilityChange)
  await store.fetchUser()
  if (store.isLoggedIn()) {
    await store.refreshUnread()
  }
})

onUnmounted(() => {
  document.removeEventListener('visibilitychange', onVisibilityChange)
})

watch(
  () => route.path,
  () => {
    if (store.isLoggedIn()) {
      void store.refreshUnread()
    }
  }
)

async function onProfileSaved() {
  await store.fetchUser()
  store.sessionTick++
}

</script>

<style scoped lang="scss">
.app-layout {
  display: flex;
  min-height: 100vh;
}
.sidebar {
  width: 220px;
  background: #fff;
  border-right: 1px solid #e2e8f0;
  display: flex;
  flex-direction: column;
  position: fixed;
  top: 0;
  left: 0;
  bottom: 0;
  z-index: 100;
}
.logo {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 20px 16px;
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
}
.nav-menu {
  flex: 1;
  padding: 8px 12px;
}
.nav-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  border-radius: 8px;
  color: #64748b;
  text-decoration: none;
  margin-bottom: 4px;
  font-size: 14px;
  position: relative;
  &:hover { background: #f1f5f9; color: #3b82f6; }
  &.active {
    background: #eff6ff;
    color: #3b82f6;
    font-weight: 500;
  }
}
.nav-badge {
  position: absolute;
  right: 12px;
  top: 50%;
  transform: translateY(-50%);
}
.sidebar-footer {
  padding: 8px;
  border-top: 1px solid #e2e8f0;
}
.main-content {
  flex: 1;
  margin-left: 220px;
  padding: 24px;
  min-height: 100vh;
}
</style>
