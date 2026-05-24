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
          <el-tooltip
            :content="hasAiResult(row) ? '查看 AI 分析结果' : '请先进行 AI 分析'"
            placement="top"
          >
            <span class="result-btn-wrap">
              <el-button
                link
                type="primary"
                class="result-btn"
                :disabled="!hasAiResult(row)"
                @click="openAnalysisResult(row)"
              >
                <el-icon><DataBoard /></el-icon>
              </el-button>
            </span>
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

    <el-dialog
      v-model="uploadVisible"
      width="520px"
      class="resume-upload-dialog"
      :show-close="false"
      align-center
      destroy-on-close
    >
      <template #header>
        <div class="upload-dialog-header">
          <button type="button" class="dialog-close-red" aria-label="关闭" @click="uploadVisible = false" />
          <span class="upload-dialog-title">上传简历</span>
        </div>
      </template>
      <div class="upload-dialog-body">
        <p class="upload-lead">将简历上传到云端，即可使用 AI 分析与在线预览</p>
        <el-upload
          drag
          class="resume-uploader"
          :auto-upload="false"
          :limit="1"
          accept=".pdf,.doc,.docx"
          :on-change="onFile"
          :on-exceed="onUploadExceed"
        >
          <div class="upload-inner">
            <div class="upload-icon-wrap">
              <el-icon class="upload-main-icon"><UploadFilled /></el-icon>
            </div>
            <p class="upload-main-text">点击或拖拽文件到此处</p>
            <p class="upload-sub-text">支持 PDF、Word（.doc / .docx）</p>
          </div>
        </el-upload>
        <div class="upload-tags">
          <span class="format-tag pdf">PDF</span>
          <span class="format-tag word">Word</span>
          <span class="size-hint">单文件不超过 20MB</span>
        </div>
        <p v-if="uploadFile" class="selected-file">
          <el-icon><Document /></el-icon>
          {{ uploadFile.name }}
        </p>
      </div>
      <template #footer>
        <div class="upload-dialog-footer">
          <el-button class="btn-cancel" @click="uploadVisible = false">取消</el-button>
          <el-button type="primary" class="btn-submit" :loading="uploading" :disabled="!uploadFile" @click="doUpload">
            开始上传
          </el-button>
        </div>
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
import { ref, computed, onMounted, nextTick } from 'vue'
import { useSessionRefresh } from '@/composables/useSessionRefresh'
import { Plus, Document, UploadFilled, View, Delete, MagicStick, DataBoard } from '@element-plus/icons-vue'
import { ElMessageBox } from 'element-plus'
import { showInfoToast, showErrorToast } from '@/utils/message'
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
import {
  parseResumeAiAnalysis,
  hasResumeAiAnalysis,
  normalizeResumeAnalysisResult,
} from '@/utils/resumeAnalysis'

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
  uploadFile.value = null
  uploadVisible.value = true
}

function onFile(f: { raw: File }) {
  uploadFile.value = f.raw
}

function onUploadExceed() {
  showInfoToast('每次仅可上传一个文件，请先移除已选文件')
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

async function openAnalysisResult(row: Record<string, unknown>) {
  if (!store.requireLogin()) return
  let source = row
  let parsed = parseResumeAiAnalysis(row.ai_analysis)
  if (!parsed) {
    try {
      source = (await resumeApi.get(row.id as number)) as Record<string, unknown>
      parsed = parseResumeAiAnalysis(source.ai_analysis)
    } catch {
      /* handled */
    }
  }
  if (!parsed) return
  currentResume.value = source
  suggestViewResult.value = true
  analysisData.value = {
    ...parsed,
    score: parsed.score ?? source.score,
  }
  if (suggestVisible.value) {
    suggestVisible.value = false
    await nextTick()
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

async function onAnalyzeDone(result: unknown) {
  suggestViewResult.value = false
  let data = normalizeResumeAnalysisResult(result)
  await load()
  if (!data && currentResume.value) {
    const row = list.value.find((r) => r.id === currentResume.value!.id)
    if (row) {
      currentResume.value = row
      data = parseResumeAiAnalysis(row.ai_analysis)
    }
  }
  if (!data) {
    showErrorToast('未获取到 AI 分析结果，请检查 DEEPSEEK_API_KEY 或稍后重试')
    return
  }
  analysisData.value = {
    ...data,
    score: data.score ?? currentResume.value?.score,
  }
  if (suggestVisible.value) {
    suggestVisible.value = false
    await nextTick()
  }
  suggestVisible.value = true
  if (currentResume.value) {
    currentResume.value.ai_adopted = false
    if (data.score != null) {
      currentResume.value.score = data.score
    }
  }
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
.result-btn-wrap {
  display: inline-flex;
  vertical-align: middle;
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
    color: #475569;
    cursor: not-allowed;
  }
  &.is-disabled {
    cursor: not-allowed;
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
  color: #0f172a;
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

<style lang="scss">
.resume-upload-dialog.el-dialog {
  border-radius: 16px;
  overflow: hidden;
  padding: 0;

  .el-dialog__header {
    margin: 0;
    padding: 14px 20px 10px;
    background: linear-gradient(180deg, #f8fafc 0%, #fff 100%);
    border-bottom: 1px solid #e2e8f0;
  }

  .el-dialog__body {
    padding: 0 20px 8px;
  }

  .el-dialog__footer {
    padding: 12px 20px 18px;
    border-top: 1px solid #f1f5f9;
  }
}

.resume-upload-dialog {
  .upload-dialog-body {
    padding-top: 8px;
  }

  .upload-lead {
    margin: 0 0 16px;
    font-size: 13px;
    color: #64748b;
    line-height: 1.5;
  }

  .resume-uploader {
    width: 100%;

    .el-upload {
      width: 100%;
    }

    .el-upload-dragger {
      width: 100%;
      height: auto;
      min-height: 168px;
      padding: 28px 20px;
      border: 2px dashed #93c5fd;
      border-radius: 14px;
      background: linear-gradient(180deg, #f0f9ff 0%, #fff 100%);
      transition: border-color 0.2s, background 0.2s;

      &:hover {
        border-color: #3b82f6;
        background: linear-gradient(180deg, #eff6ff 0%, #f8fafc 100%);
      }

      &.is-dragover {
        border-color: #2563eb;
        background: #dbeafe;
      }
    }

    .el-upload__text,
    .el-upload__tip {
      display: none;
    }
  }

  .upload-inner {
    text-align: center;
  }

  .upload-icon-wrap {
    width: 56px;
    height: 56px;
    margin: 0 auto 14px;
    border-radius: 14px;
    background: linear-gradient(135deg, #3b82f6, #60a5fa);
    display: flex;
    align-items: center;
    justify-content: center;
    box-shadow: 0 8px 20px rgba(59, 130, 246, 0.35);
  }

  .upload-main-icon {
    font-size: 28px;
    color: #fff;
  }

  .upload-main-text {
    margin: 0 0 6px;
    font-size: 15px;
    font-weight: 600;
    color: #1e293b;
  }

  .upload-sub-text {
    margin: 0;
    font-size: 13px;
    color: #94a3b8;
  }

  .upload-tags {
    display: flex;
    align-items: center;
    gap: 8px;
    margin-top: 14px;
    flex-wrap: wrap;
  }

  .format-tag {
    font-size: 12px;
    font-weight: 600;
    padding: 2px 10px;
    border-radius: 6px;

    &.pdf {
      background: #fee2e2;
      color: #dc2626;
    }

    &.word {
      background: #dbeafe;
      color: #2563eb;
    }
  }

  .size-hint {
    font-size: 12px;
    color: #94a3b8;
    margin-left: auto;
  }

  .selected-file {
    display: flex;
    align-items: center;
    gap: 8px;
    margin: 14px 0 0;
    padding: 10px 12px;
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    border-radius: 8px;
    font-size: 13px;
    color: #166534;
  }

  .upload-dialog-footer {
    display: flex;
    justify-content: flex-end;
    gap: 10px;
  }

  .btn-submit {
    min-width: 108px;
    border-radius: 8px;
    border: none;
    background: linear-gradient(135deg, #3b82f6, #2563eb);
  }
}
</style>
