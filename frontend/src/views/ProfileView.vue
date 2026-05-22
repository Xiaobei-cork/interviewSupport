<template>
  <div class="profile-page">
    <div v-if="!store.isLoggedIn()" class="page-card empty-login">
      <el-avatar :size="80">?</el-avatar>
      <p>当前未登录状态</p>
      <el-button type="primary" @click="store.showLoginDialog = true">立即登录</el-button>
    </div>

    <div v-else-if="loading" class="page-card" v-loading="true" style="min-height:200px" />

    <template v-else-if="profile">
      <div class="page-card profile-hero">
        <div class="hero-main">
          <div class="avatar-wrap" @click="openAvatarPicker">
            <el-avatar :size="88" :src="profile.user.avatar_url" class="hero-avatar">
              {{ profile.user.username[0] }}
            </el-avatar>
            <span class="avatar-edit-badge">
              <el-icon><Camera /></el-icon>
            </span>
          </div>
          <div class="hero-info">
            <div class="name-row">
              <h2 class="hero-name">{{ profile.user.username }}</h2>
              <el-button type="primary" plain size="small" class="edit-btn" @click="store.openProfileEdit()">
                编辑个人信息
              </el-button>
            </div>
            <p class="hero-meta">
              <span>账号 {{ store.user?.account }}</span>
              <span class="dot">·</span>
              <span>加入于 {{ formatDate(profile.user.created_at) }}</span>
            </p>
            <p v-if="store.user?.email || store.user?.phone" class="hero-contact">
              {{ store.user?.email || store.user?.phone }}
            </p>
          </div>
        </div>
        <el-row :gutter="16" class="stats-row">
          <el-col :span="8">
            <div class="stat-card">
              <span class="stat-num">{{ profile.stats.interview_count }}</span>
              <span class="stat-label">公开面试</span>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="stat-card">
              <span class="stat-num">{{ profile.stats.like_count }}</span>
              <span class="stat-label">获赞数</span>
            </div>
          </el-col>
          <el-col :span="8">
            <div class="stat-card">
              <span class="stat-num">{{ profile.stats.friend_count }}</span>
              <span class="stat-label">好友数</span>
            </div>
          </el-col>
        </el-row>
      </div>

      <div class="page-card records-card">
        <h3 class="section-title">公开面试记录</h3>
        <el-table :data="profile.interviews" stripe empty-text="暂无公开面试">
          <el-table-column prop="company_name" label="公司" min-width="140" />
          <el-table-column prop="job_title" label="岗位" min-width="140" />
          <el-table-column label="评分" width="100">
            <template #default="{ row }">{{ row.score?.toFixed(1) || '-' }}</template>
          </el-table-column>
          <el-table-column label="时间" width="140">
            <template #default="{ row }">{{ formatDate(row.interview_time as string) }}</template>
          </el-table-column>
        </el-table>
      </div>
    </template>

    <AvatarPickerDialog
      v-model="avatarPickerVisible"
      :current-url="profile?.user.avatar_url || store.user?.avatar_url"
      @confirmed="onProfileSaved"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { Camera } from '@element-plus/icons-vue'
import { useSessionRefresh } from '@/composables/useSessionRefresh'
import { profileApi } from '@/api'
import { useUserStore } from '@/stores/user'
import AvatarPickerDialog from '@/components/profile/AvatarPickerDialog.vue'

const store = useUserStore()
const avatarPickerVisible = ref(false)

const loading = ref(false)
const profile = ref<{
  user: { username: string; avatar_url?: string; created_at: string }
  stats: { interview_count: number; like_count: number; friend_count: number }
  interviews: Record<string, unknown>[]
} | null>(null)

function clearPageData() {
  profile.value = null
}

async function load() {
  if (!store.user) {
    clearPageData()
    loading.value = false
    return
  }
  loading.value = true
  try {
    profile.value = await profileApi.get(store.user.id) as typeof profile.value
  } finally {
    loading.value = false
  }
}

function openAvatarPicker() {
  if (!store.isLoggedIn()) {
    store.showLoginDialog = true
    return
  }
  avatarPickerVisible.value = true
}

function onProfileSaved() {
  load()
}

watch(() => store.user?.id, load, { immediate: true })
onMounted(load)
useSessionRefresh({ refresh: load, clear: clearPageData })

function formatDate(t: string) {
  return new Date(t).toLocaleDateString('zh-CN')
}
</script>

<style scoped lang="scss">
.profile-page {
  display: flex;
  flex-direction: column;
  gap: 20px;
}

.empty-login {
  text-align: center;
  padding: 80px 0;
  p {
    margin: 16px 0 24px;
    color: #64748b;
  }
}

.profile-hero {
  padding: 28px 32px;
}

.hero-main {
  display: flex;
  align-items: flex-start;
  gap: 24px;
  margin-bottom: 28px;
}

.avatar-wrap {
  position: relative;
  cursor: pointer;
  flex-shrink: 0;

  .hero-avatar {
    border: 4px solid #fff;
    box-shadow: 0 8px 24px rgba(59, 130, 246, 0.2);
  }

  .avatar-edit-badge {
    position: absolute;
    right: 0;
    bottom: 0;
    width: 28px;
    height: 28px;
    background: #3b82f6;
    color: #fff;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    border: 2px solid #fff;
    font-size: 14px;
  }

  &:hover .hero-avatar {
    opacity: 0.92;
  }
}

.hero-info {
  flex: 1;
  min-width: 0;
}

.name-row {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 12px;
  margin-bottom: 8px;
}

.hero-name {
  font-size: 26px;
  font-weight: 600;
  color: #0f172a;
  margin: 0;
}

.edit-btn {
  border-radius: 8px;
}

.hero-meta {
  font-size: 14px;
  color: #64748b;
  margin: 0 0 6px;

  .dot {
    margin: 0 8px;
  }
}

.hero-contact {
  font-size: 13px;
  color: #94a3b8;
  margin: 0;
}

.stats-row {
  margin-top: 4px;
}

.stat-card {
  text-align: center;
  padding: 16px;
  background: #f8fafc;
  border-radius: 12px;
  border: 1px solid #f1f5f9;

  .stat-num {
    display: block;
    font-size: 24px;
    font-weight: 600;
    color: #1e293b;
  }
  .stat-label {
    font-size: 13px;
    color: #64748b;
    margin-top: 4px;
  }
}

.records-card {
  .section-title {
    font-size: 16px;
    font-weight: 600;
    color: #1e293b;
    margin: 0 0 16px;
  }
}
</style>
