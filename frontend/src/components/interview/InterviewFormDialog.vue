<template>
  <el-dialog
    v-model="visible"
    width="920px"
    class="interview-form-dialog"
    align-center
    destroy-on-close
    :show-close="false"
  >
    <template #header>
      <div class="form-chrome">
        <button
          type="button"
          class="dialog-close-red"
          aria-label="关闭"
          @click="visible = false"
        />
        <span class="form-title">{{ dialogTitle }}</span>
        <div v-if="form.ai_adopted" class="adopted-stamp" title="已采纳 AI 分析">
          <el-icon><StarFilled /></el-icon>
          <span>已采纳</span>
        </div>
        <el-tag v-if="mode === 'preview'" type="info" size="small" effect="plain">只读</el-tag>
        <el-tag v-else-if="mode === 'create'" type="success" size="small" effect="plain">新建</el-tag>
      </div>
    </template>

    <!-- 预览：单列纵向，避免左右分栏滚动时左侧留白 -->
    <div v-if="mode === 'preview'" class="preview-layout">
      <section class="preview-hero">
        <div class="hero-top">
          <div class="hero-company">
            <span class="hero-label">公司</span>
            <span class="hero-value">{{ form.company_name }}</span>
          </div>
          <div class="hero-job">
            <span class="hero-label">岗位</span>
            <span class="hero-value">{{ form.job_title }}</span>
          </div>
        </div>
        <div class="hero-meta">
          <div class="meta-chip">
            <el-icon><Clock /></el-icon>
            {{ formatInterviewTime(form.interview_time) }}
          </div>
          <div class="meta-chip">
            <el-icon><View /></el-icon>
            {{ visibilityText }}
          </div>
          <div v-if="hasScore" class="meta-chip score-chip">
            <el-icon><StarFilled /></el-icon>
            <div class="rate-stars-only">
              <el-rate :model-value="Number(form.score)" disabled allow-half :show-score="false" />
            </div>
          </div>
        </div>
      </section>

      <div class="preview-grid">
        <section class="form-section">
          <h3 class="section-title">
            <el-icon><Document /></el-icon>
            岗位 JD
          </h3>
          <p class="readonly-text">{{ form.job_jd || '（未填写）' }}</p>
        </section>
        <section class="form-section">
          <h3 class="section-title">
            <el-icon><EditPen /></el-icon>
            备注
          </h3>
          <p class="readonly-text">{{ form.remark || '（未填写）' }}</p>
        </section>
        <section class="form-section">
          <h3 class="section-title">
            <el-icon><Microphone /></el-icon>
            面试录音
          </h3>
          <div v-if="!form.audio_url" class="audio-empty">未上传录音</div>
          <div v-else class="audio-player-wrap">
            <audio :src="form.audio_url" controls class="audio-player" />
          </div>
        </section>
        <section class="form-section">
          <h3 class="section-title">
            <el-icon><View /></el-icon>
            可见性
          </h3>
          <p class="readonly-text">{{ visibilityText }}{{ form.visibility === 1 && form.public_audio ? ' · 公开录音' : '' }}</p>
        </section>
      </div>

      <section class="form-section preview-ai-full">
        <h3 class="section-title">
          <el-icon><MagicStick /></el-icon>
          AI 复盘
          <span v-if="form.ai_adopted" class="inline-adopted">已采纳</span>
        </h3>
        <p v-if="form.ai_adopted" class="ai-hint adopted-hint">以下为已采纳的 AI 分析结果</p>
        <div v-if="parsedAnalysis" class="ai-preview-body">
          <div v-if="analysisSummary" class="ai-summary-block">
            <span class="summary-label">分析摘要</span>
            <p>{{ analysisSummary }}</p>
          </div>
          <div v-if="analysisHighlights.length" class="ai-list-block highlight">
            <span class="list-label">亮点</span>
            <ul>
              <li v-for="(h, i) in analysisHighlights" :key="i">{{ h }}</li>
            </ul>
          </div>
          <div v-if="analysisImprovements.length" class="ai-list-block improve">
            <span class="list-label">待改进</span>
            <ul>
              <li v-for="(h, i) in analysisImprovements" :key="i">{{ h }}</li>
            </ul>
          </div>
          <div v-if="analysisTabBlocks.length" class="ai-tabs-blocks">
            <div v-for="(block, i) in analysisTabBlocks" :key="i" class="ai-tab-card">
              <span class="tab-card-title">{{ block.label }}</span>
              <p class="tab-card-text">{{ block.text }}</p>
            </div>
          </div>
        </div>
        <p v-else class="ai-empty">暂无 AI 分析内容</p>
      </section>
    </div>

    <div v-else class="form-layout">
      <div class="form-main">
        <section class="form-section form-section-basic">
          <h3 class="section-title">
            <el-icon><OfficeBuilding /></el-icon>
            基本信息
          </h3>
          <el-form :model="form" label-position="top" class="styled-form">
            <el-row :gutter="16">
              <el-col :span="12">
                <el-form-item label="公司名称" required class="form-field-item">
                  <el-input
                    v-model="form.company_name"
                    placeholder="请输入公司名称"
                    size="large"
                    class="form-field-input"
                    clearable
                  >
                    <template #prefix>
                      <el-icon class="field-prefix"><OfficeBuilding /></el-icon>
                    </template>
                  </el-input>
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="岗位名称" required class="form-field-item">
                  <el-input
                    v-model="form.job_title"
                    placeholder="请输入岗位名称"
                    size="large"
                    class="form-field-input"
                    clearable
                  >
                    <template #prefix>
                      <el-icon class="field-prefix"><Briefcase /></el-icon>
                    </template>
                  </el-input>
                </el-form-item>
              </el-col>
            </el-row>
            <el-form-item label="面试时间" required class="form-field-item">
              <div class="datetime-field">
                <el-icon class="datetime-prefix"><Clock /></el-icon>
                <el-date-picker
                  v-model="form.interview_time"
                  type="datetime"
                  value-format="YYYY-MM-DDTHH:mm:ss"
                  placeholder="选择面试时间"
                  size="large"
                  class="form-field-input datetime-picker"
                />
              </div>
            </el-form-item>
            <el-form-item label="岗位 JD" class="form-field-item">
              <el-input
                v-model="form.job_jd"
                type="textarea"
                :rows="4"
                maxlength="1000"
                show-word-limit
                placeholder="粘贴或输入岗位描述，AI 将仅依据此处内容分析"
                class="form-field-textarea"
                resize="none"
              />
              <p class="field-hint">建议填写岗位职责与要求，便于 AI 针对性分析</p>
            </el-form-item>
            <el-form-item label="备注" class="form-field-item form-field-item-last">
              <el-input
                v-model="form.remark"
                type="textarea"
                :rows="3"
                maxlength="500"
                show-word-limit
                placeholder="记录面试过程、感受等，材料越完整分析越准确"
                class="form-field-textarea"
                resize="none"
              />
            </el-form-item>
          </el-form>
        </section>

        <section class="form-section">
          <h3 class="section-title">
            <el-icon><Microphone /></el-icon>
            面试录音
          </h3>
          <el-upload
              class="audio-upload"
              drag
              :auto-upload="false"
              :limit="1"
              accept=".mp3,.wav,.m4a"
              :on-change="onAudioChange"
            >
              <div class="upload-inner">
                <el-icon :size="32" color="#3b82f6"><UploadFilled /></el-icon>
                <p class="upload-title">点击或拖拽上传录音</p>
                <p class="upload-sub">mp3 / wav / m4a，单文件不超过 200MB</p>
              </div>
            </el-upload>
          <div v-if="form.audio_url" class="audio-player-wrap">
            <audio :src="form.audio_url" controls class="audio-player" />
          </div>
        </section>
      </div>

      <aside class="form-aside">
        <section class="aside-card">
          <h3 class="section-title">
            <el-icon><View /></el-icon>
            可见性
          </h3>
          <el-radio-group v-model="form.visibility" class="visibility-card-group">
            <el-radio :value="1" class="visibility-card">
              <span class="v-title">公开</span>
              <span class="v-desc">所有人可见</span>
            </el-radio>
            <el-radio :value="2" class="visibility-card">
              <span class="v-title">仅好友</span>
              <span class="v-desc">好友可见</span>
            </el-radio>
            <el-radio :value="0" class="visibility-card">
              <span class="v-title">私密</span>
              <span class="v-desc">仅自己可见</span>
            </el-radio>
          </el-radio-group>
          <el-checkbox
            v-if="form.visibility === 1"
            v-model="publicAudioChecked"
            class="public-audio-check"
          >
            公开录音（面试分享中可播放）
          </el-checkbox>
        </section>

        <section class="aside-card ai-card">
          <h3 class="section-title">
            <el-icon><MagicStick /></el-icon>
            AI 复盘
          </h3>

          <template v-if="form.ai_adopted">
            <p class="ai-hint adopted-hint">已采纳 AI 分析，不可再次分析</p>
            <div v-if="parsedAnalysis" class="ai-preview-body compact">
              <div v-if="analysisSummary" class="ai-summary">
                <span class="summary-label">分析摘要</span>
                <p>{{ analysisSummary }}</p>
              </div>
            </div>
          </template>
          <template v-else>
            <p class="ai-hint">分析依据本记录的岗位、JD、备注与录音；完成后可在结果弹窗中采纳。</p>
            <el-button
              type="primary"
              class="ai-btn"
              :disabled="!recordId"
              @click="emit('analyze')"
            >
              使用 AI 分析
            </el-button>
            <div v-if="form.ai_analysis" class="ai-summary">
              <span class="summary-label">分析摘要</span>
              <p>{{ analysisSummary }}</p>
            </div>
          </template>
        </section>

        <section v-if="form.score != null && Number(form.score) > 0" class="aside-card score-card">
          <h3 class="section-title">
            <el-icon><StarFilled /></el-icon>
            AI 评分
            <span v-if="form.ai_adopted" class="adopted-badge">已采纳</span>
          </h3>
          <div class="rate-stars-only">
            <el-rate :model-value="Number(form.score)" disabled allow-half :show-score="false" />
          </div>
          <p class="score-tip">
            {{ form.ai_adopted ? '您已采纳本次 AI 分析结果' : '完成分析后可在结果弹窗中点击「采纳 AI 分析」' }}
          </p>
        </section>
      </aside>
    </div>

    <template v-if="mode !== 'preview'" #footer>
      <div class="form-footer">
        <el-button class="btn-cancel" @click="visible = false">取消</el-button>
        <el-button type="primary" class="btn-primary" :loading="saving" @click="save">保存</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, reactive, computed, watch } from 'vue'
import {
  UploadFilled,
  OfficeBuilding,
  Briefcase,
  Microphone,
  View,
  MagicStick,
  StarFilled,
  Clock,
  Document,
  EditPen,
} from '@element-plus/icons-vue'
import { parseInterviewAiAnalysis } from '@/utils/interviewAnalysis'

export interface InterviewForm {
  id?: number
  company_name: string
  job_title: string
  job_jd: string
  remark: string
  interview_time: string
  visibility: number
  public_audio: number
  audio_url?: string
  ai_analysis?: string
  score?: number
  ai_adopted?: boolean
}

const props = defineProps<{
  modelValue: boolean
  mode: 'create' | 'edit' | 'preview'
  data?: InterviewForm | null
  recordId?: number
}>()
const emit = defineEmits<{
  'update:modelValue': [boolean]
  save: [InterviewForm, File | null]
  analyze: []
}>()

const visible = ref(false)
const saving = ref(false)
const audioFile = ref<File | null>(null)
const form = reactive<InterviewForm>({
  company_name: '',
  job_title: '',
  job_jd: '',
  remark: '',
  interview_time: new Date().toISOString().slice(0, 19),
  visibility: 1,
  public_audio: 0,
  score: 0,
  ai_adopted: false,
})

const dialogTitle = computed(() => {
  if (props.mode === 'preview') return '预览面试记录'
  if (props.mode === 'edit') return '编辑面试记录'
  return '新增面试记录'
})

const publicAudioChecked = computed({
  get: () => form.public_audio === 1,
  set: (v) => {
    form.public_audio = v ? 1 : 0
  },
})

const parsedAnalysis = computed(() => parseInterviewAiAnalysis(form.ai_analysis))

const analysisSummary = computed(() => {
  const d = parsedAnalysis.value
  if (d?.overall) return String(d.overall)
  if (!form.ai_analysis) return ''
  return String(form.ai_analysis).slice(0, 500)
})

const analysisHighlights = computed(() => {
  const h = parsedAnalysis.value?.highlights
  return Array.isArray(h) ? (h as string[]).filter(Boolean) : []
})

const analysisImprovements = computed(() => {
  const im = parsedAnalysis.value?.improvements
  return Array.isArray(im) ? (im as string[]).filter(Boolean) : []
})

const hasScore = computed(() => form.score != null && Number(form.score) > 0)

const visibilityText = computed(() => {
  if (form.visibility === 1) return '公开'
  if (form.visibility === 2) return '仅好友可见'
  return '私密'
})

const TAB_LABELS: Record<string, string> = {
  comprehensive: '综合建议',
  problems: '问题分析',
  highlights_eval: '亮点评估',
  plan: '提升计划',
}

const analysisTabBlocks = computed(() => {
  const tabs = parsedAnalysis.value?.tabs as Record<string, string> | undefined
  if (!tabs) return []
  return Object.entries(TAB_LABELS)
    .map(([key, label]) => {
      const text = tabs[key]?.trim()
      return text ? { label, text } : null
    })
    .filter((x): x is { label: string; text: string } => x != null)
})

function formatInterviewTime(t: string) {
  if (!t) return '-'
  return new Date(t).toLocaleString('zh-CN', { hour12: false })
}

const emptyForm = (): InterviewForm => ({
  company_name: '',
  job_title: '',
  job_jd: '',
  remark: '',
  interview_time: new Date().toISOString().slice(0, 19),
  visibility: 1,
  public_audio: 0,
  score: 0,
  ai_adopted: false,
})

watch(
  () => props.modelValue,
  (v) => {
    visible.value = v
    if (v && props.data) {
      audioFile.value = null
      Object.assign(form, emptyForm(), props.data, {
        score: props.data.score != null ? Number(props.data.score) : 0,
        ai_adopted: Boolean(props.data.ai_adopted),
      })
    } else if (v && props.mode === 'create') {
      audioFile.value = null
      Object.assign(form, emptyForm())
    }
  }
)
watch(visible, (v) => emit('update:modelValue', v))

function onAudioChange(file: { raw?: File }) {
  if (file.raw) audioFile.value = file.raw
}

function save() {
  emit('save', { ...form }, audioFile.value)
}

defineExpose({ setSaving: (v: boolean) => { saving.value = v } })
</script>

<style scoped lang="scss">
.form-chrome {
  display: flex;
  align-items: center;
  gap: 10px;
}

.dialog-close-red {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: none;
  background: #ff5f57;
  cursor: pointer;
  flex-shrink: 0;
  padding: 0;
}

.form-title {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
}

.adopted-stamp {
  display: inline-flex;
  align-items: center;
  gap: 4px;
  padding: 4px 10px;
  border: 2px solid #f59e0b;
  border-radius: 6px;
  color: #d97706;
  font-size: 12px;
  font-weight: 700;
  transform: rotate(-8deg);
  background: rgba(255, 251, 235, 0.9);
  box-shadow: 0 1px 0 rgba(245, 158, 11, 0.35);
  margin-left: 4px;

  .el-icon {
    font-size: 14px;
  }
}

.preview-layout {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.preview-hero {
  background: linear-gradient(135deg, #eff6ff 0%, #f8fafc 100%);
  border: 1px solid #dbeafe;
  border-radius: 14px;
  padding: 16px 20px;
}

.hero-top {
  display: flex;
  flex-wrap: wrap;
  gap: 20px 32px;
  margin-bottom: 12px;
}

.hero-company,
.hero-job {
  display: flex;
  flex-direction: column;
  gap: 4px;
  min-width: 140px;
}

.hero-label {
  font-size: 12px;
  color: #64748b;
}

.hero-value {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
}

.hero-meta {
  display: flex;
  flex-wrap: wrap;
  align-items: center;
  gap: 10px;
}

.meta-chip {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 6px 12px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
  font-size: 13px;
  color: #475569;

  &.score-chip {
    gap: 4px;
  }
}

.preview-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 16px;

  @media (max-width: 720px) {
    grid-template-columns: 1fr;
  }
}

.preview-ai-full {
  background: linear-gradient(160deg, #eff6ff 0%, #fff 100%);
  border-color: #dbeafe;

  .inline-adopted {
    margin-left: auto;
    font-size: 11px;
    font-weight: 600;
    color: #d97706;
    padding: 2px 8px;
    border: 1.5px solid #fbbf24;
    border-radius: 4px;
    background: #fffbeb;
  }

  .section-title {
    width: 100%;
  }
}

.readonly-text {
  margin: 0;
  font-size: 14px;
  color: #475569;
  line-height: 1.7;
  white-space: pre-wrap;
  word-break: break-word;
}

.ai-summary-block {
  padding: 14px 16px;
  background: #fff;
  border-radius: 10px;
  border: 1px solid #e2e8f0;

  .summary-label {
    font-size: 12px;
    font-weight: 600;
    color: #0369a1;
  }
  p {
    margin: 8px 0 0;
    font-size: 14px;
    color: #334155;
    line-height: 1.7;
  }
}

.ai-tabs-blocks {
  display: grid;
  grid-template-columns: repeat(2, 1fr);
  gap: 12px;

  @media (max-width: 640px) {
    grid-template-columns: 1fr;
  }
}

.ai-tab-card {
  padding: 12px 14px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 10px;

  .tab-card-title {
    display: block;
    font-size: 13px;
    font-weight: 600;
    color: #1e293b;
    margin-bottom: 8px;
  }
  .tab-card-text {
    margin: 0;
    font-size: 13px;
    color: #475569;
    line-height: 1.65;
    white-space: pre-wrap;
  }
}

.form-layout {
  display: flex;
  gap: 20px;
  align-items: flex-start;
}

.form-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.form-section,
.aside-card {
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  padding: 20px 22px;
  box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04);
}

.section-title {
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  margin: 0 0 16px;

  .el-icon {
    color: #3b82f6;
  }
}

.form-section-basic {
  background: linear-gradient(180deg, #fff 0%, #fafbfc 100%);
}

.styled-form {
  :deep(.form-field-item) {
    margin-bottom: 18px;
  }

  :deep(.form-field-item-last) {
    margin-bottom: 0;
  }

  :deep(.el-form-item__label) {
    font-size: 13px;
    font-weight: 600;
    color: #334155;
    line-height: 1.4;
    padding-bottom: 6px;

    &::before {
      color: #ef4444 !important;
    }
  }

  :deep(.form-field-input .el-input__wrapper) {
    border-radius: 10px;
    padding: 4px 12px 4px 8px;
    background: #f8fafc;
    box-shadow: 0 0 0 1px #e2e8f0 inset;
    transition: box-shadow 0.2s, background 0.2s;

    &:hover {
      background: #fff;
      box-shadow: 0 0 0 1px #cbd5e1 inset;
    }

    &.is-focus {
      background: #fff;
      box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.35) inset;
    }
  }

  :deep(.field-prefix) {
    color: #94a3b8;
    font-size: 16px;
  }

  :deep(.form-field-textarea .el-textarea__inner) {
    border-radius: 10px;
    padding: 12px 14px;
    background: #f8fafc;
    border: none;
    box-shadow: 0 0 0 1px #e2e8f0 inset;
    font-size: 14px;
    line-height: 1.65;
    color: #1e293b;
    transition: box-shadow 0.2s, background 0.2s;

    &::placeholder {
      color: #94a3b8;
    }

    &:hover {
      background: #fff;
      box-shadow: 0 0 0 1px #cbd5e1 inset;
    }

    &:focus {
      background: #fff;
      box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.35) inset;
    }
  }

  :deep(.el-input__count) {
    background: transparent;
    color: #94a3b8;
    font-size: 12px;
  }
}

.datetime-field {
  position: relative;
  width: 100%;

  .datetime-prefix {
    position: absolute;
    left: 14px;
    top: 50%;
    transform: translateY(-50%);
    z-index: 2;
    color: #94a3b8;
    font-size: 16px;
    pointer-events: none;
  }

  :deep(.datetime-picker) {
    width: 100%;

    .el-input__wrapper {
      padding-left: 36px;
      border-radius: 10px;
      background: #f8fafc;
      box-shadow: 0 0 0 1px #e2e8f0 inset;
      transition: box-shadow 0.2s, background 0.2s;

      &:hover {
        background: #fff;
        box-shadow: 0 0 0 1px #cbd5e1 inset;
      }

      &.is-focus {
        background: #fff;
        box-shadow: 0 0 0 2px rgba(59, 130, 246, 0.35) inset;
      }
    }
  }
}

.field-hint {
  margin: 6px 0 0;
  font-size: 12px;
  color: #94a3b8;
  line-height: 1.4;
}

.audio-upload {
  width: 100%;
  :deep(.el-upload-dragger) {
    border: none;
    background: transparent;
    padding: 0;
  }
}

.upload-inner {
  padding: 32px 20px;
  background: linear-gradient(180deg, #f0f9ff 0%, #fff 100%);
  border: 2px dashed #93c5fd;
  border-radius: 14px;
  text-align: center;
  transition: border-color 0.2s, background 0.2s;

  &:hover {
    border-color: #3b82f6;
    background: linear-gradient(180deg, #eff6ff 0%, #f8fafc 100%);
  }

  .upload-title {
    margin: 10px 0 4px;
    font-size: 14px;
    font-weight: 600;
    color: #2563eb;
  }
  .upload-sub {
    font-size: 12px;
    color: #94a3b8;
  }
}

.audio-player-wrap {
  margin-top: 12px;
  padding: 12px;
  background: #f8fafc;
  border-radius: 10px;
}

.audio-player {
  width: 100%;
}

.audio-empty {
  font-size: 13px;
  color: #94a3b8;
  padding: 12px 0;
}

.form-aside {
  width: 280px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.visibility-card-group {
  display: flex;
  flex-direction: column;
  gap: 8px;
  width: 100%;

  :deep(.el-radio) {
    width: 100%;
    height: auto;
    margin-right: 0;
    padding: 0;
    border: none;
    background: transparent;

    .el-radio__input {
      display: none;
    }

    .el-radio__label {
      width: 100%;
      padding: 0;
    }
  }

  :deep(.visibility-card) {
    display: block;
    width: 100%;
    padding: 10px 12px;
    border-radius: 10px;
    border: 1px solid #e2e8f0;
    background: #f8fafc;
    cursor: pointer;
    transition: border-color 0.2s, background 0.2s, box-shadow 0.2s;

    .v-title {
      display: block;
      font-size: 14px;
      font-weight: 600;
      color: #334155;
      line-height: 1.3;
    }

    .v-desc {
      display: block;
      font-size: 11px;
      color: #94a3b8;
      margin-top: 2px;
    }

    &:hover {
      border-color: #93c5fd;
      background: #fff;
    }

    &.is-checked {
      border-color: #3b82f6;
      background: linear-gradient(135deg, #eff6ff 0%, #fff 100%);
      box-shadow: 0 0 0 1px rgba(59, 130, 246, 0.2);

      .v-title {
        color: #1d4ed8;
      }
    }
  }
}

.public-audio-check {
  margin-top: 12px;
}

.ai-card {
  background: linear-gradient(160deg, #eff6ff 0%, #f8fafc 100%);
  border-color: #dbeafe;
}

.ai-hint {
  font-size: 12px;
  color: #64748b;
  line-height: 1.5;
  margin: 0 0 12px;

  &.adopted-hint {
    color: #b45309;
    font-weight: 500;
  }
}

.ai-empty {
  font-size: 13px;
  color: #94a3b8;
  margin: 8px 0;
}

.ai-preview-body {
  display: flex;
  flex-direction: column;
  gap: 12px;

  &.compact {
    margin-top: 4px;
  }
}

.ai-list-block {
  padding: 10px 12px;
  border-radius: 8px;
  font-size: 13px;

  &.highlight {
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
  }
  &.improve {
    background: #fffbeb;
    border: 1px solid #fde68a;
  }

  .list-label {
    display: block;
    font-weight: 600;
    margin-bottom: 6px;
    color: #475569;
  }

  ul {
    margin: 0;
    padding-left: 18px;
    color: #475569;
    line-height: 1.6;
  }
}

.ai-btn {
  width: 100%;
  border-radius: 8px;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  border: none;
}

.ai-summary {
  margin-top: 14px;
  padding-top: 12px;
  border-top: 1px solid #dbeafe;

  .summary-label {
    font-size: 12px;
    font-weight: 600;
    color: #0369a1;
  }
  p {
    margin: 8px 0 0;
    font-size: 13px;
    color: #475569;
    line-height: 1.6;
  }
}

.score-card {
  .adopted-badge {
    margin-left: auto;
    font-size: 11px;
    font-weight: 600;
    color: #d97706;
    padding: 2px 8px;
    border: 1.5px solid #fbbf24;
    border-radius: 4px;
    transform: rotate(-6deg);
    background: #fffbeb;
  }

  .section-title {
    display: flex;
    align-items: center;
    width: 100%;
  }

  .rate-stars-only {
    :deep(.el-rate__text) {
      display: none !important;
    }
  }

  .score-tip {
    margin: 8px 0 0;
    font-size: 12px;
    color: #94a3b8;
  }
}

.form-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  width: 100%;

  .btn-cancel {
    border-radius: 10px;
    min-width: 88px;
    color: #64748b;
    border-color: #e2e8f0;
    background: #fff;

    &:hover {
      color: #334155;
      border-color: #cbd5e1;
      background: #f8fafc;
    }
  }

  .btn-primary {
    border-radius: 10px;
    min-width: 96px;
    background: linear-gradient(135deg, #3b82f6, #2563eb);
    border: none;
    box-shadow: 0 4px 14px rgba(37, 99, 235, 0.28);

    &:hover {
      background: linear-gradient(135deg, #2563eb, #1d4ed8);
    }
  }
}
</style>

<style lang="scss">
.interview-form-dialog.el-dialog {
  border-radius: 16px;
  overflow: hidden;
  padding: 0;
  box-shadow: 0 22px 70px rgba(0, 0, 0, 0.16);

  .el-dialog__header {
    margin: 0;
    padding: 14px 20px 12px;
    background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
    border-bottom: 1px solid #e2e8f0;
  }

  .el-dialog__body {
    padding: 16px 20px;
    background: #f1f5f9;
    max-height: 70vh;
    overflow-y: auto;
  }

  .el-dialog__footer {
    padding: 12px 20px 16px;
    border-top: 1px solid #e2e8f0;
    background: #fff;
  }
}
</style>
