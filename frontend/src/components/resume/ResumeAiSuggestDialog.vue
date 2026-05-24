<template>
  <el-dialog
    v-model="visible"
    width="680px"
    class="resume-suggest-dialog"
    align-center
    destroy-on-close
    :show-close="false"
  >
    <template #header>
      <div class="suggest-chrome">
        <button type="button" class="dialog-close-red" aria-label="关闭" @click="visible = false" />
        <span class="suggest-title">{{ dialogTitle }}</span>
        <div
          ref="stampRef"
          class="adopted-stamp"
          :class="{ visible: showAdoptedStamp, pop: stampPop }"
        >
          <el-icon><StarFilled /></el-icon>
          <span>已采纳</span>
        </div>
      </div>
    </template>

    <p v-if="viewResult && showAdoptedStamp" class="result-hint">以下为已采纳的 AI 分析结果</p>
    <p v-else-if="viewResult && !showAdoptedStamp" class="result-hint muted">以下为最近一次 AI 分析，采纳后将标记为正式结果</p>

    <div v-if="hasScore" class="score-bar">
      <span class="score-label">AI 评分</span>
      <div class="rate-stars-only">
        <el-rate :model-value="scoreValue" disabled allow-half :show-score="false" />
      </div>
    </div>

    <el-tabs v-model="activeTab" class="suggest-tabs">
      <el-tab-pane label="综合建议" name="comprehensive" />
      <el-tab-pane label="问题分析" name="problems" />
      <el-tab-pane label="亮点评估" name="highlights_eval" />
      <el-tab-pane label="提升计划" name="plan" />
    </el-tabs>

    <div class="suggest-body">
      <template v-if="currentSections.length">
        <div v-for="(sec, i) in currentSections" :key="i" class="suggest-block">
          <div class="block-icon" :class="sec.icon">
            <el-icon v-if="sec.icon === 'star'"><StarFilled /></el-icon>
            <el-icon v-else-if="sec.icon === 'warn'"><WarningFilled /></el-icon>
            <el-icon v-else-if="sec.icon === 'target'"><Aim /></el-icon>
            <el-icon v-else><Sunny /></el-icon>
          </div>
          <div class="block-content">
            <h4>{{ sec.title }}</h4>
            <ul v-if="Array.isArray(sec.content)">
              <li v-for="(line, j) in sec.content" :key="j">{{ line }}</li>
            </ul>
            <p v-else>{{ sec.content }}</p>
          </div>
        </div>
      </template>
      <p v-else-if="plainTabText" class="plain-text">{{ plainTabText }}</p>
      <p v-else class="empty-text">暂无分析内容</p>
    </div>

    <template #footer>
      <div class="suggest-footer">
        <el-button link type="primary" class="deep-link" @click="emit('deepOptimize')">
          需要更进一步？试试深度优化 →
        </el-button>
        <div v-if="!viewResult && !adopted" class="footer-actions">
          <el-button
            ref="adoptBtnRef"
            type="primary"
            class="btn-adopt"
            :disabled="showAdoptedStamp || adopting"
            :loading="adopting && !flying"
            @click="handleAdopt"
          >
            {{ showAdoptedStamp ? '已采纳' : '采纳 AI 分析' }}
          </el-button>
        </div>
        <div v-else-if="viewResult" class="footer-actions">
          <el-button v-if="!showAdoptedStamp" ref="adoptBtnRef" type="primary" class="btn-adopt" @click="handleAdopt">
            采纳 AI 分析
          </el-button>
          <el-button v-else class="btn-adopt" disabled>已采纳</el-button>
        </div>
      </div>
    </template>

    <Teleport to="body">
      <div v-if="flying" class="fly-star-layer" aria-hidden="true">
        <div class="fly-star" :style="flyStyle">
          <el-icon :size="32"><StarFilled /></el-icon>
        </div>
      </div>
    </Teleport>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed, ref, watch } from 'vue'
import { StarFilled, WarningFilled, Aim, Sunny } from '@element-plus/icons-vue'
import { useAdoptFlyAnimation, resolveEl } from '@/composables/useAdoptFlyAnimation'

type SectionIcon = 'star' | 'warn' | 'target' | 'bulb'
interface SuggestSection {
  icon: SectionIcon
  title: string
  content: string | string[]
}

const props = withDefaults(
  defineProps<{
    modelValue: boolean
    data: Record<string, unknown> | null
    adopted?: boolean
    /** 从列表查看已保存的分析结果 */
    viewResult?: boolean
  }>(),
  { adopted: false, viewResult: false }
)
const emit = defineEmits<{
  'update:modelValue': [boolean]
  deepOptimize: []
  adopt: []
}>()

const activeTab = ref('comprehensive')
const adoptBtnRef = ref()
const stampRef = ref<HTMLElement | null>(null)
const adopting = ref(false)
const adoptedLocal = ref(false)
const stampPop = ref(false)
const { flying, flyStyle, playFly } = useAdoptFlyAnimation()

const showAdoptedStamp = computed(() => props.adopted || adoptedLocal.value)

const dialogTitle = computed(() =>
  props.viewResult ? 'AI 分析结果' : 'AI 优化建议'
)

const scoreValue = computed(() => {
  const s = props.data?.score as number | undefined
  if (s != null && s > 0) return Number(s)
  return 0
})
const hasScore = computed(() => scoreValue.value > 0)

const visible = computed({
  get: () => props.modelValue,
  set: (v: boolean) => emit('update:modelValue', v),
})

watch(
  () => props.modelValue,
  (v) => {
    if (v) {
      activeTab.value = 'comprehensive'
      stampPop.value = false
      if (props.viewResult) {
        adoptedLocal.value = !!props.adopted
      } else {
        adoptedLocal.value = false
      }
    }
  },
  { immediate: true }
)
watch(
  () => props.adopted,
  (v) => {
    if (v) adoptedLocal.value = true
  },
  { immediate: true }
)

const suggestSections = computed(() => {
  const raw = props.data?.suggest_sections as Record<string, SuggestSection[]> | undefined
  return raw || null
})

const currentSections = computed(() => {
  const secs = suggestSections.value?.[activeTab.value]
  if (!Array.isArray(secs)) return []
  return secs.filter((s) => {
    if (Array.isArray(s.content)) return s.content.length > 0
    return Boolean(String(s.content || '').trim())
  })
})

const plainTabText = computed(() => {
  const tabs = props.data?.tabs as Record<string, string> | undefined
  const text = tabs?.[activeTab.value]?.trim()
  if (text) return text
  const tab = activeTab.value
  if (tab === 'comprehensive' && props.data?.overall) {
    return String(props.data.overall)
  }
  if (tab === 'problems' && Array.isArray(props.data?.improvements)) {
    return (props.data.improvements as string[]).join('\n')
  }
  if (tab === 'highlights_eval' && Array.isArray(props.data?.highlights)) {
    return (props.data.highlights as string[]).join('\n')
  }
  return ''
})

function handleAdopt() {
  if (showAdoptedStamp.value || adopting.value) return
  adopting.value = true
  const fromEl = resolveEl(adoptBtnRef)
  const toEl = stampRef.value
  playFly(fromEl, toEl, () => {
    adoptedLocal.value = true
    stampPop.value = true
    window.setTimeout(() => {
      stampPop.value = false
    }, 420)
    emit('adopt')
    adopting.value = false
  })
}
</script>

<style scoped lang="scss">
.suggest-chrome {
  display: flex;
  align-items: center;
  gap: 10px;
  flex-wrap: wrap;
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

.suggest-title {
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
  transform: rotate(-8deg) scale(0.6);
  opacity: 0;
  visibility: hidden;
  background: rgba(255, 251, 235, 0.95);
  box-shadow: 0 1px 0 rgba(245, 158, 11, 0.35);
  transition: opacity 0.2s, transform 0.35s cubic-bezier(0.34, 1.56, 0.64, 1), visibility 0.2s;

  &.visible {
    opacity: 1;
    visibility: visible;
    transform: rotate(-8deg) scale(1);
  }

  &.pop {
    transform: rotate(-8deg) scale(1.12);
  }
}

.result-hint {
  margin: 0 0 10px;
  font-size: 13px;
  color: #0369a1;
  font-weight: 500;

  &.muted {
    color: #64748b;
    font-weight: 400;
  }
}

.score-bar {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 12px;
  padding: 10px 14px;
  background: #f8fafc;
  border-radius: 10px;
  border: 1px solid #e2e8f0;

  .score-label {
    font-size: 13px;
    font-weight: 600;
    color: #64748b;
    flex-shrink: 0;
  }
}

.rate-stars-only {
  :deep(.el-rate__text) {
    display: none !important;
  }
}

.suggest-tabs {
  :deep(.el-tabs__item.is-active) {
    color: #3b82f6;
    font-weight: 600;
  }
  :deep(.el-tabs__active-bar) {
    background: #3b82f6;
    height: 3px;
  }
}

.suggest-body {
  min-height: 260px;
  max-height: 400px;
  overflow-y: auto;
  padding: 4px 0;
}

.suggest-block {
  display: flex;
  gap: 14px;
  margin-bottom: 20px;
}

.block-icon {
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;
  color: #fff;
  font-size: 18px;

  &.star {
    background: linear-gradient(135deg, #3b82f6, #60a5fa);
  }
  &.warn {
    background: linear-gradient(135deg, #22c55e, #4ade80);
  }
  &.target {
    background: linear-gradient(135deg, #f59e0b, #fbbf24);
  }
  &.bulb {
    background: linear-gradient(135deg, #6366f1, #818cf8);
  }
}

.block-content {
  flex: 1;
  h4 {
    font-size: 15px;
    font-weight: 600;
    color: #1e293b;
    margin: 0 0 8px;
  }
  p,
  li {
    font-size: 14px;
    color: #475569;
    line-height: 1.6;
  }
  ul {
    margin: 0;
    padding-left: 18px;
  }
}

.plain-text,
.empty-text {
  font-size: 14px;
  color: #475569;
  line-height: 1.7;
  white-space: pre-wrap;
}

.empty-text {
  color: #94a3b8;
  text-align: center;
  padding: 48px 0;
}

.suggest-footer {
  display: flex;
  flex-direction: column;
  align-items: stretch;
  gap: 12px;
  width: 100%;
}

.footer-actions {
  display: flex;
  justify-content: flex-end;
}

.deep-link {
  font-size: 13px;
  align-self: flex-start;
}

.btn-adopt {
  border-radius: 8px;
  min-width: 120px;
  background: linear-gradient(135deg, #3b82f6, #2563eb);
  border: none;
}
</style>

<style lang="scss">
.resume-suggest-dialog.el-dialog {
  border-radius: 16px;
  overflow: hidden;
  padding: 0;

  .el-dialog__header {
    margin: 0;
    padding: 14px 20px 10px;
    background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
    border-bottom: 1px solid #e2e8f0;
  }
  .el-dialog__body {
    padding: 14px 20px 12px;
  }
  .el-dialog__footer {
    padding: 12px 20px 16px;
    border-top: 1px solid #e2e8f0;
  }
}

.fly-star-layer {
  position: fixed;
  inset: 0;
  pointer-events: none;
  z-index: 9999;
}

.fly-star {
  position: fixed;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #f59e0b;
  filter: drop-shadow(0 4px 12px rgba(245, 158, 11, 0.45));
  will-change: left, top, transform, width, height;
}
</style>
