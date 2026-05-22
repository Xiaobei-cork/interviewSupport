<template>
  <div class="page-card">
    <div class="page-header">
      <h2 class="page-title">面试复盘</h2>
      <el-button type="primary" :icon="Plus" @click="openCreate">新增面试记录</el-button>
    </div>
    <div class="filters">
      <el-select v-model="filters.visibility" placeholder="全部可见性" clearable style="width:140px">
        <el-option label="公开" :value="1" />
        <el-option label="仅好友" :value="2" />
        <el-option label="私密" :value="0" />
      </el-select>
      <el-input v-model="filters.keyword" placeholder="搜索公司/岗位" clearable style="width:240px" :prefix-icon="Search" @keyup.enter="load" />
      <el-button @click="load">搜索</el-button>
    </div>
    <el-table :data="list" v-loading="loading" stripe>
      <el-table-column label="公司/岗位" min-width="200">
        <template #default="{ row }">
          <div class="company-cell">
            <el-avatar :size="32" shape="square">{{ row.company_name[0] }}</el-avatar>
            <div>
              <div class="company">{{ row.company_name }}</div>
              <div class="job">{{ row.job_title }}</div>
            </div>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="面试时间" prop="interview_time" width="180">
        <template #default="{ row }">{{ formatTime(row.interview_time) }}</template>
      </el-table-column>
      <el-table-column label="可见性" width="140">
        <template #default="{ row }">
          <el-tag :class="visibilityClass(row.visibility)" size="small">{{ visibilityLabel(row.visibility) }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="AI 评分" width="130">
        <template #default="{ row }">
          <div v-if="row.score != null && Number(row.score) > 0" class="rate-cell">
            <el-rate
              :model-value="Number(row.score)"
              disabled
              allow-half
              :show-score="false"
            />
          </div>
          <span v-else class="score-empty">未分析</span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="140" fixed="right">
        <template #default="{ row }">
          <el-button link type="primary" :icon="View" @click="openPreview(row)" />
          <el-button link type="primary" :icon="Edit" @click="openEdit(row)" />
          <el-button link type="danger" :icon="Delete" @click="handleDelete(row)" />
        </template>
      </el-table-column>
    </el-table>
    <el-pagination
      v-model:current-page="page"
      v-model:page-size="pageSize"
      :total="total"
      layout="total, prev, pager, next"
      style="margin-top:16px;justify-content:flex-end"
      @change="load"
    />
    <div class="ai-banner">
      <span>对面试结果不满意？用 AI 分析，发现问题并获得专业建议</span>
      <el-button type="primary" size="small" @click="openBannerPicker">使用 AI 分析</el-button>
    </div>
    <InterviewFormDialog
      v-model="formVisible"
      :mode="formMode"
      :data="currentForm"
      :record-id="currentRow?.id as number | undefined"
      ref="formRef"
      @save="handleSave"
      @analyze="startAnalyze"
    />
    <AiProgressDialog
      v-model="progressVisible"
      :task-id="taskId"
      variant="interview"
      :poll-fn="interviewApi.pollTask"
      @done="onAnalyzeDone"
    />
    <AiAnalysisResult
      v-model="resultVisible"
      :data="analysisData"
      :show-adopt="true"
      :adopted="!!currentRow?.ai_adopted"
      @reanalyze="startAnalyze"
      @chat="openChat"
      @adopt="openAdopt"
    />
    <RecordPickerDialog
      v-model="pickerVisible"
      title="选择要分析的面试记录"
      hint="请选择一条面试记录后再开始 AI 分析"
      empty-text="请先新增面试记录"
      :items="interviewPickerItems"
      @confirm="onPickInterview"
    />
    <AiChatDialog v-model="chatVisible" :chat-fn="chatFn" welcome="您好，我是面试 AI 助手，有什么可以帮您？" />
    <LoginPrompt v-model="loginPromptVisible" />
  </div>
</template>

<script setup lang="ts">
import { ref, reactive, computed, onMounted } from 'vue'
import { useSessionRefresh } from '@/composables/useSessionRefresh'
import { Plus, Search, View, Edit, Delete } from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'
import { showSuccessToast, showInfoToast } from '@/utils/message'
import { interviewApi } from '@/api'
import { useUserStore } from '@/stores/user'
import InterviewFormDialog, { type InterviewForm } from '@/components/interview/InterviewFormDialog.vue'
import AiProgressDialog from '@/components/ai/AiProgressDialog.vue'
import AiAnalysisResult from '@/components/ai/AiAnalysisResult.vue'
import AiChatDialog from '@/components/ai/AiChatDialog.vue'
import LoginPrompt from '@/components/common/LoginPrompt.vue'
import RecordPickerDialog, { type PickerRecord } from '@/components/common/RecordPickerDialog.vue'

const store = useUserStore()
const list = ref<Record<string, unknown>[]>([])
const loading = ref(false)
const page = ref(1)
const pageSize = ref(10)
const total = ref(0)
const filters = reactive({ visibility: undefined as number | undefined, keyword: '' })

const formVisible = ref(false)
const formMode = ref<'create' | 'edit' | 'preview'>('create')
const currentRow = ref<Record<string, unknown> | null>(null)
const currentForm = ref<InterviewForm | null>(null)
const formRef = ref()

const progressVisible = ref(false)
const taskId = ref('')
const resultVisible = ref(false)
const analysisData = ref<Record<string, unknown> | null>(null)
const chatVisible = ref(false)
const loginPromptVisible = ref(false)
const pickerVisible = ref(false)

const interviewPickerItems = computed<PickerRecord[]>(() =>
  list.value
    .filter((r) => !r.ai_adopted)
    .map((r) => ({
      id: r.id as number,
      title: `${r.company_name} · ${r.job_title}`,
      subtitle: formatTime(String(r.interview_time)),
      meta: r.score && Number(r.score) > 0 ? '已有 AI 评分' : '未分析',
    }))
)

function clearPageData() {
  list.value = []
  total.value = 0
  page.value = 1
  formVisible.value = false
  progressVisible.value = false
  resultVisible.value = false
  chatVisible.value = false
  currentRow.value = null
  currentForm.value = null
  analysisData.value = null
  taskId.value = ''
}

onMounted(() => {
  if (store.isLoggedIn()) load()
  else clearPageData()
})
useSessionRefresh({ refresh: () => load(), clear: clearPageData })

async function load() {
  if (!store.isLoggedIn()) {
    clearPageData()
    return
  }
  loading.value = true
  try {
    const res = await interviewApi.list({ page: page.value, page_size: pageSize.value, ...filters }) as { items: Record<string, unknown>[]; total: number }
    list.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function formatTime(t: string) {
  return new Date(t).toLocaleString('zh-CN', { hour12: false })
}

function visibilityLabel(v: number) {
  return v === 1 ? '公开' : v === 2 ? '仅好友可见' : '私密'
}
function visibilityClass(v: number) {
  return v === 1 ? 'tag-public' : v === 2 ? 'tag-friends' : 'tag-private'
}

function rowToForm(row: Record<string, unknown>): InterviewForm {
  return {
    id: row.id as number,
    company_name: String(row.company_name),
    job_title: String(row.job_title),
    job_jd: String(row.job_jd || ''),
    remark: String(row.remark || ''),
    interview_time: String(row.interview_time),
    visibility: Number(row.visibility),
    public_audio: Number(row.public_audio),
    audio_url: row.audio_url as string | undefined,
    ai_analysis: row.ai_analysis as string | undefined,
    score: row.score as number | undefined,
    ai_adopted: Boolean(row.ai_adopted),
  }
}

function openCreate() {
  if (!store.requireLogin()) return
  formMode.value = 'create'
  currentRow.value = null
  currentForm.value = null
  formVisible.value = true
}

function openEdit(row: Record<string, unknown>) {
  formMode.value = 'edit'
  currentRow.value = row
  currentForm.value = rowToForm(row)
  formVisible.value = true
}

function openPreview(row: Record<string, unknown>) {
  formMode.value = 'preview'
  currentRow.value = row
  currentForm.value = rowToForm(row)
  formVisible.value = true
}

async function handleSave(form: InterviewForm, audio: File | null) {
  try {
    let id = form.id as number | undefined
    const { id: _id, score: _s, ai_analysis: _a, audio_url: _u, ...payload } = form
    if (formMode.value === 'create') {
      const created = await interviewApi.create(payload) as { id: number }
      id = created.id
      showSuccessToast('创建成功')
    } else {
      await interviewApi.update(id!, payload)
      showSuccessToast('保存成功')
    }
    if (audio && id) await interviewApi.uploadAudio(id, audio)
    formVisible.value = false
    load()
  } catch { /* handled */ }
}

async function handleDelete(row: Record<string, unknown>) {
  await ElMessageBox.confirm('确定删除该记录？', '提示', { type: 'warning' })
  await interviewApi.remove(row.id as number)
  showSuccessToast('已删除')
  load()
}

async function startAnalyze() {
  const id = currentRow.value?.id as number
  if (!id) { showInfoToast('请先保存记录'); return }
  if (currentRow.value?.ai_adopted) {
    showInfoToast('已采纳 AI 分析，不可重新分析')
    return
  }
  const res = await interviewApi.analyze(id) as { task_id: string }
  taskId.value = res.task_id
  progressVisible.value = true
}

function onAnalyzeDone(result: unknown) {
  analysisData.value = result as Record<string, unknown>
  resultVisible.value = true
  if (currentRow.value) {
    currentRow.value.ai_analysis = JSON.stringify(result)
    currentRow.value.ai_adopted = false
    if ((result as Record<string, unknown>)?.score != null) {
      currentRow.value.score = (result as Record<string, unknown>).score
    }
  }
  load()
}

async function openAdopt() {
  const id = currentRow.value?.id as number
  if (!id) return
  const s = (analysisData.value?.score as number) || undefined
  await interviewApi.adoptAi(id, s)
  showSuccessToast('已采纳 AI 分析')
  if (currentRow.value) currentRow.value.ai_adopted = true
  resultVisible.value = false
  load()
}

function openBannerPicker() {
  if (!store.requireLogin()) return
  if (!list.value.length) {
    showInfoToast('请先新增面试记录')
    return
  }
  if (!interviewPickerItems.value.length) {
    showInfoToast('已采纳的记录不可重新分析')
    return
  }
  pickerVisible.value = true
}

function onPickInterview(item: PickerRecord) {
  const row = list.value.find((r) => r.id === item.id)
  if (row) {
    currentRow.value = row
    startAnalyze()
  }
}

function openChat() {
  chatVisible.value = true
}

async function chatFn(msg: string) {
  const id = currentRow.value?.id as number
  return interviewApi.chat(id, msg) as Promise<{ reply: string }>
}

</script>

<style scoped lang="scss">
.page-header { display: flex; justify-content: space-between; align-items: center; margin-bottom: 20px; }
.filters { display: flex; gap: 12px; margin-bottom: 16px; }
.company-cell { display: flex; align-items: center; gap: 10px; }
.company { font-weight: 500; }
.job { font-size: 12px; color: #64748b; }
.rate-cell {
  display: inline-flex;
  align-items: center;
  :deep(.el-rate__text) {
    display: none !important;
  }
  :deep(.el-rate) {
    height: auto;
  }
}
.score-empty { font-size: 13px; color: #94a3b8; }
</style>
