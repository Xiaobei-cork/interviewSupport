<template>
  <div class="share-page">
    <div class="page-card share-shell">
      <div class="page-head">
        <div class="page-head-left">
          <h2 class="page-title">面试分享</h2>
          <p class="page-desc">浏览他人的公开面试复盘，点赞、收藏并参与讨论</p>
        </div>
      </div>

      <div class="share-feed" v-loading="loading">
        <div
          v-for="card in list"
          :key="card.id"
          class="share-card"
          :class="{ active: activeCardId === card.id }"
          @click="openDetail(card)"
        >
          <div class="card-accent" />
          <div class="card-inner">
            <div class="card-header">
              <el-avatar :src="card.avatar_url" :size="48" class="card-avatar">
                {{ card.username?.[0] }}
              </el-avatar>
              <div class="meta">
                <span class="username">{{ card.username }}</span>
                <div class="position-row">
                  <span class="company">{{ card.company_name }}</span>
                  <span class="dot">·</span>
                  <span class="job">{{ card.job_title }}</span>
                </div>
              </div>
              <div class="score-badge">
                <el-rate :model-value="card.score || 0" disabled allow-half size="small" />
                <span class="score-text">{{ card.score?.toFixed(1) || '-' }}</span>
              </div>
            </div>

            <p class="summary">
              <span class="summary-label">AI 摘要</span>
              {{ card.ai_summary || '暂无 AI 分析摘要，可先在面试复盘中完成分析' }}
            </p>

            <div class="card-footer">
              <span class="foot-pill" :class="{ active: card.is_liked }">
                <el-icon><Star /></el-icon>
                {{ card.like_count }} 赞
              </span>
              <span
                class="foot-pill"
                :class="{ active: card.is_favorited }"
                @click.stop="toggleFavorite(card)"
              >
                <el-icon><Collection /></el-icon>
                {{ card.favorite_count }} 收藏
              </span>
              <span class="foot-pill">
                <el-icon><ChatDotRound /></el-icon>
                {{ card.comment_count }} 评论
              </span>
              <span class="view-hint">
                查看详情
                <el-icon><ArrowRight /></el-icon>
              </span>
            </div>
          </div>
        </div>

        <div v-if="!loading && !list.length" class="feed-empty">
          <el-icon :size="56" color="#cbd5e1"><Share /></el-icon>
          <p>暂无公开面试记录</p>
          <span>将面试复盘设为公开后，会出现在这里</span>
        </div>
      </div>

      <div v-if="total > 0" class="share-pagination">
        <el-pagination
          v-model:current-page="page"
          v-model:page-size="pageSize"
          :total="total"
          :page-sizes="[5, 10, 20, 50, 100]"
          layout="sizes, total, prev, pager, next"
          background
          @size-change="onPageSizeChange"
          @current-change="load"
        />
      </div>
    </div>

    <el-dialog
      v-model="detailVisible"
      width="760px"
      class="share-detail-dialog"
      align-center
      destroy-on-close
      :show-close="true"
      @closed="onDetailClosed"
    >
      <template #header>
        <div class="detail-dialog-header">
          <div>
            <h3 class="detail-title">{{ detail?.company_name }} · {{ detail?.job_title }}</h3>
            <p class="detail-sub">面试经验分享</p>
          </div>
        </div>
      </template>

      <div v-if="detail" class="detail-body">
        <div class="detail-grid">
          <div class="info-panel">
            <div class="info-row">
              <span class="label">公司</span>
              <span class="value">{{ detail.company_name }}</span>
            </div>
            <div class="info-row">
              <span class="label">岗位</span>
              <span class="value">{{ detail.job_title }}</span>
            </div>
            <div class="info-row">
              <span class="label">面试时间</span>
              <span class="value">{{ formatTime(detail.interview_time) }}</span>
            </div>
            <div class="info-row score-row">
              <span class="label">评分</span>
              <el-rate :model-value="detail.score || 0" disabled allow-half />
            </div>
            <div class="action-row">
              <el-button
                :type="detail.is_liked ? 'primary' : 'default'"
                round
                @click="toggleLike(detail)"
              >
                <el-icon><Star /></el-icon>
                点赞 {{ detail.like_count }}
              </el-button>
              <el-button round @click="toggleFavorite(detail)">
                <el-icon><Collection /></el-icon>
                收藏
              </el-button>
            </div>
          </div>
          <div class="ai-panel">
            <div class="ai-panel-title">
              <el-icon color="#3b82f6"><MagicStick /></el-icon>
              AI 分析
            </div>
            <p class="ai-text">{{ aiSummary }}</p>
          </div>
        </div>

        <div class="comments-block">
          <div class="comments-head">
            <span class="comments-title">评论 ({{ commentTotal }})</span>
            <el-button
              v-if="commentTotal > comments.length"
              link
              type="primary"
              size="small"
              @click="loadMoreComments"
            >
              查看全部 {{ commentTotal }} 条
            </el-button>
          </div>
          <div v-if="comments.length" class="comment-list">
            <div v-for="c in comments" :key="c.id" class="comment-item">
              <el-avatar :size="36" :src="c.avatar_url">{{ c.username?.[0] }}</el-avatar>
              <div class="comment-body">
                <span class="c-user">{{ c.username }}</span>
                <p class="c-content">{{ c.content }}</p>
              </div>
            </div>
          </div>
          <el-empty v-else description="暂无评论，来抢沙发吧" :image-size="64" />
          <div v-if="store.isLoggedIn()" class="comment-compose">
            <el-input
              v-model="newComment"
              type="textarea"
              :rows="2"
              maxlength="500"
              show-word-limit
              placeholder="写下你的评论…"
              resize="none"
            />
            <el-button type="primary" :loading="commentSending" @click="submitComment">发送</el-button>
          </div>
          <div v-else class="comment-login-hint">
            <el-button type="primary" link @click="store.showLoginDialog = true">登录后参与评论</el-button>
          </div>
        </div>
      </div>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import {
  ArrowRight,
  Star,
  Collection,
  ChatDotRound,
  MagicStick,
  Share,
} from '@element-plus/icons-vue'
import { shareApi } from '@/api'
import { useUserStore } from '@/stores/user'
import { showSuccessToast, showErrorToast } from '@/utils/message'

const route = useRoute()
const router = useRouter()
const store = useUserStore()

interface ShareCard {
  id: number
  username: string
  avatar_url?: string
  company_name: string
  job_title: string
  score?: number
  ai_summary?: string
  like_count: number
  comment_count: number
  favorite_count: number
  is_liked: boolean
  is_favorited?: boolean
}

interface CommentItem {
  id: number
  username: string
  avatar_url?: string
  content: string
}

interface DetailRecord {
  id: number
  company_name: string
  job_title: string
  interview_time: string
  score?: number
  ai_analysis?: string
  like_count: number
  is_liked?: boolean
  is_favorited?: boolean
}

const list = ref<ShareCard[]>([])
const page = ref(1)
const pageSize = ref(5)
const total = ref(0)
const loading = ref(false)
const detailVisible = ref(false)
const detail = ref<DetailRecord | null>(null)
const comments = ref<CommentItem[]>([])
const commentTotal = ref(0)
const newComment = ref('')
const commentSending = ref(false)
const openingDetail = ref(false)

const activeCardId = computed(() => {
  const id = route.query.id
  if (!id) return null
  const n = Number(id)
  return Number.isFinite(n) && n > 0 ? n : null
})

const aiSummary = computed(() => {
  if (!detail.value?.ai_analysis) return '暂无分析内容，可先在面试复盘中完成 AI 分析后再分享。'
  try {
    const data = JSON.parse(detail.value.ai_analysis as string)
    return data.overall || data.tabs?.comprehensive || '暂无分析'
  } catch {
    return String(detail.value.ai_analysis).slice(0, 400)
  }
})

onMounted(load)

watch(
  () => route.query.id,
  async (id) => {
    if (!id) return
    const numId = Number(id)
    if (!Number.isFinite(numId) || numId <= 0) return
    if (detailVisible.value && detail.value?.id === numId) return
    await openDetailById(numId)
  },
  { immediate: true }
)

async function load() {
  loading.value = true
  try {
    const res = await shareApi.feed({
      page: page.value,
      page_size: pageSize.value,
    }) as { items: ShareCard[]; total: number }
    list.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function onPageSizeChange() {
  page.value = 1
  void load()
}

function formatTime(t: string) {
  return new Date(t).toLocaleString('zh-CN', { hour12: false })
}

async function openDetailById(id: number) {
  if (openingDetail.value) return
  openingDetail.value = true
  try {
    detail.value = await shareApi.detail(id) as DetailRecord
    const cr = await shareApi.comments(id, 3) as { items: CommentItem[]; total: number }
    comments.value = cr.items
    commentTotal.value = cr.total
    newComment.value = ''
    detailVisible.value = true
  } catch {
    showErrorToast('无法打开该分享，可能已设为私密或不存在')
    clearShareQuery()
  } finally {
    openingDetail.value = false
  }
}

function openDetail(card: ShareCard) {
  if (route.query.id === String(card.id) && detailVisible.value) return
  void router.replace({ path: '/share', query: { id: String(card.id) } })
}

function clearShareQuery() {
  if (route.query.id) {
    router.replace({ path: '/share', query: {} })
  }
}

function onDetailClosed() {
  detail.value = null
  comments.value = []
  commentTotal.value = 0
  clearShareQuery()
}

async function toggleLike(card: ShareCard | DetailRecord | null) {
  if (!card || !store.requireLogin()) return
  await shareApi.like(card.id)
  showSuccessToast('点赞操作成功')
  await load()
  if (detail.value?.id === card.id) {
    detail.value = await shareApi.detail(card.id) as DetailRecord
  }
}

async function toggleFavorite(card: ShareCard | DetailRecord | null) {
  if (!card || !store.requireLogin()) return
  await shareApi.favorite(card.id)
  showSuccessToast('收藏操作成功')
  await syncCardInList(card.id)
  if (detail.value?.id === card.id) {
    detail.value = await shareApi.detail(card.id) as DetailRecord
  }
}

async function syncCardInList(id: number) {
  const idx = list.value.findIndex((c) => c.id === id)
  if (idx >= 0) {
    const fresh = await shareApi.feed({
      page: page.value,
      page_size: pageSize.value,
    }) as { items: ShareCard[] }
    const updated = fresh.items.find((c) => c.id === id)
    if (updated) list.value[idx] = updated
  }
}

async function submitComment() {
  if (!detail.value || !newComment.value.trim()) return
  if (!store.requireLogin()) return
  commentSending.value = true
  try {
    await shareApi.addComment(detail.value.id, { content: newComment.value.trim() })
    newComment.value = ''
    const cr = await shareApi.comments(detail.value.id, 3) as { items: CommentItem[]; total: number }
    comments.value = cr.items
    commentTotal.value = cr.total
    showSuccessToast('评论发表成功')
    await load()
  } finally {
    commentSending.value = false
  }
}

async function loadMoreComments() {
  if (!detail.value) return
  const cr = await shareApi.comments(detail.value.id, 50) as { items: CommentItem[]; total: number }
  comments.value = cr.items
  commentTotal.value = cr.total
}
</script>

<style scoped lang="scss">
.share-page {
  width: 100%;
}

.share-shell {
  padding: 24px 28px 28px;
}

.page-head {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 16px;
  margin-bottom: 22px;
  padding-bottom: 18px;
  border-bottom: 1px solid #f1f5f9;
}

.page-head-left {
  min-width: 0;
}

.page-title {
  margin: 0 0 6px;
  font-size: 20px;
  font-weight: 600;
  color: #0f172a;
}

.page-desc {
  margin: 0;
  font-size: 13px;
  color: #94a3b8;
  line-height: 1.5;
}

.share-feed {
  display: flex;
  flex-direction: column;
  gap: 14px;
  min-height: 120px;
}

.share-card {
  position: relative;
  border-radius: 16px;
  border: 1px solid #e2e8f0;
  background: linear-gradient(135deg, #fafbfc 0%, #fff 48%);
  cursor: pointer;
  overflow: hidden;
  transition: border-color 0.2s, box-shadow 0.2s, transform 0.15s;

  &:hover {
    border-color: #93c5fd;
    box-shadow: 0 10px 28px rgba(59, 130, 246, 0.12);
    transform: translateY(-2px);

    .view-hint {
      color: #3b82f6;
    }
  }

  &.active {
    border-color: #3b82f6;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15);
  }
}

.card-accent {
  position: absolute;
  left: 0;
  top: 0;
  bottom: 0;
  width: 4px;
  background: linear-gradient(180deg, #3b82f6, #60a5fa);
  opacity: 0;
  transition: opacity 0.2s;
}

.share-card:hover .card-accent,
.share-card.active .card-accent {
  opacity: 1;
}

.card-inner {
  padding: 20px 22px 18px 24px;
}

.card-header {
  display: flex;
  align-items: center;
  gap: 14px;
}

.card-avatar {
  flex-shrink: 0;
  border: 2px solid #fff;
  box-shadow: 0 4px 12px rgba(15, 23, 42, 0.08);
}

.meta {
  flex: 1;
  min-width: 0;
}

.username {
  font-weight: 600;
  font-size: 15px;
  color: #0f172a;
  display: block;
  margin-bottom: 4px;
}

.position-row {
  font-size: 13px;
  color: #64748b;
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 4px;

  .company {
    font-weight: 500;
    color: #475569;
  }

  .dot {
    color: #cbd5e1;
  }
}

.score-badge {
  text-align: right;
  flex-shrink: 0;
  padding: 8px 12px;
  background: #fffbeb;
  border-radius: 12px;
  border: 1px solid #fde68a;

  :deep(.el-rate) {
    height: auto;
  }

  .score-text {
    display: block;
    font-size: 13px;
    font-weight: 600;
    color: #d97706;
    margin-top: 2px;
    text-align: center;
  }
}

.summary {
  margin: 16px 0 14px;
  padding: 14px 16px;
  background: #f8fafc;
  border-radius: 12px;
  border-left: 3px solid #93c5fd;
  color: #475569;
  font-size: 14px;
  line-height: 1.7;

  .summary-label {
    display: inline-block;
    font-size: 11px;
    font-weight: 600;
    color: #3b82f6;
    background: #eff6ff;
    padding: 2px 8px;
    border-radius: 4px;
    margin-right: 8px;
    vertical-align: middle;
  }
}

.card-footer {
  display: flex;
  align-items: center;
  flex-wrap: wrap;
  gap: 10px;
}

.foot-pill {
  display: inline-flex;
  align-items: center;
  gap: 5px;
  padding: 6px 12px;
  border-radius: 20px;
  background: #f1f5f9;
  color: #64748b;
  font-size: 13px;
  transition: background 0.15s, color 0.15s;

  &.active {
    background: #eff6ff;
    color: #2563eb;
    font-weight: 500;
  }
}

.view-hint {
  margin-left: auto;
  display: inline-flex;
  align-items: center;
  gap: 4px;
  font-size: 13px;
  color: #94a3b8;
  transition: color 0.15s;
}

.feed-empty {
  text-align: center;
  padding: 56px 24px;
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

.share-pagination {
  margin-top: 20px;
  padding-top: 18px;
  border-top: 1px solid #f1f5f9;
  display: flex;
  justify-content: flex-end;

  :deep(.el-pagination) {
    flex-wrap: wrap;
    justify-content: flex-end;
    gap: 8px 0;
  }
}

.detail-dialog-header {
  .detail-title {
    font-size: 18px;
    font-weight: 600;
    color: #1e293b;
    margin: 0;
  }
  .detail-sub {
    font-size: 13px;
    color: #94a3b8;
    margin: 4px 0 0;
  }
}

.detail-body {
  padding: 0 4px;
}

.detail-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;
  margin-bottom: 20px;
}

@media (max-width: 720px) {
  .detail-grid {
    grid-template-columns: 1fr;
  }
}

.info-panel {
  padding: 18px;
  background: #f8fafc;
  border-radius: 12px;
  border: 1px solid #f1f5f9;
}

.info-row {
  display: flex;
  margin-bottom: 12px;
  font-size: 14px;

  .label {
    width: 72px;
    color: #64748b;
    flex-shrink: 0;
  }
  .value {
    color: #1e293b;
    font-weight: 500;
  }
  &.score-row {
    align-items: center;
  }
}

.action-row {
  display: flex;
  gap: 10px;
  margin-top: 16px;
  padding-top: 14px;
  border-top: 1px dashed #e2e8f0;
}

.ai-panel {
  padding: 18px;
  background: linear-gradient(135deg, #eff6ff 0%, #f8fafc 100%);
  border-radius: 12px;
  border: 1px solid #dbeafe;

  .ai-panel-title {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 15px;
    font-weight: 600;
    color: #1e40af;
    margin-bottom: 12px;
  }

  .ai-text {
    font-size: 14px;
    line-height: 1.7;
    color: #475569;
    margin: 0;
    white-space: pre-wrap;
  }
}

.comments-block {
  border-top: 1px solid #f1f5f9;
  padding-top: 18px;
}

.comments-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  margin-bottom: 12px;

  .comments-title {
    font-size: 15px;
    font-weight: 600;
    color: #1e293b;
  }
}

.comment-list {
  max-height: 220px;
  overflow-y: auto;
  margin-bottom: 16px;
}

.comment-item {
  display: flex;
  gap: 12px;
  padding: 12px;
  background: #f8fafc;
  border-radius: 10px;
  margin-bottom: 8px;

  .comment-body {
    flex: 1;
    min-width: 0;
  }

  .c-user {
    font-size: 13px;
    font-weight: 600;
    color: #334155;
  }

  .c-content {
    font-size: 14px;
    color: #475569;
    margin: 6px 0 0;
    line-height: 1.5;
  }
}

.comment-compose {
  display: flex;
  gap: 12px;
  align-items: flex-end;

  .el-textarea {
    flex: 1;
  }

  .el-button {
    flex-shrink: 0;
    border-radius: 8px;
    min-width: 88px;
  }
}

.comment-login-hint {
  text-align: center;
  padding: 12px;
}
</style>

<style lang="scss">
.share-detail-dialog.el-dialog {
  border-radius: 16px;

  .el-dialog__header {
    padding: 20px 24px 12px;
    margin: 0;
  }

  .el-dialog__body {
    padding: 8px 24px 24px;
  }
}
</style>
