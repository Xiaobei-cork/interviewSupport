<template>
  <el-dialog
    v-model="visible"
    :width="width"
    :show-close="false"
    :close-on-click-modal="closeOnClickModal"
    class="mac-dialog"
    align-center
    destroy-on-close
    @closed="$emit('closed')"
  >
    <template #header>
      <div class="mac-dialog__chrome">
        <button type="button" class="light red" aria-label="关闭" @click="visible = false" />
        <span class="mac-dialog__title">{{ title }}</span>
      </div>
    </template>
    <div class="mac-dialog__body">
      <slot />
    </div>
    <template v-if="$slots.footer" #footer>
      <div class="mac-dialog__footer">
        <slot name="footer" />
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue'

const props = withDefaults(
  defineProps<{
    modelValue: boolean
    title?: string
    width?: string | number
    closeOnClickModal?: boolean
  }>(),
  {
    title: '',
    width: '420px',
    closeOnClickModal: true,
  }
)

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  closed: []
}>()

const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})
</script>
