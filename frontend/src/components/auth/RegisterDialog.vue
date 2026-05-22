<template>
  <MacDialog v-model="visible" title="注册" width="440px" :close-on-click-modal="false">
    <el-form :model="form" label-width="88px" @submit.prevent="handleRegister">
      <el-form-item label="账号">
        <el-input v-model="form.account" placeholder="设置唯一账号（注册后不可改）" maxlength="50" />
      </el-form-item>
      <el-form-item label="手机/邮箱">
        <el-input v-model="form.contact" placeholder="手机号或邮箱（至少填一项）" />
      </el-form-item>
      <el-form-item label="密码">
        <el-input v-model="form.password" type="password" show-password placeholder="至少 6 位" />
      </el-form-item>
      <el-form-item label="确认密码">
        <el-input v-model="form.confirm" type="password" show-password />
      </el-form-item>
      <el-form-item>
        <el-checkbox v-model="form.agree">我已阅读并同意服务条款</el-checkbox>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button type="primary" class="mac-btn-primary" :loading="loading" @click="handleRegister">注册</el-button>
    </template>
    <div class="switch-link">
      已有账号？<el-link type="primary" :underline="false" @click="switchLogin">返回登录</el-link>
    </div>
  </MacDialog>
</template>

<script setup lang="ts">
import { reactive, ref, computed } from 'vue'
import { useUserStore } from '@/stores/user'
import MacDialog from '@/components/common/MacDialog.vue'
import { showMacAlert } from '@/utils/macMessage'

const store = useUserStore()
const loading = ref(false)
const form = reactive({ account: '', contact: '', password: '', confirm: '', agree: false })

const visible = computed({
  get: () => store.showRegisterDialog,
  set: (v) => { store.showRegisterDialog = v },
})

async function handleRegister() {
  if (!form.agree) {
    void showMacAlert('请先阅读并同意服务条款', '注册', 'warning')
    return
  }
  if (!form.account.trim()) {
    void showMacAlert('请填写账号', '注册', 'warning')
    return
  }
  if (form.account.trim().length < 3) {
    void showMacAlert('账号至少 3 个字符', '注册', 'warning')
    return
  }
  if (!form.contact.trim()) {
    void showMacAlert('请填写手机号或邮箱', '注册', 'warning')
    return
  }
  if (form.password.length < 6) {
    void showMacAlert('密码至少 6 位', '注册', 'warning')
    return
  }
  if (form.password !== form.confirm) {
    void showMacAlert('两次输入的密码不一致', '注册', 'warning')
    return
  }

  const data: Record<string, string> = {
    account: form.account.trim(),
    password: form.password,
  }
  if (form.contact.includes('@')) data.email = form.contact.trim()
  else data.phone = form.contact.trim()

  loading.value = true
  try {
    await store.register(data)
    form.account = ''
    form.contact = ''
    form.password = ''
    form.confirm = ''
  } catch {
    /* 账号/手机/邮箱已存在等由 request 拦截器弹出 Mac 提示 */
  } finally {
    loading.value = false
  }
}

function switchLogin() {
  store.showRegisterDialog = false
  store.showLoginDialog = true
}
</script>

<style scoped>
.switch-link {
  text-align: center;
  margin-top: 12px;
  font-size: 13px;
  color: #64748b;
}
.mac-btn-secondary,
.mac-btn-primary {
  border-radius: 8px;
}
.mac-btn-primary {
  background: #007aff;
  border-color: #007aff;
}
</style>
