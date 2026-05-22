<template>
  <el-dialog
    v-model="visible"
    width="520px"
    class="ai-progress-dialog"
    :close-on-click-modal="false"
    :show-close="false"
    align-center
    @close="stopPoll"
  >
    <template #header>
      <span class="dialog-title">AI 正在分析中...</span>
    </template>
    <div class="ai-progress">
      <AiRobotIcon />
      <p class="tip">别着急，AI 正在为您分析中，请稍候...</p>
      <div class="progress-row">
        <el-progress
          :percentage="progress"
          :stroke-width="14"
          :show-text="false"
          color="#3b82f6"
        />
        <span class="pct">{{ progress }}%</span>
      </div>
      <div class="checklist-title">分析进度</div>
      <ul class="checklist">
        <li v-for="(item, i) in stageList" :key="i" :class="{ done: progress >= item.threshold, active: activeIndex === i }">
          <span class="step-icon">
            <el-icon v-if="progress >= item.threshold" color="#fff"><CircleCheck /></el-icon>
            <span v-else class="dot" />
          </span>
          <span class="step-label">{{ item.label }}</span>
        </li>
      </ul>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, computed, onUnmounted } from 'vue'
import { CircleCheck } from '@element-plus/icons-vue'
import AiRobotIcon from './AiRobotIcon.vue'

const props = withDefaults(
  defineProps<{
    modelValue: boolean
    pollFn: (taskId: string) => Promise<{ progress?: number; status?: string; result?: unknown }>
    taskId: string
    /** interview | resume — 分析步骤文案 */
    variant?: 'interview' | 'resume'
  }>(),
  { variant: 'interview' }
)
const emit = defineEmits<{ 'update:modelValue': [boolean]; done: [unknown] }>()

const visible = ref(false)
const progress = ref(0)
let timer: ReturnType<typeof setInterval> | null = null

const interviewStages = [
  { label: '正在解析面试内容...', threshold: 20 },
  { label: '正在提取关键信息...', threshold: 45 },
  { label: '正在生成分析报告...', threshold: 70 },
  { label: '正在生成优化建议...', threshold: 90 },
]

const resumeStages = [
  { label: '正在解析简历内容...', threshold: 20 },
  { label: '正在提取关键信息...', threshold: 45 },
  { label: '正在生成分析报告...', threshold: 70 },
  { label: '正在生成优化建议...', threshold: 90 },
]

const stageList = computed(() => (props.variant === 'resume' ? resumeStages : interviewStages))

const activeIndex = computed(() => {
  const idx = stageList.value.findIndex((s) => progress.value < s.threshold)
  return idx === -1 ? stageList.value.length - 1 : idx
})

watch(() => props.modelValue, (v) => {
  visible.value = v
  if (v && props.taskId) startPoll()
  else stopPoll()
})

watch(visible, (v) => emit('update:modelValue', v))

function startPoll() {
  progress.value = 8
  timer = setInterval(async () => {
    try {
      const task = await props.pollFn(props.taskId)
      progress.value = Math.max(progress.value, task.progress || 0)
      if (task.status === 'done') {
        progress.value = 100
        stopPoll()
        setTimeout(() => {
          visible.value = false
          emit('done', task.result)
        }, 600)
      } else if (task.status === 'error') {
        stopPoll()
        visible.value = false
      }
    } catch {
      /* retry */
    }
  }, 800)
}

function stopPoll() {
  if (timer) {
    clearInterval(timer)
    timer = null
  }
}

onUnmounted(stopPoll)
</script>

<style scoped lang="scss">
.dialog-title {
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
}

.ai-progress {
  text-align: center;
  padding: 8px 12px 16px;
}

.tip {
  color: #64748b;
  font-size: 14px;
  margin: 16px 0 20px;
}

.progress-row {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 24px;

  .el-progress {
    flex: 1;
  }
  .pct {
    font-size: 14px;
    font-weight: 600;
    color: #3b82f6;
    min-width: 40px;
  }
}

.checklist-title {
  text-align: left;
  font-size: 14px;
  font-weight: 600;
  color: #1e293b;
  margin-bottom: 12px;
}

.checklist {
  list-style: none;
  text-align: left;
  margin: 0;
  padding: 0;

  li {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 0;
    color: #94a3b8;
    font-size: 14px;

    &.done,
    &.active {
      color: #1e293b;
    }
  }
}

.step-icon {
  width: 22px;
  height: 22px;
  border-radius: 50%;
  border: 2px solid #cbd5e1;
  display: flex;
  align-items: center;
  justify-content: center;
  flex-shrink: 0;

  .dot {
    width: 8px;
    height: 8px;
    border-radius: 50%;
    background: #cbd5e1;
  }
}

li.done .step-icon,
li.active .step-icon {
  background: #3b82f6;
  border-color: #3b82f6;
}

li.active:not(.done) .step-icon .dot {
  background: #3b82f6;
}

.step-label {
  flex: 1;
}
</style>

<style lang="scss">
.ai-progress-dialog.el-dialog {
  border-radius: 16px;
  .el-dialog__header {
    padding: 20px 24px 8px;
    margin: 0;
  }
  .el-dialog__body {
    padding: 0 24px 24px;
  }
}
</style>
