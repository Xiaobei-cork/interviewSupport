<template>
  <div class="messages-page">
    <div class="page-card messages-card">
      <div class="page-head">
        <h2 class="page-title">消息中心</h2>
        <el-button
          v-if="store.isLoggedIn() && list.length"
          link
          type="primary"
          :disabled="unreadCount === 0"
          @click="markAllRead"
        >
          全部标为已读
        </el-button>
      </div>

      <div v-if="!store.isLoggedIn()" class="empty-state">
        <el-icon :size="48" color="#cbd5e1"><Bell /></el-icon>
        <p>请先登录查看消息</p>
        <el-button type="primary" @click="store.showLoginDialog = true">立即登录</el-button>
      </div>

      <div v-else v-loading="loading" class="msg-list-wrap">
        <div
          v-for="msg in list"
          :key="msg.id"
          class="msg-item"
          :class="{ unread: !msg.is_read, [`type-${msg.msg_type}`]: true }"
          @click="markRead(msg)"
        >
          <div class="msg-icon" :class="`icon-${msg.msg_type}`">
            <el-icon>
              <ChatDotRound v-if="msg.msg_type === 'comment'" />
              <StarFilled v-else-if="msg.msg_type === 'like'" />
              <Bell v-else />
            </el-icon>
          </div>
          <div class="msg-body">
            <div class="msg-title-row">
              <span class="msg-title">{{ msg.title }}</span>
              <span class="msg-time">{{ formatTime(msg.created_at) }}</span>
            </div>
            <p class="msg-content">{{ msg.content }}</p>
          </div>
          <span v-if="!msg.is_read" class="unread-dot" />
        </div>
        <el-empty v-if="!loading && !list.length" description="暂无消息">
          <template #description>
            <p class="empty-desc">当有人评论或点赞你的面试分享时，会在这里收到通知</p>
          </template>
        </el-empty>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { Bell, ChatDotRound, StarFilled } from '@element-plus/icons-vue'
import { messageApi } from '@/api'
import { useUserStore } from '@/stores/user'
import { useSessionRefresh } from '@/composables/useSessionRefresh'

type MsgItem = {
  id: number
  title: string
  content: string
  msg_type: string
  is_read: number
  created_at: string
}

const store = useUserStore()
const list = ref<MsgItem[]>([])
const loading = ref(false)
const unreadCount = computed(() => store.unreadCount)

function clearPageData() {
  list.value = []
}

async function load() {
  if (!store.isLoggedIn()) {
    clearPageData()
    return
  }
  loading.value = true
  try {
    const res = await messageApi.list({ page: 1, page_size: 50 }) as { items: MsgItem[] }
    list.value = res.items
    await store.refreshUnread()
  } finally {
    loading.value = false
  }
}

onMounted(load)
useSessionRefresh({ refresh: load, clear: clearPageData })

function formatTime(t: string) {
  return new Date(t).toLocaleString('zh-CN', { hour12: false })
}

async function markRead(msg: MsgItem) {
  if (!msg.is_read) {
    await messageApi.markRead(msg.id)
    msg.is_read = 1
    store.unreadCount = Math.max(0, store.unreadCount - 1)
  }
}

async function markAllRead() {
  const unread = list.value.filter((m) => !m.is_read)
  for (const m of unread) {
    await messageApi.markRead(m.id)
    m.is_read = 1
  }
  store.unreadCount = 0
}
</script>

<style scoped lang="scss">
.messages-page {
  width: 100%;
  min-height: calc(100vh - 48px);
  display: flex;
  flex-direction: column;
}

.messages-card {
  flex: 1;
  display: flex;
  flex-direction: column;
  width: 100%;
  padding: 24px 28px 28px;
  min-height: calc(100vh - 48px);
  box-sizing: border-box;
}

.page-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 20px;
}

.page-title {
  margin: 0;
  font-size: 20px;
  font-weight: 600;
  color: #0f172a;
}

.empty-state {
  flex: 1;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  text-align: center;
  padding: 48px 0;
  color: #64748b;

  p {
    margin: 16px 0 20px;
  }
}

.msg-list-wrap {
  flex: 1;
  min-height: 200px;
}

.msg-item {
  display: flex;
  align-items: flex-start;
  gap: 14px;
  padding: 16px 14px;
  border-radius: 12px;
  border: 1px solid #f1f5f9;
  margin-bottom: 10px;
  cursor: pointer;
  transition: background 0.15s, border-color 0.15s;
  position: relative;

  &:hover {
    background: #f8fafc;
    border-color: #e2e8f0;
  }

  &.unread {
    background: linear-gradient(90deg, #eff6ff 0%, #fff 100%);
    border-color: #bfdbfe;
  }
}

.msg-icon {
  width: 40px;
  height: 40px;
  border-radius: 10px;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  font-size: 20px;

  &.icon-comment {
    background: #dbeafe;
    color: #2563eb;
  }

  &.icon-like {
    background: #fef3c7;
    color: #d97706;
  }

  &.icon-system {
    background: #f1f5f9;
    color: #64748b;
  }
}

.msg-body {
  flex: 1;
  min-width: 0;
}

.msg-title-row {
  display: flex;
  align-items: baseline;
  gap: 12px;
  margin-bottom: 6px;
}

.msg-title {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
  flex: 1;
}

.msg-time {
  font-size: 12px;
  color: #94a3b8;
  flex-shrink: 0;
}

.msg-content {
  margin: 0;
  font-size: 14px;
  line-height: 1.55;
  color: #64748b;
}

.unread-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ef4444;
  flex-shrink: 0;
  margin-top: 6px;
}

.empty-desc {
  font-size: 13px;
  color: #94a3b8;
  margin-top: 4px;
}
</style>
