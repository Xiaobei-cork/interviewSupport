<template>
  <el-dialog
    v-model="visible"
    width="720px"
    class="resume-opt-preview-dialog"
    align-center
    destroy-on-close
    :show-close="false"
    top="5vh"
  >
    <template #header>
      <div class="dlg-header-row">
        <button type="button" class="dialog-close-red" aria-label="关闭" @click="visible = false" />
        <span class="dlg-title">优化效果预览</span>
      </div>
    </template>

    <div v-if="form" class="preview-card">
      <div class="preview-header">
        <el-input v-model="form.name" class="name-input" placeholder="姓名" />
        <div class="contact-row">
          <el-input v-model="form.phone" placeholder="电话" size="small" />
          <span class="sep">|</span>
          <el-input v-model="form.email" placeholder="邮箱" size="small" />
          <span class="sep">|</span>
          <el-input v-model="form.location" placeholder="城市" size="small" />
        </div>
      </div>

      <section class="preview-section">
        <h3>个人简介</h3>
        <el-input v-model="form.summary" type="textarea" :rows="4" placeholder="个人简介" />
      </section>

      <section class="preview-section">
        <div class="section-head">
          <h3>工作经历</h3>
          <el-button link type="primary" size="small" @click="addExperience">+ 添加经历</el-button>
        </div>
        <div v-for="(exp, idx) in form.experiences" :key="idx" class="exp-block">
          <div class="exp-head">
            <el-input v-model="exp.period" placeholder="时间" size="small" style="width:140px" />
            <el-input v-model="exp.company" placeholder="公司" size="small" style="flex:1" />
            <el-input v-model="exp.title" placeholder="职位" size="small" style="flex:1" />
            <el-tag v-if="exp.current" type="success" size="small">至今</el-tag>
            <el-button link type="danger" size="small" @click="removeExperience(idx)">删除</el-button>
          </div>
          <div v-for="(_, bi) in exp.bullets" :key="bi" class="bullet-row">
            <span class="bullet-dot">•</span>
            <el-input v-model="exp.bullets[bi]" type="textarea" :rows="2" autosize placeholder="工作内容" />
            <el-button link type="danger" @click="removeBullet(idx, bi)">×</el-button>
          </div>
          <el-button link type="primary" size="small" @click="addBullet(idx)">+ 添加描述</el-button>
        </div>
      </section>
    </div>

    <template #footer>
      <el-button @click="copyPreview">复制全文</el-button>
      <el-button type="primary" :loading="saving" @click="save">保存优化内容</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { showMacToast } from '@/utils/macMessage'

export interface OptimizedExperience {
  period: string
  company: string
  title: string
  current: boolean
  bullets: string[]
}

export interface OptimizedPreview {
  name: string
  phone: string
  email: string
  location: string
  summary: string
  experiences: OptimizedExperience[]
}

const props = defineProps<{
  modelValue: boolean
  data: OptimizedPreview | null
  saving?: boolean
}>()
const emit = defineEmits<{
  'update:modelValue': [boolean]
  save: [preview: OptimizedPreview]
}>()

const visible = ref(false)
const form = ref<OptimizedPreview | null>(null)

watch(
  () => props.modelValue,
  (v) => {
    visible.value = v
    if (v && props.data) {
      form.value = JSON.parse(JSON.stringify(props.data))
    }
  }
)
watch(visible, (v) => emit('update:modelValue', v))

function addExperience() {
  form.value?.experiences.push({
    period: '',
    company: '',
    title: '',
    current: false,
    bullets: [''],
  })
}

function removeExperience(idx: number) {
  form.value?.experiences.splice(idx, 1)
}

function addBullet(expIdx: number) {
  form.value?.experiences[expIdx].bullets.push('')
}

function removeBullet(expIdx: number, bi: number) {
  const bullets = form.value?.experiences[expIdx].bullets
  if (bullets && bullets.length > 1) bullets.splice(bi, 1)
}

function previewToText(p: OptimizedPreview) {
  const lines = [
    p.name,
    `电话: ${p.phone} | 邮箱: ${p.email} | ${p.location}`,
    '',
    '【个人简介】',
    p.summary,
    '',
    '【工作经历】',
  ]
  for (const e of p.experiences) {
    lines.push(`${e.period}  ${e.company}  ${e.title}`)
    for (const b of e.bullets) {
      if (b.trim()) lines.push(`  • ${b}`)
    }
    lines.push('')
  }
  return lines.join('\n')
}

function copyPreview() {
  if (!form.value) return
  navigator.clipboard.writeText(previewToText(form.value)).then(() => showMacToast('已复制'))
}

function save() {
  if (!form.value) return
  emit('save', form.value)
}
</script>

<style scoped lang="scss">
.dlg-header-row {
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

.dlg-title {
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
}
.preview-card {
  background: #fafbfc;
  border: 1px solid #e2e8f0;
  border-radius: 12px;
  padding: 24px 28px;
  max-height: 65vh;
  overflow-y: auto;
}
.preview-header {
  margin-bottom: 20px;
  padding-bottom: 16px;
  border-bottom: 1px solid #e2e8f0;
}
.name-input {
  :deep(.el-input__wrapper) {
    font-size: 22px;
    font-weight: 600;
    box-shadow: none;
    background: transparent;
    padding: 0;
  }
}
.contact-row {
  display: flex;
  align-items: center;
  gap: 8px;
  margin-top: 10px;
  flex-wrap: wrap;
  .sep {
    color: #cbd5e1;
  }
}
.preview-section {
  margin-bottom: 24px;
  h3 {
    font-size: 15px;
    font-weight: 600;
    color: #1e293b;
    margin: 0 0 12px;
    padding-bottom: 8px;
    border-bottom: 1px solid #e2e8f0;
  }
}
.section-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
  h3 {
    margin: 0;
    border: none;
    padding: 0;
  }
}
.exp-block {
  background: #fff;
  border-radius: 8px;
  padding: 14px;
  margin-bottom: 12px;
  border: 1px solid #f1f5f9;
}
.exp-head {
  display: flex;
  align-items: center;
  gap: 8px;
  flex-wrap: wrap;
  margin-bottom: 10px;
}
.bullet-row {
  display: flex;
  align-items: flex-start;
  gap: 8px;
  margin-bottom: 8px;
  .bullet-dot {
    color: #64748b;
    line-height: 32px;
  }
  .el-input {
    flex: 1;
  }
}
</style>

<style lang="scss">
.resume-opt-preview-dialog.el-dialog {
  border-radius: 16px;
}
</style>
