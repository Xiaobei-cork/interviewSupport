<template>
  <div class="page-card">
    <h2 class="page-title">消息中心</h2>
    <div v-if="!store.isLoggedIn()" class="empty">
      <p>请先登录查看消息</p>
      <el-button type="primary" @click="store.showLoginDialog = true">立即登录</el-button>
    </div>
    <div v-else>
      <div v-for="msg in list" :key="msg.id" class="msg-item" :class="{ unread: !msg.is_read }" @click="markRead(msg)">
        <div class="msg-title">
          <el-badge v-if="!msg.is_read" is-dot />
          <span>{{ msg.title }}</span>
          <span class="time">{{ formatTime(msg.created_at) }}</span>
        </div>
        <p class="msg-content">{{ msg.content }}</p>
      </div>
      <el-empty v-if="!list.length" description="暂无消息" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { messageApi } from '@/api'
import { useUserStore } from '@/stores/user'
import { useSessionRefresh } from '@/composables/useSessionRefresh'

const store = useUserStore()
const list = ref<{ id: number; title: string; content: string; is_read: number; created_at: string }[]>([])

function clearPageData() {
  list.value = []
}

async function load() {
  if (!store.isLoggedIn()) {
    clearPageData()
    return
  }
  const res = await messageApi.list({ page: 1, page_size: 50 }) as { items: typeof list.value }
  list.value = res.items
}

onMounted(load)
useSessionRefresh({ refresh: load, clear: clearPageData })

function formatTime(t: string) {
  return new Date(t).toLocaleString('zh-CN')
}

async function markRead(msg: { id: number; is_read: number }) {
  if (!msg.is_read) {
    await messageApi.markRead(msg.id)
    msg.is_read = 1
    store.unreadCount = Math.max(0, store.unreadCount - 1)
  }
}
</script>

<style scoped lang="scss">
.empty { text-align: center; padding: 60px; color: #64748b; }
.msg-item {
  padding: 16px; border-bottom: 1px solid #e2e8f0; cursor: pointer;
  &:hover { background: #f8fafc; }
  &.unread { background: #eff6ff; }
}
.msg-title {
  display: flex; align-items: center; gap: 8px; font-weight: 500;
  .time { margin-left: auto; font-size: 12px; color: #94a3b8; font-weight: normal; }
}
.msg-content { margin-top: 8px; font-size: 14px; color: #64748b; }
</style>
