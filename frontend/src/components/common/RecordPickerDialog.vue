<template>
  <el-dialog
    v-model="visible"
    width="520px"
    class="record-picker-dialog"
    align-center
    destroy-on-close
    :show-close="false"
  >
    <template #header>
      <div class="picker-header-row">
        <button type="button" class="dialog-close-red" aria-label="关闭" @click="visible = false" />
        <span class="picker-title">{{ title }}</span>
      </div>
    </template>
    <p class="picker-hint">{{ hint }}</p>
    <div v-if="items.length" class="record-list">
      <div
        v-for="item in items"
        :key="item.id"
        class="record-item"
        :class="{ active: selectedId === item.id }"
        @click="selectedId = item.id"
      >
        <div class="record-main">
          <span class="record-title">{{ item.title }}</span>
          <span v-if="item.subtitle" class="record-sub">{{ item.subtitle }}</span>
        </div>
        <span v-if="item.meta" class="record-meta">{{ item.meta }}</span>
        <el-icon v-if="selectedId === item.id" class="check-icon" color="#3b82f6"><CircleCheckFilled /></el-icon>
      </div>
    </div>
    <el-empty v-else :description="emptyText" />
    <template #footer>
      <el-button type="primary" :disabled="!selectedId" @click="confirm">开始 AI 分析</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { CircleCheckFilled } from '@element-plus/icons-vue'

export interface PickerRecord {
  id: number
  title: string
  subtitle?: string
  meta?: string
}

const props = withDefaults(
  defineProps<{
    modelValue: boolean
    items: PickerRecord[]
    title?: string
    hint?: string
    emptyText?: string
  }>(),
  {
    title: '选择记录',
    hint: '请选择一条记录后再开始 AI 分析',
    emptyText: '暂无记录',
  }
)

const emit = defineEmits<{
  'update:modelValue': [boolean]
  confirm: [item: PickerRecord]
}>()

const visible = ref(false)
const selectedId = ref<number | null>(null)

watch(() => props.modelValue, (v) => {
  visible.value = v
  if (v) {
    selectedId.value = props.items[0]?.id ?? null
  }
})
watch(visible, (v) => emit('update:modelValue', v))

function confirm() {
  const item = props.items.find((i) => i.id === selectedId.value)
  if (!item) return
  emit('confirm', item)
  visible.value = false
}
</script>

<style scoped lang="scss">
.picker-header-row {
  display: flex;
  align-items: center;
  gap: 10px;
}

.picker-title {
  font-size: 16px;
  font-weight: 600;
  color: #1e293b;
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

.picker-hint {
  font-size: 13px;
  color: #64748b;
  margin: 0 0 16px;
}
.record-list {
  max-height: 360px;
  overflow-y: auto;
  display: flex;
  flex-direction: column;
  gap: 8px;
}
.record-item {
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 14px 16px;
  border: 1px solid #e2e8f0;
  border-radius: 10px;
  cursor: pointer;
  transition: all 0.15s;

  &:hover {
    border-color: #93c5fd;
    background: #f8fafc;
  }
  &.active {
    border-color: #3b82f6;
    background: #eff6ff;
  }
}
.record-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 4px;
}
.record-title {
  font-size: 14px;
  font-weight: 500;
  color: #1e293b;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
.record-sub {
  font-size: 12px;
  color: #94a3b8;
}
.record-meta {
  font-size: 12px;
  color: #64748b;
  flex-shrink: 0;
}
.check-icon {
  flex-shrink: 0;
  font-size: 20px;
}
</style>

<style lang="scss">
.record-picker-dialog.el-dialog {
  border-radius: 14px;
}
</style>
