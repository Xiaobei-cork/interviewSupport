<template>
  <el-dialog
    v-model="visible"
    width="520px"
    class="deep-opt-input-dialog"
    align-center
    destroy-on-close
    :show-close="false"
    :close-on-click-modal="false"
  >
    <template #header>
      <div class="dlg-title-row">
        <button type="button" class="dialog-close-red" aria-label="关闭" @click="visible = false" />
        <div class="dlg-title">
          <el-icon class="title-icon" color="#8b5cf6"><MagicStick /></el-icon>
          <span>深度优化简历</span>
        </div>
      </div>
    </template>
    <p class="desc">请描述你希望如何优化这份简历，AI 将结合当前简历内容生成可编辑的优化预览。</p>
    <div class="examples">
      <span class="label">快捷示例：</span>
      <el-tag
        v-for="ex in examples"
        :key="ex"
        class="ex-tag"
        effect="plain"
        @click="requirement = ex"
      >
        {{ ex }}
      </el-tag>
    </div>
    <el-input
      v-model="requirement"
      type="textarea"
      :rows="5"
      maxlength="2000"
      show-word-limit
      placeholder="例如：突出 Python 后端经验，补充项目量化数据，面向大厂社招岗位…"
    />
    <template #footer>
      <el-button type="primary" :loading="loading" :disabled="!requirement.trim()" @click="submit">
        开始优化
      </el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch } from 'vue'
import { MagicStick } from '@element-plus/icons-vue'

const props = defineProps<{ modelValue: boolean; loading?: boolean }>()
const emit = defineEmits<{
  'update:modelValue': [boolean]
  submit: [requirement: string]
}>()

const visible = ref(false)
const requirement = ref('')

const examples = [
  '突出技术深度与项目成果',
  '面向 Java 后端岗位优化',
  '精简表述并补充量化指标',
]

watch(() => props.modelValue, (v) => {
  visible.value = v
  if (v) requirement.value = ''
})
watch(visible, (v) => emit('update:modelValue', v))

function submit() {
  if (!requirement.value.trim()) return
  emit('submit', requirement.value.trim())
}
</script>

<style scoped lang="scss">
.dlg-title-row {
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
  display: flex;
  align-items: center;
  gap: 8px;
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
}
.title-icon {
  font-size: 22px;
}
.desc {
  font-size: 14px;
  color: #64748b;
  line-height: 1.6;
  margin: 0 0 16px;
}
.examples {
  margin-bottom: 12px;
  .label {
    font-size: 12px;
    color: #94a3b8;
    display: block;
    margin-bottom: 8px;
  }
  .ex-tag {
    margin: 0 8px 8px 0;
    cursor: pointer;
    border-radius: 6px;
    &:hover {
      color: #3b82f6;
      border-color: #3b82f6;
    }
  }
}
</style>

<style lang="scss">
.deep-opt-input-dialog.el-dialog {
  border-radius: 16px;
  .el-dialog__footer .el-button--primary {
    background: #3b82f6;
    border-color: #3b82f6;
  }
}
</style>
