<template>
  <el-dialog
    v-model="visible"
    width="680px"
    class="ai-analysis-dialog"
    align-center
    destroy-on-close
    :show-close="false"
  >
    <template #header>
      <div class="analysis-chrome">
        <button type="button" class="dialog-close-red" aria-label="关闭" @click="visible = false" />
        <span class="analysis-title">AI 分析结果</span>
      </div>
    </template>

    <div class="score-hero">
      <div class="score-ring">
        <svg viewBox="0 0 100 100" class="ring-svg">
          <circle cx="50" cy="50" r="42" fill="none" stroke="#e2e8f0" stroke-width="8" />
          <circle
            cx="50"
            cy="50"
            r="42"
            fill="none"
            stroke="url(#scoreGrad)"
            stroke-width="8"
            stroke-linecap="round"
            :stroke-dasharray="ringDash"
            transform="rotate(-90 50 50)"
          />
          <defs>
            <linearGradient id="scoreGrad" x1="0%" y1="0%" x2="100%" y2="0%">
              <stop offset="0%" stop-color="#3b82f6" />
              <stop offset="100%" stop-color="#60a5fa" />
            </linearGradient>
          </defs>
        </svg>
        <div class="score-inner">
          <span class="score-num">{{ scoreDisplay }}</span>
          <span class="score-unit">/ 5</span>
        </div>
      </div>
      <div class="score-meta">
        <p class="meta-label">综合评分</p>
        <el-rate v-model="rateValue" disabled text-color="#f59e0b" />
        <p v-if="overall" class="meta-summary">{{ overall }}</p>
      </div>
    </div>

    <el-tabs v-model="mainTab" class="main-tabs">
      <el-tab-pane label="分析结果" name="result" />
      <el-tab-pane label="优化建议" name="suggest" />
    </el-tabs>

    <div class="tab-body">
      <template v-if="mainTab === 'result'">
        <div v-if="highlights.length" class="insight-card highlight">
          <div class="card-head">
            <el-icon><CircleCheckFilled /></el-icon>
            <span>亮点</span>
          </div>
          <ul>
            <li v-for="(h, i) in highlights" :key="i">{{ h }}</li>
          </ul>
        </div>
        <div v-if="improvements.length" class="insight-card improve">
          <div class="card-head">
            <el-icon><WarningFilled /></el-icon>
            <span>待改进</span>
          </div>
          <ul>
            <li v-for="(h, i) in improvements" :key="i">{{ h }}</li>
          </ul>
        </div>
        <p v-if="!highlights.length && !improvements.length" class="empty-hint">暂无分析条目</p>
      </template>

      <template v-else>
        <div class="sub-tabs">
          <button
            v-for="t in subTabItems"
            :key="t.key"
            type="button"
            :class="['sub-tab', { active: suggestTab === t.key }]"
            @click="suggestTab = t.key"
          >
            {{ t.label }}
          </button>
        </div>
        <div class="suggest-content">
          <template v-if="currentSuggestSections.length">
            <div
              v-for="(sec, i) in currentSuggestSections"
              :key="i"
              class="suggest-block"
            >
              <div class="block-icon" :class="sec.icon">
                <el-icon v-if="sec.icon === 'star'"><StarFilled /></el-icon>
                <el-icon v-else-if="sec.icon === 'warn'"><WarningFilled /></el-icon>
                <el-icon v-else-if="sec.icon === 'target'"><Aim /></el-icon>
                <el-icon v-else><Sunny /></el-icon>
              </div>
              <div class="block-text">
                <h4>{{ sec.title }}</h4>
                <ul v-if="Array.isArray(sec.content)">
                  <li v-for="(line, j) in sec.content" :key="j">{{ line }}</li>
                </ul>
                <p v-else>{{ sec.content }}</p>
              </div>
            </div>
          </template>
          <p v-else-if="currentSuggestPlain" class="plain-suggest">{{ currentSuggestPlain }}</p>
          <p v-else class="empty-hint">暂无优化建议</p>
        </div>
      </template>
    </div>

    <template #footer>
      <div class="analysis-footer">
        <el-button v-if="!adopted" class="btn-ghost" @click="emit('reanalyze')">重新分析</el-button>
        <el-button class="btn-ghost" @click="toggleMainTab">
          {{ mainTab === 'suggest' ? '查看分析结果' : '查看优化建议' }}
        </el-button>
        <el-button type="primary" class="btn-primary" @click="emit('chat')">
          <el-icon><ChatDotRound /></el-icon>
          AI 对话
        </el-button>
        <el-button v-if="showExport" class="btn-ghost" @click="emit('export')">导出简历</el-button>
        <el-button
          v-if="showAdopt"
          type="primary"
          class="btn-primary"
          :disabled="adopted"
          @click="emit('adopt')"
        >
          {{ adopted ? '已采纳' : '采纳 AI 分析' }}
        </el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch, withDefaults } from 'vue'
import {
  StarFilled,
  WarningFilled,
  Aim,
  Sunny,
  CircleCheckFilled,
  ChatDotRound,
} from '@element-plus/icons-vue'

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
    showExport?: boolean
    showAdopt?: boolean
    adopted?: boolean
  }>(),
  { showAdopt: true, adopted: false }
)
const emit = defineEmits<{
  'update:modelValue': [boolean]
  reanalyze: []
  chat: []
  export: []
  adopt: []
}>()

const visible = ref(false)
const mainTab = ref('result')
const suggestTab = ref('comprehensive')
const rateValue = ref(4)

const subTabItems = [
  { key: 'comprehensive', label: '综合建议' },
  { key: 'problems', label: '问题分析' },
  { key: 'highlights_eval', label: '亮点评估' },
  { key: 'plan', label: '提升计划' },
]

watch(() => props.modelValue, (v) => {
  visible.value = v
  if (v) mainTab.value = 'result'
})
watch(visible, (v) => emit('update:modelValue', v))

const score = computed(() => {
  const s = props.data?.score as number | undefined
  return s ?? 4.2
})
const scoreDisplay = computed(() => score.value.toFixed(1))
const ringDash = computed(() => {
  const pct = Math.min(score.value / 5, 1)
  const circumference = 2 * Math.PI * 42
  return `${pct * circumference} ${circumference}`
})

const highlights = computed(() => (props.data?.highlights as string[]) || [])
const improvements = computed(() => (props.data?.improvements as string[]) || [])
const overall = computed(() => (props.data?.overall as string) || '')
const tabData = computed(() => props.data?.tabs as Record<string, string> | undefined)
const suggestSections = computed(
  () => props.data?.suggest_sections as Record<string, SuggestSection[]> | undefined
)

const currentSuggestSections = computed(() => {
  const secs = suggestSections.value?.[suggestTab.value]
  if (!Array.isArray(secs)) return []
  return secs.filter((s) => {
    if (Array.isArray(s.content)) return s.content.length > 0
    return Boolean(String(s.content || '').trim())
  })
})

const currentSuggestPlain = computed(() => tabData.value?.[suggestTab.value]?.trim() || '')

watch(score, (s) => {
  rateValue.value = Math.round(s)
}, { immediate: true })

function toggleMainTab() {
  mainTab.value = mainTab.value === 'suggest' ? 'result' : 'suggest'
}
</script>

<style scoped lang="scss">
.analysis-chrome {
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

.analysis-title {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
}

.score-hero {
  display: flex;
  align-items: center;
  gap: 24px;
  padding: 16px 20px;
  margin-bottom: 8px;
  background: linear-gradient(135deg, #eff6ff 0%, #f8fafc 100%);
  border-radius: 14px;
  border: 1px solid #dbeafe;
}

.score-ring {
  position: relative;
  width: 96px;
  height: 96px;
  flex-shrink: 0;

  .ring-svg {
    width: 100%;
    height: 100%;
  }

  .score-inner {
    position: absolute;
    inset: 0;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
  }

  .score-num {
    font-size: 26px;
    font-weight: 700;
    color: #2563eb;
    line-height: 1;
  }

  .score-unit {
    font-size: 12px;
    color: #64748b;
    margin-top: 2px;
  }
}

.score-meta {
  flex: 1;
  min-width: 0;

  .meta-label {
    font-size: 13px;
    color: #64748b;
    margin: 0 0 6px;
  }

  .meta-summary {
    margin: 10px 0 0;
    font-size: 13px;
    color: #475569;
    line-height: 1.6;
  }
}

.main-tabs {
  :deep(.el-tabs__header) {
    margin-bottom: 0;
  }
  :deep(.el-tabs__item.is-active) {
    color: #2563eb;
    font-weight: 600;
  }
  :deep(.el-tabs__active-bar) {
    background: #3b82f6;
    height: 3px;
    border-radius: 2px;
  }
}

.tab-body {
  min-height: 240px;
  max-height: 320px;
  overflow-y: auto;
  padding: 12px 4px 4px;
}

.insight-card {
  border-radius: 12px;
  padding: 14px 16px;
  margin-bottom: 12px;

  &.highlight {
    background: #f0fdf4;
    border: 1px solid #bbf7d0;
    .card-head {
      color: #16a34a;
    }
  }

  &.improve {
    background: #fffbeb;
    border: 1px solid #fde68a;
    .card-head {
      color: #d97706;
    }
  }

  .card-head {
    display: flex;
    align-items: center;
    gap: 6px;
    font-size: 14px;
    font-weight: 600;
    margin-bottom: 8px;
  }

  ul {
    margin: 0;
    padding-left: 18px;
    li {
      font-size: 14px;
      color: #475569;
      line-height: 1.65;
      margin: 6px 0;
    }
  }
}

.sub-tabs {
  display: flex;
  flex-wrap: wrap;
  gap: 8px;
  margin-bottom: 14px;
  padding: 4px;
  background: #f1f5f9;
  border-radius: 10px;
}

.sub-tab {
  flex: 1;
  min-width: 72px;
  padding: 8px 12px;
  border: none;
  border-radius: 8px;
  font-size: 13px;
  color: #64748b;
  background: transparent;
  cursor: pointer;
  transition: all 0.2s;

  &.active {
    background: #fff;
    color: #2563eb;
    font-weight: 600;
    box-shadow: 0 1px 4px rgba(15, 23, 42, 0.08);
  }

  &:hover:not(.active) {
    color: #334155;
  }
}

.suggest-content {
  padding: 4px 0;
}

.suggest-block {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
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
  font-size: 16px;

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

.block-text {
  flex: 1;
  h4 {
    margin: 0 0 6px;
    font-size: 14px;
    font-weight: 600;
    color: #1e293b;
  }
  p,
  li {
    font-size: 14px;
    color: #475569;
    line-height: 1.65;
  }
  ul {
    margin: 0;
    padding-left: 18px;
  }
}

.plain-suggest {
  font-size: 14px;
  color: #475569;
  line-height: 1.7;
  white-space: pre-wrap;
}

.empty-hint {
  text-align: center;
  color: #94a3b8;
  padding: 40px 0;
  font-size: 14px;
}

.analysis-footer {
  display: flex;
  flex-wrap: wrap;
  justify-content: flex-end;
  gap: 10px;
  width: 100%;

  .btn-ghost {
    border-radius: 8px;
    border-color: #e2e8f0;
    color: #475569;
  }

  .score-sync-hint {
    font-size: 13px;
    color: #64748b;
    align-self: center;
    margin-left: 4px;
  }

  .btn-primary {
    border-radius: 8px;
    background: linear-gradient(135deg, #3b82f6, #2563eb);
    border: none;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.3);
  }
}
</style>

<style lang="scss">
.ai-analysis-dialog.el-dialog {
  border-radius: 16px;
  overflow: hidden;
  padding: 0;
  box-shadow:
    0 22px 70px rgba(0, 0, 0, 0.18),
    0 0 0 1px rgba(0, 0, 0, 0.05);

  .el-dialog__header {
    margin: 0;
    padding: 14px 20px 12px;
    background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
    border-bottom: 1px solid #e2e8f0;
  }

  .el-dialog__body {
    padding: 16px 22px 8px;
  }

  .el-dialog__footer {
    padding: 14px 22px 18px;
    border-top: 1px solid #f1f5f9;
  }
}
</style>
