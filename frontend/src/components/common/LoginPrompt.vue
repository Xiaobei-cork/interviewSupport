<template>
  <el-dialog v-model="visible" width="360px" :show-close="false" align-center>
    <template #header>
      <div class="login-prompt-header">
        <button type="button" class="dialog-close-red" aria-label="关闭" @click="visible = false" />
        <span class="login-prompt-title">请先登录</span>
      </div>
    </template>
    <p class="login-prompt-body">登录后即可使用此功能</p>
    <template #footer>
      <el-button type="primary" @click="goLogin">立即登录</el-button>
    </template>
  </el-dialog>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useUserStore } from '@/stores/user'

const props = defineProps<{ modelValue: boolean }>()
const emit = defineEmits<{ 'update:modelValue': [boolean] }>()
const store = useUserStore()

const visible = computed({
  get: () => props.modelValue,
  set: (v) => emit('update:modelValue', v),
})

function goLogin() {
  visible.value = false
  store.showLoginDialog = true
}
</script>

<style scoped lang="scss">
.login-prompt-header {
  display: flex;
  align-items: center;
  gap: 10px;
}
.login-prompt-title {
  font-size: 16px;
  font-weight: 600;
}
.login-prompt-body {
  text-align: center;
  color: #64748b;
  padding: 12px 0;
  margin: 0;
}
.dialog-close-red {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  border: none;
  background: #ff5f57;
  cursor: pointer;
  padding: 0;
}
</style>
