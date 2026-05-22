<template>
  <div class="page-card">
    <div class="page-header">
      <h2 class="page-title">简历管理</h2>
      <el-button type="primary" :icon="Plus" @click="openUpload">上传简历</el-button>
    </div>
    <el-tabs v-model="activeTab" @tab-change="load">
      <el-tab-pane label="全部" name="all" />
      <el-tab-pane label="Word" name="word" />
      <el-tab-pane label="PDF" name="pdf" />
    </el-tabs>
    <el-table :data="list" v-loading="loading" stripe>
      <el-table-column label="文件名称" min-width="240">
        <template #default="{ row }">
          <div class="file-cell">
            <el-icon :size="20" :color="row.file_type === 'pdf' ? '#ef4444' : '#3b82f6'">
              <Document />
            </el-icon>
            <span>{{ row.file_name }}</span>
          </div>
        </template>
      </el-table-column>
      <el-table-column label="类型" width="80">
        <template #default="{ row }">{{ row.file_type === 'pdf' ? 'PDF' : 'Word' }}</template>
      </el-table-column>
      <el-table-column label="上传时间" width="180">
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
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
      <el-table-column label="操作" width="180" fixed="right">
        <template #default="{ row }">
          <el-tooltip content="预览简历" placement="top">
            <el-button link type="primary" :icon="View" @click="preview(row)" />
          </el-tooltip>
          <el-tooltip content="查看 AI 分析结果" placement="top">
            <el-button
              link
              type="primary"
              class="result-btn"
              :disabled="!hasAiResult(row)"
              @click="openAnalysisResult(row)"
            >
              <el-icon><DataBoard /></el-icon>
            </el-button>
          </el-tooltip>
          <el-tooltip
            :content="row.ai_adopted ? '已采纳，不可重新分析' : 'AI 分析'"
            placement="top"
          >
            <el-button
              link
              type="primary"
              class="ai-btn"
              :disabled="!!row.ai_adopted"
              @click="analyze(row)"
            >
              <el-icon><MagicStick /></el-icon>
            </el-button>
          </el-tooltip>
          <el-tooltip content="删除" placement="top">
            <el-button link type="danger" :icon="Delete" @click="remove(row)" />
          </el-tooltip>
        </template>
      </el-table-column>
    </el-table>
    <el-pagination
      v-model:current-page="page"
      :total="total"
      layout="total, prev, pager, next"
      style="margin-top:16px;justify-content:flex-end"
      @change="load"
    />
    <div class="ai-banner">
      <span>对简历效果不满意？用 AI 分析，优化简历内容</span>
      <el-button type="primary" size="small" @click="openBannerPicker">使用 AI 分析</el-button>
    </div>

    <el-dialog v-model="uploadVisible" width="480px" :show-close="false" align-center>
      <template #header>
        <div class="upload-dialog-header">
          <button type="button" class="dialog-close-red" aria-label="关闭" @click="uploadVisible = false" />
          <span class="upload-dialog-title">上传简历</span>
        </div>
      </template>
      <el-upload drag :auto-upload="false" :limit="1" accept=".pdf,.doc,.docx" :on-change="onFile">
        <el-icon class="el-icon--upload"><UploadFilled /></el-icon>
        <div class="el-upload__text">点击或拖拽上传简历</div>
        <template #tip><div class="el-upload__tip">支持 Word/PDF，单文件不超过 20MB</div></template>
      </el-upload>
      <template #footer>
        <el-button type="primary" :loading="uploading" @click="doUpload">上传</el-button>
      </template>
    </el-dialog>

    <RecordPickerDialog
      v-model="pickerVisible"
      title="选择要分析的简历"
      hint="请选择一份简历后再开始 AI 分析"
      empty-text="请先上传简历"
      :items="resumePickerItems"
      @confirm="onPickResume"
    />
    <AiProgressDialog
      v-model="progressVisible"
      :task-id="taskId"
      variant="resume"
      :poll-fn="resumeApi.pollTask"
      @done="onAnalyzeDone"
    />
    <ResumeAiSuggestDialog
      v-model="suggestVisible"
      :data="analysisData"
      :adopted="!!currentResume?.ai_adopted"
      :view-result="suggestViewResult"
      @deep-optimize="openDeepOptimizeInput"
      @adopt="openAdopt"
    />
    <DeepOptimizeInputDialog
      v-model="deepInputVisible"
      :loading="deepOptimizing"
      @submit="runDeepOptimize"
    />
    <ResumeOptimizedPreviewDialog
      v-model="optPreviewVisible"
      :data="optimizedPreview"
      :saving="savingOptimized"
      @save="saveOptimized"
    />
    <ResumePreviewDialog
      v-model="previewVisible"
      :blob="previewBlob"
      :file-name="previewRow?.file_name as string"
      :file-type="previewRow?.file_type as string"
      @download="downloadPreview"
    />
  </div>
</template>

<script setup lang="ts">
import { ref, computed, onMounted } from 'vue'
import { useSessionRefresh } from '@/composables/useSessionRefresh'
import { Plus, Document, UploadFilled, View, Delete, MagicStick, DataBoard } from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'
import { showInfoToast } from '@/utils/message'
import { resumeApi } from '@/api'
import { useUserStore } from '@/stores/user'
import AiProgressDialog from '@/components/ai/AiProgressDialog.vue'
import ResumeAiSuggestDialog from '@/components/resume/ResumeAiSuggestDialog.vue'
import ResumePreviewDialog from '@/components/resume/ResumePreviewDialog.vue'
import DeepOptimizeInputDialog from '@/components/resume/DeepOptimizeInputDialog.vue'
import ResumeOptimizedPreviewDialog, {
  type OptimizedPreview,
} from '@/components/resume/ResumeOptimizedPreviewDialog.vue'
import RecordPickerDialog, { type PickerRecord } from '@/components/common/RecordPickerDialog.vue'
import { showMacToast } from '@/utils/macMessage'
import { parseResumeAiAnalysis, hasResumeAiAnalysis } from '@/utils/resumeAnalysis'

const store = useUserStore()
const list = ref<Record<string, unknown>[]>([])
const loading = ref(false)
const page = ref(1)
const total = ref(0)
const activeTab = ref('all')

const uploadVisible = ref(false)
const uploadFile = ref<File | null>(null)
const uploading = ref(false)

const pickerVisible = ref(false)
const progressVisible = ref(false)
const taskId = ref('')
const suggestVisible = ref(false)
const suggestViewResult = ref(false)
const analysisData = ref<Record<string, unknown> | null>(null)
const currentResume = ref<Record<string, unknown> | null>(null)
const deepInputVisible = ref(false)
const deepOptimizing = ref(false)
const optPreviewVisible = ref(false)
const optimizedPreview = ref<OptimizedPreview | null>(null)
const savingOptimized = ref(false)

const previewVisible = ref(false)
const previewBlob = ref<Blob | null>(null)
const previewRow = ref<Record<string, unknown> | null>(null)

const resumePickerItems = computed<PickerRecord[]>(() =>
  list.value
    .filter((r) => !r.ai_adopted)
    .map((r) => ({
      id: r.id as number,
      title: String(r.file_name),
      subtitle: r.file_type === 'pdf' ? 'PDF' : 'Word',
      meta: r.score && Number(r.score) > 0 ? '已有 AI 评分' : '未分析',
    }))
)

function clearPageData() {
  list.value = []
  total.value = 0
  page.value = 1
  uploadVisible.value = false
  pickerVisible.value = false
  progressVisible.value = false
  suggestVisible.value = false
  deepInputVisible.value = false
  optPreviewVisible.value = false
  previewVisible.value = false
  previewBlob.value = null
  currentResume.value = null
  analysisData.value = null
  optimizedPreview.value = null
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
  const params: Record<string, unknown> = { page: page.value, page_size: 10 }
  if (activeTab.value !== 'all') params.file_type = activeTab.value
  try {
    const res = await resumeApi.list(params) as { items: Record<string, unknown>[]; total: number }
    list.value = res.items
    total.value = res.total
  } finally {
    loading.value = false
  }
}

function formatTime(t: string) {
  return new Date(t).toLocaleString('zh-CN', { hour12: false })
}

function openUpload() {
  if (!store.requireLogin()) return
  uploadVisible.value = true
}

function onFile(f: { raw: File }) {
  uploadFile.value = f.raw
}

async function doUpload() {
  if (!uploadFile.value) return
  uploading.value = true
  try {
    await resumeApi.upload(uploadFile.value)
    showMacToast('上传成功')
    uploadVisible.value = false
    load()
  } finally {
    uploading.value = false
  }
}

async function preview(row: Record<string, unknown>) {
  if (!store.requireLogin()) return
  previewRow.value = row
  try {
    previewBlob.value = await resumeApi.previewBlob(row.id as number)
    previewVisible.value = true
  } catch {
    /* handled */
  }
}

async function downloadPreview() {
  if (!previewRow.value) return
  try {
    const blob = await resumeApi.exportBlob(previewRow.value.id as number, 'pdf')
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = String(previewRow.value.file_name || 'resume')
    a.click()
    URL.revokeObjectURL(url)
  } catch {
    /* handled */
  }
}

function openBannerPicker() {
  if (!store.requireLogin()) return
  if (!list.value.length) {
    showInfoToast('请先上传简历')
    return
  }
  if (!resumePickerItems.value.length) {
    showInfoToast('已采纳的记录不可重新分析')
    return
  }
  pickerVisible.value = true
}

function onPickResume(item: PickerRecord) {
  const row = list.value.find((r) => r.id === item.id)
  if (row) analyze(row)
}

function hasAiResult(row: Record<string, unknown>) {
  return hasResumeAiAnalysis(row)
}

function openAnalysisResult(row: Record<string, unknown>) {
  if (!store.requireLogin()) return
  const parsed = parseResumeAiAnalysis(row.ai_analysis)
  if (!parsed) {
    showInfoToast('暂无 AI 分析结果，请先使用 AI 分析')
    return
  }
  currentResume.value = row
  suggestViewResult.value = true
  analysisData.value = {
    ...parsed,
    score: parsed.score ?? row.score,
  }
  suggestVisible.value = true
}

async function analyze(row: Record<string, unknown> | null) {
  if (!row || !store.requireLogin()) return
  if (row.ai_adopted) {
    showInfoToast('已采纳 AI 分析，不可重新分析')
    return
  }
  currentResume.value = row
  suggestViewResult.value = false
  const res = await resumeApi.analyze(row.id as number) as { task_id: string }
  taskId.value = res.task_id
  progressVisible.value = true
}

function onAnalyzeDone(result: unknown) {
  suggestViewResult.value = false
  analysisData.value = result as Record<string, unknown>
  suggestVisible.value = true
  if (currentResume.value) {
    currentResume.value.ai_adopted = false
    if ((result as Record<string, unknown>)?.score != null) {
      currentResume.value.score = (result as Record<string, unknown>).score
    }
  }
  load()
}

async function openAdopt() {
  const id = currentResume.value?.id as number
  if (!id) return
  const s = (analysisData.value?.score as number) || undefined
  try {
    await resumeApi.adoptAi(id, s)
    if (currentResume.value) currentResume.value.ai_adopted = true
    showMacToast('已采纳 AI 分析')
    load()
  } catch {
    /* handled */
  }
}

function openDeepOptimizeInput() {
  if (!currentResume.value) return
  suggestVisible.value = false
  deepInputVisible.value = true
}

async function runDeepOptimize(requirement: string) {
  if (!currentResume.value) return
  deepOptimizing.value = true
  try {
    const res = await resumeApi.deepOptimize(currentResume.value.id as number, requirement) as {
      preview: OptimizedPreview
    }
    optimizedPreview.value = res.preview
    deepInputVisible.value = false
    optPreviewVisible.value = true
  } catch {
    /* handled */
  } finally {
    deepOptimizing.value = false
  }
}

async function saveOptimized(preview: OptimizedPreview) {
  if (!currentResume.value) return
  savingOptimized.value = true
  try {
    await resumeApi.saveOptimizedPreview(currentResume.value.id as number, preview)
    showMacToast('优化内容已保存')
    optPreviewVisible.value = false
  } finally {
    savingOptimized.value = false
  }
}

async function remove(row: Record<string, unknown>) {
  await ElMessageBox.confirm('确定删除？', '提示', { type: 'warning' })
  await resumeApi.remove(row.id as number)
  showMacToast('已删除')
  load()
}
</script>

<style scoped lang="scss">
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.file-cell {
  display: flex;
  align-items: center;
  gap: 8px;
}
.result-btn {
  :deep(.el-icon) {
    font-size: 18px;
    color: #0ea5e9;
  }
  &:hover:not(.is-disabled) :deep(.el-icon) {
    color: #0284c7;
  }
  &.is-disabled :deep(.el-icon) {
    color: #cbd5e1;
  }
}
.ai-btn {
  :deep(.el-icon) {
    font-size: 18px;
    color: #8b5cf6;
  }
  &:hover:not(.is-disabled) :deep(.el-icon) {
    color: #7c3aed;
  }
  &.is-disabled :deep(.el-icon) {
    color: #cbd5e1;
  }
}
.rate-cell {
  display: inline-flex;
  align-items: center;
  :deep(.el-rate__text) {
    display: none !important;
  }
}
.score-empty {
  font-size: 13px;
  color: #94a3b8;
}
.upload-dialog-header {
  display: flex;
  align-items: center;
  gap: 10px;
}
.upload-dialog-title {
  font-size: 16px;
  font-weight: 600;
}
.dialog-close-red {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: none;
  background: #ff5f57;
  cursor: pointer;
  padding: 0;
}
</style>
