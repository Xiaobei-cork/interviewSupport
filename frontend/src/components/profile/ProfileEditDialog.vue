<template>
  <el-dialog
    v-model="visible"
    width="560px"
    class="profile-edit-dialog"
    :show-close="false"
    align-center
  >
    <template #header>
      <div class="edit-header">
        <span class="edit-title">编辑个人信息</span>
        <button type="button" class="edit-close" @click="visible = false">
          <el-icon><Close /></el-icon>
        </button>
      </div>
    </template>

    <div class="edit-body">
      <div class="avatar-section" @click="avatarPickerVisible = true">
        <el-avatar :size="88" :src="form.avatar_url" class="profile-avatar">
          {{ form.username?.[0] || '?' }}
        </el-avatar>
        <div class="avatar-hint">
          <span class="hint-title">点击头像更换</span>
          <span class="hint-sub">支持预设或本地上传</span>
        </div>
      </div>

      <el-form :model="form" label-position="top" class="profile-form">
        <el-form-item label="用户名">
          <el-input v-model="form.username" placeholder="显示名称，可自由修改" maxlength="50" />
        </el-form-item>
        <el-form-item label="账号">
          <el-input v-model="form.account" disabled />
          <p class="field-tip">注册账号，不可修改</p>
        </el-form-item>
        <el-row :gutter="16">
          <el-col :span="12">
            <el-form-item label="手机号">
              <el-input v-model="form.phone" placeholder="选填" />
            </el-form-item>
          </el-col>
          <el-col :span="12">
            <el-form-item label="邮箱">
              <el-input v-model="form.email" placeholder="选填" />
            </el-form-item>
          </el-col>
        </el-row>
        <el-form-item label="住址">
          <el-input v-model="form.address" placeholder="选填" />
        </el-form-item>
      </el-form>

      <el-collapse class="pwd-collapse">
        <el-collapse-item title="修改密码" name="pwd">
          <el-form :model="pwdForm" label-position="top">
            <el-form-item label="旧密码">
              <el-input v-model="pwdForm.old_password" type="password" show-password />
            </el-form-item>
            <el-row :gutter="12">
              <el-col :span="12">
                <el-form-item label="新密码">
                  <el-input v-model="pwdForm.new_password" type="password" show-password />
                </el-form-item>
              </el-col>
              <el-col :span="12">
                <el-form-item label="确认密码">
                  <el-input v-model="pwdForm.confirm" type="password" show-password />
                </el-form-item>
              </el-col>
            </el-row>
            <el-button type="primary" plain size="small" @click="changePwd">更新密码</el-button>
          </el-form>
        </el-collapse-item>
      </el-collapse>
    </div>

    <template #footer>
      <div class="edit-footer">
        <el-button type="primary" :loading="saving" @click="saveProfile">保存</el-button>
      </div>
    </template>

    <AvatarPickerDialog
      v-model="avatarPickerVisible"
      :current-url="form.avatar_url"
      defer-save
      @picked="onAvatarPicked"
    />
  </el-dialog>
</template>

<script setup lang="ts">
import { reactive, ref, computed, watch, nextTick } from 'vue'
import { Close } from '@element-plus/icons-vue'
import { userApi } from '@/api'
import { useUserStore } from '@/stores/user'
import { showMacAlert, showMacToast } from '@/utils/macMessage'
import AvatarPickerDialog from './AvatarPickerDialog.vue'
import type { AvatarPickResult } from './avatarPick'

const props = defineProps<{ modelValue: boolean }>()
const emit = defineEmits<{
  'update:modelValue': [value: boolean]
  saved: []
}>()

const store = useUserStore()
const saving = ref(false)
const avatarPickerVisible = ref(false)
const savedSuccessfully = ref(false)

/** 打开弹窗时的快照，取消时恢复 */
const formSnapshot = ref<Record<string, string> | null>(null)
/** 待保存的头像：本地上传文件 */
const pendingAvatarFile = ref<File | null>(null)
/** 待保存的头像：预设 URL */
const pendingAvatarPreset = ref<string | null>(null)
/** 本地上传预览 blob，取消时需 revoke */
const avatarPreviewBlob = ref<string | null>(null)

const form = reactive({
  username: '',
  account: '',
  phone: '',
  email: '',
  address: '',
  avatar_url: '',
})
const pwdForm = reactive({ old_password: '', new_password: '', confirm: '' })

const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

async function syncForm() {
  if (!store.user && localStorage.getItem('token')) {
    await store.fetchUser()
  }
  const u = store.user
  if (!u) return
  Object.assign(form, {
    username: u.username,
    account: u.account,
    phone: u.phone || '',
    email: u.email || '',
    address: u.address || '',
    avatar_url: u.avatar_url || '',
  })
}

watch(
  () => props.modelValue,
  async (open) => {
    if (open) {
      savedSuccessfully.value = false
      pendingAvatarFile.value = null
      pendingAvatarPreset.value = null
      revokeAvatarPreviewBlob()
      await syncForm()
      formSnapshot.value = {
        username: form.username,
        account: form.account,
        phone: form.phone,
        email: form.email,
        address: form.address,
        avatar_url: form.avatar_url,
      }
      await nextTick()
    } else if (!savedSuccessfully.value) {
      restoreFormSnapshot()
    }
  }
)

watch(
  () => store.user?.id,
  () => {
    if (visible.value && !pendingAvatarFile.value && !pendingAvatarPreset.value) {
      syncForm()
    }
  }
)

function revokeAvatarPreviewBlob() {
  if (avatarPreviewBlob.value) {
    URL.revokeObjectURL(avatarPreviewBlob.value)
    avatarPreviewBlob.value = null
  }
}

function restoreFormSnapshot() {
  if (!formSnapshot.value) return
  Object.assign(form, formSnapshot.value)
  pendingAvatarFile.value = null
  pendingAvatarPreset.value = null
  revokeAvatarPreviewBlob()
}

function onAvatarPicked(result: AvatarPickResult) {
  pendingAvatarFile.value = null
  pendingAvatarPreset.value = null
  revokeAvatarPreviewBlob()

  if (result.kind === 'file') {
    pendingAvatarFile.value = result.file
    avatarPreviewBlob.value = result.previewUrl
    form.avatar_url = result.previewUrl
  } else {
    pendingAvatarPreset.value = result.url
    form.avatar_url = result.url
  }
}

async function resolveAvatarUrlForSave(): Promise<string | undefined> {
  if (pendingAvatarFile.value) {
    const u = await userApi.uploadAvatar(pendingAvatarFile.value) as { avatar_url: string }
    return u.avatar_url
  }
  if (pendingAvatarPreset.value) {
    return pendingAvatarPreset.value
  }
  return form.avatar_url || formSnapshot.value?.avatar_url || undefined
}

async function saveProfile() {
  if (!form.username?.trim()) {
    void showMacAlert('用户名不能为空', '编辑个人信息', 'warning')
    return
  }
  saving.value = true
  try {
    const avatar_url = await resolveAvatarUrlForSave()
    await userApi.update({
      username: form.username.trim(),
      phone: form.phone || undefined,
      email: form.email || undefined,
      address: form.address || undefined,
      avatar_url,
    })
    pendingAvatarFile.value = null
    pendingAvatarPreset.value = null
    revokeAvatarPreviewBlob()
    await store.fetchUser()
    savedSuccessfully.value = true
    showMacToast('保存成功')
    emit('saved')
    visible.value = false
  } catch {
    /* handled */
  } finally {
    saving.value = false
  }
}

async function changePwd() {
  if (pwdForm.new_password !== pwdForm.confirm) {
    void showMacAlert('两次输入的新密码不一致', '修改密码', 'warning')
    return
  }
  try {
    await userApi.changePassword({
      old_password: pwdForm.old_password,
      new_password: pwdForm.new_password,
    })
    showMacToast('密码修改成功')
    Object.assign(pwdForm, { old_password: '', new_password: '', confirm: '' })
  } catch {
    /* handled */
  }
}
</script>

<style scoped lang="scss">
.edit-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
}
.edit-title {
  font-size: 18px;
  font-weight: 600;
  color: #1e293b;
}
.edit-close {
  border: none;
  background: transparent;
  cursor: pointer;
  color: #94a3b8;
  padding: 4px;
  border-radius: 6px;
  &:hover {
    background: #f1f5f9;
  }
}

.avatar-section {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 20px;
  margin-bottom: 20px;
  background: linear-gradient(135deg, #eff6ff 0%, #f8fafc 100%);
  border-radius: 14px;
  cursor: pointer;
  transition: box-shadow 0.2s;

  &:hover {
    box-shadow: 0 4px 16px rgba(59, 130, 246, 0.12);
  }

  .profile-avatar {
    border: 3px solid #fff;
    box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
  }
  .hint-title {
    display: block;
    font-size: 15px;
    font-weight: 500;
    color: #1e293b;
  }
  .hint-sub {
    font-size: 12px;
    color: #64748b;
    margin-top: 4px;
  }
}

.profile-form {
  :deep(.el-form-item__label) {
    font-weight: 500;
    color: #475569;
    padding-bottom: 4px;
  }
}

.field-tip {
  font-size: 12px;
  color: #94a3b8;
  margin: 4px 0 0;
}

.pwd-collapse {
  margin-top: 8px;
  border: none;

  :deep(.el-collapse-item__header) {
    font-weight: 500;
    color: #475569;
    border: none;
    background: #f8fafc;
    border-radius: 8px;
    padding: 0 12px;
    height: 44px;
  }
  :deep(.el-collapse-item__wrap) {
    border: none;
  }
  :deep(.el-collapse-item__content) {
    padding: 12px 0 0;
  }
}

.edit-footer {
  display: flex;
  justify-content: flex-end;
  gap: 12px;
  .el-button--primary {
    background: #3b82f6;
    border-color: #3b82f6;
    border-radius: 8px;
    min-width: 96px;
  }
}
</style>

<style lang="scss">
.profile-edit-dialog.el-dialog {
  border-radius: 16px;
  padding: 0;
  .el-dialog__header {
    padding: 20px 24px 0;
    margin: 0;
  }
  .el-dialog__body {
    padding: 16px 24px;
  }
  .el-dialog__footer {
    padding: 12px 24px 20px;
    border-top: 1px solid #f1f5f9;
  }
}
</style>
