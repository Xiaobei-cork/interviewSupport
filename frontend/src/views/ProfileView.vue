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
            <el-avatar :size="88" :src="heroAvatarUrl" class="hero-avatar">
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
        <div class="section-head">
          <div class="section-head-left">
            <h3 class="section-title">公开面试记录</h3>
            <p class="section-desc">对外展示的面试复盘，可在「面试分享」中被他人浏览</p>
          </div>
          <span v-if="profile.interviews.length" class="section-count">
            共 {{ profile.interviews.length }} 条
          </span>
        </div>

        <div v-if="profile.interviews.length" class="record-list">
          <div
            v-for="row in profile.interviews"
            :key="(row.id as number)"
            class="record-item"
            @click="goShareRecord(row)"
          >
            <div class="record-icon">
              <el-icon><Briefcase /></el-icon>
            </div>
            <div class="record-main">
              <div class="record-top">
                <span class="company">{{ row.company_name }}</span>
                <el-tag size="small" effect="plain" round class="job-tag">
                  {{ row.job_title }}
                </el-tag>
              </div>
              <div class="record-meta">
                <div class="score-wrap">
                  <el-rate
                    :model-value="Number(row.score) || 0"
                    disabled
                    allow-half
                    size="small"
                  />
                  <span class="score-num">{{ formatScore(row.score) }}</span>
                </div>
                <span class="record-time">
                  <el-icon><Calendar /></el-icon>
                  {{ formatDate(row.interview_time as string) }}
                </span>
              </div>
            </div>
            <el-icon class="record-arrow"><ArrowRight /></el-icon>
          </div>
        </div>

        <div v-else class="records-empty">
          <el-icon :size="56" color="#cbd5e1"><Document /></el-icon>
          <p>暂无公开面试</p>
          <span>将面试复盘设为公开后，会展示在这里</span>
        </div>
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
import { ref, computed, watch, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { ArrowRight, Briefcase, Calendar, Camera, Document } from '@element-plus/icons-vue'
import { useSessionRefresh } from '@/composables/useSessionRefresh'
import { profileApi } from '@/api'
import { useUserStore } from '@/stores/user'
import AvatarPickerDialog from '@/components/profile/AvatarPickerDialog.vue'

const router = useRouter()
const store = useUserStore()
const avatarPickerVisible = ref(false)

const loading = ref(false)

/** 与侧边栏一致：优先用 store（保存头像后立即更新），否则用 profile 接口数据 */
const heroAvatarUrl = computed(
  () => store.user?.avatar_url || profile.value?.user.avatar_url
)

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

async function onProfileSaved() {
  await store.fetchUser()
  await load()
}

watch(
  () => store.user?.avatar_url,
  (url) => {
    if (profile.value?.user && url) {
      profile.value.user.avatar_url = url
    }
  }
)

watch(() => store.user?.id, load, { immediate: true })
onMounted(load)
useSessionRefresh({ refresh: load, clear: clearPageData })

function formatDate(t: string) {
  return new Date(t).toLocaleDateString('zh-CN')
}

function formatScore(score: unknown) {
  const n = Number(score)
  return Number.isFinite(n) ? n.toFixed(1) : '-'
}

function goShareRecord(row: Record<string, unknown>) {
  const id = row.id
  if (id == null) {
    router.push('/share')
    return
  }
  router.push({ path: '/share', query: { id: String(id) } })
}
</script>

<style scoped lang="scss">
.profile-page {
  width: 100%;
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
  padding: 24px 28px 28px;
}

.section-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #f1f5f9;
}

.section-head-left {
  min-width: 0;
}

.section-title {
  font-size: 17px;
  font-weight: 600;
  color: #0f172a;
  margin: 0 0 6px;
}

.section-desc {
  margin: 0;
  font-size: 13px;
  color: #94a3b8;
  line-height: 1.5;
}

.section-count {
  flex-shrink: 0;
  font-size: 13px;
  color: #64748b;
  background: #f1f5f9;
  padding: 6px 12px;
  border-radius: 20px;
}

.record-list {
  display: flex;
  flex-direction: column;
  gap: 12px;
}

.record-item {
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 18px 20px;
  border-radius: 14px;
  border: 1px solid #e2e8f0;
  background: linear-gradient(135deg, #fafbfc 0%, #fff 55%);
  cursor: pointer;
  transition: border-color 0.2s, box-shadow 0.2s, transform 0.15s;

  &:hover {
    border-color: #93c5fd;
    box-shadow: 0 8px 24px rgba(59, 130, 246, 0.1);
    transform: translateY(-1px);

    .record-arrow {
      color: #3b82f6;
      transform: translateX(2px);
    }
  }
}

.record-icon {
  width: 48px;
  height: 48px;
  border-radius: 12px;
  background: linear-gradient(145deg, #dbeafe, #eff6ff);
  color: #2563eb;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 22px;
  flex-shrink: 0;
}

.record-main {
  flex: 1;
  min-width: 0;
}

.record-top {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 10px;
}

.company {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

.job-tag {
  border-color: #e2e8f0;
  color: #475569;
  background: #fff;
}

.record-meta {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 16px;
}

.score-wrap {
  display: flex;
  align-items: center;
  gap: 8px;

  :deep(.el-rate) {
    height: auto;
  }
}

.score-num {
  font-size: 14px;
  font-weight: 600;
  color: #f59e0b;
  min-width: 28px;
}

.record-time {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #94a3b8;
}

.record-arrow {
  font-size: 18px;
  color: #cbd5e1;
  flex-shrink: 0;
  transition: color 0.2s, transform 0.2s;
}

.records-empty {
  text-align: center;
  padding: 48px 24px;
  color: #64748b;

  p {
    margin: 16px 0 8px;
    font-size: 15px;
    font-weight: 500;
    color: #475569;
  }

  span {
    font-size: 13px;
    color: #94a3b8;
  }
}
</style>
