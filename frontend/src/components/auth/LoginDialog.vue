<template>
  <MacDialog v-model="visible" title="登录" width="420px">
    <el-form :model="form" label-width="80px" @submit.prevent="handleLogin">
      <el-form-item label="账号">
        <el-input v-model="form.account" placeholder="注册账号" />
      </el-form-item>
      <el-form-item label="密码">
        <el-input v-model="form.password" type="password" show-password placeholder="请输入密码" />
      </el-form-item>
      <el-form-item>
        <el-checkbox v-model="form.remember">记住我</el-checkbox>
        <el-link type="primary" style="float:right" :underline="false">忘记密码？</el-link>
      </el-form-item>
    </el-form>
    <template #footer>
      <el-button type="primary" class="mac-btn-primary" :loading="loading" @click="handleLogin">登录</el-button>
    </template>
    <div class="switch-link">
      还没有账号？<el-link type="primary" @click="switchRegister">立即注册</el-link>
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
const form = reactive({ account: '', password: '', remember: false })

const visible = computed({
  get: () => store.showLoginDialog,
  set: (v) => { store.showLoginDialog = v },
})

async function handleLogin() {
  if (!form.account || !form.password) {
    void showMacAlert('请填写账号和密码', '登录', 'warning')
    return
  }
  loading.value = true
  try {
    await store.login(form.account, form.password)
    form.password = ''
    /* 成功提示在 reload 后由 flashNotice 展示 */
  } catch {
    /* handled */
  } finally {
    loading.value = false
  }
}

function switchRegister() {
  store.showLoginDialog = false
  store.showRegisterDialog = true
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
