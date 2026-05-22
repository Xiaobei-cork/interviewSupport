<template>
  <el-dialog
    v-model="visible"
    width="640px"
    class="avatar-picker-dialog"
    :show-close="false"
    align-center
    destroy-on-close
    :close-on-click-modal="false"
    @closed="onClosed"
  >
    <template #header>
      <div class="picker-header">
        <span class="picker-title">选择头像</span>
        <button type="button" class="picker-close" aria-label="关闭" @click="visible = false">
          <el-icon><Close /></el-icon>
        </button>
      </div>
    </template>

    <div class="picker-body">
      <div v-if="draftUrl" class="picker-preview-bar">
        <span class="preview-label">预览</span>
        <el-avatar :size="72" :src="draftUrl" />
        <span class="preview-tip">{{ deferSave ? '确认后仅在编辑页展示，点保存才上传' : '点击确认后同步为系统头像' }}</span>
      </div>

      <div class="picker-main">
        <div class="preset-grid">
          <div
            v-for="(url, i) in displayPresets"
            :key="i"
            class="preset-item"
            :class="{ active: draftUrl === url && !pendingFile }"
            @click="selectPreset(url)"
          >
            <el-avatar :size="52" :src="url" />
          </div>
        </div>

        <el-upload
          class="upload-zone"
          :show-file-list="false"
          :auto-upload="false"
          accept=".jpg,.jpeg,.png,image/jpeg,image/png"
          :on-change="onFileChange"
        >
          <div class="upload-inner" :class="{ active: !!pendingFile, 'has-preview': !!draftUrl && pendingFile }">
            <template v-if="draftUrl && pendingFile">
              <el-avatar :size="80" :src="draftUrl" />
              <span class="upload-title">已选择图片</span>
              <span class="upload-sub">{{ deferSave ? '确认后在编辑页预览' : '点击确认后生效' }}</span>
            </template>
            <template v-else>
              <el-icon class="upload-icon" :size="36"><Picture /></el-icon>
              <span class="upload-title">上传头像</span>
              <span class="upload-sub">支持 jpg、jpeg、png，2MB 以内</span>
            </template>
          </div>
        </el-upload>
      </div>
    </div>

    <template #footer>
      <div class="picker-footer">
        <el-button type="primary" :loading="confirming" @click="handleConfirm">确认</el-button>
      </div>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, computed, watch, onMounted, onBeforeUnmount } from 'vue'
import { Close, Picture } from '@element-plus/icons-vue'
import { userApi } from '@/api'
import { useUserStore } from '@/stores/user'
import { showMacAlert, showMacToast } from '@/utils/macMessage'
import type { AvatarPickResult } from './avatarPick'

const props = withDefaults(
  defineProps<{
    modelValue: boolean
    currentUrl?: string
    /** true：只回传选择结果，不上传 OSS；在编辑页点「保存」时再上传 */
    deferSave?: boolean
  }>(),
  { deferSave: false }
)

const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  /** 延迟模式：仅更新编辑页预览 */
  picked: [result: AvatarPickResult]
  /** 立即模式：已上传并写入用户资料 */
  confirmed: [url: string]
}>()

const store = useUserStore()
const presetAvatars = ref<string[]>([])
const draftUrl = ref('')
const pendingFile = ref<File | null>(null)
const blobUrl = ref<string | null>(null)
const confirming = ref(false)

const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

const displayPresets = computed(() => presetAvatars.value.slice(0, 8))

watch(
  () => props.modelValue,
  (open) => {
    if (open) {
      draftUrl.value = props.currentUrl || store.user?.avatar_url || ''
      pendingFile.value = null
      revokeBlob()
    }
  }
)

onMounted(async () => {
  const res = await userApi.presetAvatars() as { avatars: string[] }
  presetAvatars.value = res.avatars
})

onBeforeUnmount(revokeBlob)

function revokeBlob() {
  if (blobUrl.value) {
    URL.revokeObjectURL(blobUrl.value)
    blobUrl.value = null
  }
}

function selectPreset(url: string) {
  pendingFile.value = null
  revokeBlob()
  draftUrl.value = url
}

function onFileChange(f: { raw?: File }) {
  const file = f.raw
  if (!file) return
  if (!['image/jpeg', 'image/png', 'image/jpg'].includes(file.type) && !file.name.match(/\.(jpe?g|png)$/i)) {
    void showMacAlert('仅支持 jpg、jpeg、png 格式', '上传头像', 'warning')
    return
  }
  if (file.size > 2 * 1024 * 1024) {
    void showMacAlert('图片大小不能超过 2MB', '上传头像', 'warning')
    return
  }
  revokeBlob()
  pendingFile.value = file
  blobUrl.value = URL.createObjectURL(file)
  draftUrl.value = blobUrl.value
}

function onClosed() {
  draftUrl.value = ''
  pendingFile.value = null
  revokeBlob()
}

async function handleConfirm() {
  if (!draftUrl.value && !pendingFile.value) {
    void showMacAlert('请先选择或上传头像', '选择头像', 'info')
    return
  }

  if (props.deferSave) {
    if (pendingFile.value && blobUrl.value) {
      emit('picked', { kind: 'file', file: pendingFile.value, previewUrl: blobUrl.value })
      blobUrl.value = null
      pendingFile.value = null
    } else {
      emit('picked', { kind: 'preset', url: draftUrl.value })
    }
    visible.value = false
    return
  }

  confirming.value = true
  try {
    let finalUrl = draftUrl.value
    if (pendingFile.value) {
      const u = await userApi.uploadAvatar(pendingFile.value) as { avatar_url: string }
      finalUrl = u.avatar_url
    } else {
      await userApi.update({ avatar_url: draftUrl.value })
    }
    await store.fetchUser()
    emit('confirmed', finalUrl)
    showMacToast('头像已更新')
    visible.value = false
  } catch {
    /* handled */
  } finally {
    confirming.value = false
  }
}
</script>

<style scoped lang="scss">
.picker-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 4px 0;
}

.picker-title {
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
}

.picker-close {
  border: none;
  background: transparent;
  cursor: pointer;
  color: #94a3b8;
  padding: 4px;
  border-radius: 6px;
  display: flex;
  &:hover {
    background: #f1f5f9;
    color: #64748b;
  }
}

.picker-preview-bar {
  display: flex;
  align-items: center;
  gap: 14px;
  padding: 14px 16px;
  margin-bottom: 16px;
  background: linear-gradient(135deg, #f0f9ff 0%, #f8fafc 100%);
  border-radius: 12px;
  border: 1px solid #e0f2fe;

  .preview-label {
    font-size: 13px;
    font-weight: 600;
    color: #0369a1;
  }
  .preview-tip {
    font-size: 12px;
    color: #64748b;
    margin-left: auto;
    max-width: 220px;
    text-align: right;
    line-height: 1.4;
  }
}

.picker-main {
  display: flex;
  gap: 20px;
  align-items: stretch;
}

.preset-grid {
  flex: 1;
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 12px;
}

.preset-item {
  display: flex;
  justify-content: center;
  padding: 8px;
  border-radius: 12px;
  cursor: pointer;
  border: 2px solid transparent;
  transition: all 0.15s;

  &:hover {
    background: #f8fafc;
  }
  &.active {
    border-color: #3b82f6;
    background: #eff6ff;
  }
}

.upload-zone {
  width: 160px;
  flex-shrink: 0;

  :deep(.el-upload) {
    width: 100%;
    height: 100%;
  }
}

.upload-inner {
  height: 100%;
  min-height: 200px;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 8px;
  padding: 16px 12px;
  border-radius: 12px;
  background: #f8fafc;
  border: 1px dashed #cbd5e1;
  cursor: pointer;
  transition: all 0.15s;
  text-align: center;

  &:hover,
  &.active {
    border-color: #3b82f6;
    background: #eff6ff;
  }

  &.has-preview {
    border-style: solid;
  }

  .upload-icon {
    color: #3b82f6;
  }
  .upload-title {
    font-size: 14px;
    font-weight: 500;
    color: #3b82f6;
  }
  .upload-sub {
    font-size: 11px;
    color: #94a3b8;
    line-height: 1.4;
    padding: 0 4px;
  }
}

.picker-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;

  .el-button--primary {
    background: #3b82f6;
    border-color: #3b82f6;
    border-radius: 8px;
    min-width: 88px;
  }
}
</style>

<style lang="scss">
.avatar-picker-dialog.el-dialog {
  border-radius: 16px;
  overflow: hidden;
  padding: 0;

  .el-dialog__header {
    margin: 0;
    padding: 20px 24px 0;
  }
  .el-dialog__body {
    padding: 16px 24px;
  }
  .el-dialog__footer {
    padding: 8px 24px 20px;
    border-top: 1px solid #f1f5f9;
  }
}
</style>
