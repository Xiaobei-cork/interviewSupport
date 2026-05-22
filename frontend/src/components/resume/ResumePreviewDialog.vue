<template>
  <el-dialog v-model="visible" :title="fileName || '简历预览'" width="80%" class="resume-preview-dialog" align-center destroy-on-close @closed="onClosed">
    <div v-loading="loading" class="preview-wrap">
      <iframe v-if="previewUrl && isPdf" :src="previewUrl" class="preview-frame" />
      <div v-else-if="!loading && !previewUrl" class="preview-empty">
        <p>暂不支持在线预览该格式</p>
        <el-button type="primary" @click="emit('download')">下载查看</el-button>
      </div>
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, onBeforeUnmount } from 'vue'

const props = defineProps<{
  modelValue: boolean
  blob: Blob | null
  fileName?: string
  fileType?: string
}>()
const emit = defineEmits<{
  'update:modelValue': [boolean]
  download: []
}>()

const visible = ref(false)
const loading = ref(false)
const previewUrl = ref<string | null>(null)
const isPdf = ref(true)

watch(() => props.modelValue, (v) => {
  visible.value = v
  if (v && props.blob) mountPreview(props.blob)
})

watch(visible, (v) => emit('update:modelValue', v))

function mountPreview(blob: Blob) {
  revokeUrl()
  loading.value = true
  isPdf.value = blob.type.includes('pdf') || props.fileType === 'pdf'
  if (isPdf.value) {
    previewUrl.value = URL.createObjectURL(blob)
  } else {
    previewUrl.value = null
  }
  loading.value = false
}

function revokeUrl() {
  if (previewUrl.value) {
    URL.revokeObjectURL(previewUrl.value)
    previewUrl.value = null
  }
}

function onClosed() {
  revokeUrl()
}

onBeforeUnmount(revokeUrl)
</script>

<style scoped lang="scss">
.preview-wrap {
  min-height: 60vh;
}
.preview-frame {
  width: 100%;
  height: 70vh;
  border: 1px solid #e2e8f0;
  border-radius: 8px;
}
.preview-empty {
  text-align: center;
  padding: 80px 0;
  color: #64748b;
  p {
    margin-bottom: 16px;
  }
}
</style>
