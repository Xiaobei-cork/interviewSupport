<template>
  <el-popover
    v-if="loggedIn"
    placement="top-start"
    :width="300"
    trigger="hover"
    :show-after="150"
    :hide-after="200"
    popper-class="user-sidebar-popover"
  >
    <template #reference>
      <div class="user-trigger">
        <el-avatar :size="36" :src="user?.avatar_url">{{ user?.username?.[0] || '?' }}</el-avatar>
        <div class="user-info">
          <span class="name">{{ user?.username }}</span>
          <span class="sub">悬停查看更多</span>
        </div>
        <el-icon class="arrow"><ArrowUp /></el-icon>
      </div>
    </template>

    <div class="popover-panel">
      <div class="panel-header">
        <el-avatar :size="52" :src="user?.avatar_url" class="header-avatar">
          {{ user?.username?.[0] }}
        </el-avatar>
        <div class="header-name">{{ user?.username }}</div>
        <div class="header-account">账号：{{ user?.account }}</div>
        <div v-if="user?.email || user?.phone" class="header-contact">
          {{ user?.email || user?.phone }}
        </div>
      </div>

      <div v-if="stats" class="stats-row">
        <div class="stat-item">
          <span class="num">{{ stats.interview_count }}</span>
          <span class="label">公开面试</span>
        </div>
        <div class="stat-item">
          <span class="num">{{ stats.like_count }}</span>
          <span class="label">获赞</span>
        </div>
        <div class="stat-item" @click="go('/messages')">
          <span class="num">{{ unreadCount || 0 }}</span>
          <span class="label">未读消息</span>
        </div>
      </div>

      <div class="menu-list">
        <div
          v-for="item in menuLinks"
          :key="item.key"
          class="menu-item"
          @click.stop="onMenuClick(item)"
        >
          <el-icon><component :is="item.icon" /></el-icon>
          <span class="label">{{ item.label }}</span>
          <el-badge v-if="item.badge && unreadCount > 0" :value="unreadCount" class="item-badge" />
          <el-icon class="chevron"><ArrowRight /></el-icon>
        </div>
      </div>

      <div class="menu-divider" />

      <div class="menu-item logout" @click="handleLogout">
        <el-icon><SwitchButton /></el-icon>
        <span class="label">退出登录</span>
      </div>
    </div>
  </el-popover>

  <div v-else class="user-trigger guest" @click="store.showLoginDialog = true">
    <el-avatar :size="36">?</el-avatar>
    <div class="user-info">
      <span class="name">未登录</span>
      <span class="sub login-link">立即登录</span>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch } from 'vue'
import { useRouter } from 'vue-router'
import {
  ArrowUp,
  ArrowRight,
  SwitchButton,
  User,
  EditPen,
  Briefcase,
  Document,
  Bell,
  Share,
} from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'
import { useUserStore } from '@/stores/user'
import { profileApi } from '@/api'

const router = useRouter()
const store = useUserStore()
const user = computed(() => store.user)
const unreadCount = computed(() => store.unreadCount)
const loggedIn = computed(() => store.isLoggedIn())

const stats = ref<{ interview_count: number; like_count: number } | null>(null)

const menuLinks = [
  { key: 'profile', path: '/profile', label: '我的主页', icon: User },
  { key: 'edit', path: '/profile', label: '编辑个人信息', icon: EditPen, edit: true },
  { key: 'interviews', path: '/interviews', label: '面试复盘', icon: Briefcase },
  { key: 'resumes', path: '/resumes', label: '简历管理', icon: Document },
  { key: 'share', path: '/share', label: '面试分享', icon: Share },
  { key: 'messages', path: '/messages', label: '消息中心', icon: Bell, badge: true },
]

watch(
  () => store.user?.id,
  async (id) => {
    if (!id) {
      stats.value = null
      return
    }
    try {
      const res = await profileApi.get(id) as {
        stats: { interview_count: number; like_count: number }
      }
      stats.value = res.stats
    } catch {
      stats.value = null
    }
  },
  { immediate: true }
)

function go(path: string, query?: Record<string, string>) {
  router.push({ path, query })
}

function onMenuClick(item: (typeof menuLinks)[number]) {
  if (item.edit) {
    void store.openProfileEdit()
    return
  }
  go(item.path)
}

async function handleLogout() {
  try {
    await ElMessageBox.confirm('确定要退出当前账号吗？', '退出登录', {
      confirmButtonText: '退出',
      cancelButtonText: '取消',
      type: 'warning',
      customClass: 'mac-alert-box',
      appendTo: document.body,
    })
    stats.value = null
    store.logout({ reload: true, flashMessage: '已退出登录' })
  } catch {
    /* cancelled */
  }
}
</script>

<style scoped lang="scss">
.user-trigger {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 12px 14px;
  cursor: pointer;
  border-radius: 8px;
  transition: background 0.2s;
  width: 100%;
  box-sizing: border-box;

  &:hover {
    background: #f1f5f9;
  }

  &.guest .login-link {
    color: #3b82f6;
  }

  .user-info {
    flex: 1;
    min-width: 0;
    display: flex;
    flex-direction: column;

    .name {
      font-size: 14px;
      font-weight: 500;
      color: #1e293b;
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }

    .sub {
      font-size: 12px;
      color: #94a3b8;
    }
  }

  .arrow {
    color: #94a3b8;
    font-size: 14px;
  }
}

.popover-panel {
  margin: -4px;
}

.panel-header {
  text-align: center;
  padding: 8px 12px 16px;
  border-bottom: 1px solid #f1f5f9;

  .header-avatar {
    margin-bottom: 8px;
    border: 2px solid #eff6ff;
  }

  .header-name {
    font-size: 16px;
    font-weight: 600;
    color: #1e293b;
    margin-bottom: 4px;
  }

  .header-account {
    font-size: 12px;
    color: #64748b;
  }

  .header-contact {
    font-size: 12px;
    color: #94a3b8;
    margin-top: 4px;
  }
}

.stats-row {
  display: flex;
  justify-content: space-around;
  padding: 14px 8px;
  border-bottom: 1px solid #f1f5f9;

  .stat-item {
    text-align: center;
    cursor: default;

    &:last-child {
      cursor: pointer;
      &:hover .label {
        color: #3b82f6;
      }
    }

    .num {
      display: block;
      font-size: 18px;
      font-weight: 600;
      color: #1e293b;
    }

    .label {
      font-size: 12px;
      color: #94a3b8;
    }
  }
}

.menu-list {
  padding: 6px 0;
}

.menu-item {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 10px 14px;
  cursor: pointer;
  font-size: 14px;
  color: #334155;
  transition: background 0.15s;

  &:hover {
    background: #f8fafc;
    color: #3b82f6;
  }

  .label {
    flex: 1;
  }

  .chevron {
    color: #cbd5e1;
    font-size: 14px;
  }

  &.logout {
    color: #64748b;

    &:hover {
      color: #ef4444;
      background: #fef2f2;
    }
  }
}

.menu-divider {
  height: 1px;
  background: #f1f5f9;
  margin: 4px 0;
}

.item-badge {
  margin-right: 4px;
}
</style>

<style lang="scss">
.user-sidebar-popover.el-popper {
  padding: 12px 8px !important;
  border-radius: 12px !important;
  box-shadow: 0 8px 30px rgba(0, 0, 0, 0.12) !important;
  border: 1px solid #e2e8f0 !important;
}
</style>
