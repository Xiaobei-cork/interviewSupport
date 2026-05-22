<template>
  <el-dialog
    v-model="visible"
    width="580px"
    class="ai-chat-dialog"
    align-center
    destroy-on-close
    :show-close="false"
  >
    <template #header>
      <div class="chat-chrome">
        <button type="button" class="dialog-close-red" aria-label="关闭" @click="visible = false" />
        <span class="chat-title">AI 对话</span>
        <span class="chat-badge">DeepSeek V4 Pro</span>
      </div>
    </template>

    <div class="chat-messages" ref="msgRef">
      <div v-for="(m, i) in messages" :key="i" :class="['msg-row', m.role]">
        <div v-if="m.role === 'assistant'" class="avatar ai-avatar">
          <AiRobotIcon />
        </div>
        <div class="bubble-wrap">
          <span v-if="m.role === 'assistant'" class="sender-label">面试教练</span>
          <div class="bubble" v-html="formatMsg(m.content)" />
        </div>
        <div v-if="m.role === 'user'" class="avatar user-avatar">
          <el-icon><User /></el-icon>
        </div>
      </div>
      <div v-if="loading" class="msg-row assistant typing-row">
        <div class="avatar ai-avatar">
          <AiRobotIcon />
        </div>
        <div class="bubble typing">
          <span /><span /><span />
        </div>
      </div>
    </div>

    <div class="chat-input-bar">
      <el-input
        v-model="input"
        type="textarea"
        :autosize="{ minRows: 1, maxRows: 4 }"
        resize="none"
        placeholder="输入您的问题，Enter 发送…"
        @keydown.enter.exact.prevent="send"
      />
      <el-button
        type="primary"
        class="send-btn"
        :icon="Promotion"
        circle
        :loading="loading"
        :disabled="!input.trim()"
        @click="send"
      />
    </div>
  </el-dialog>
</template>

<script setup lang="ts">
import { ref, watch, nextTick } from 'vue'
import { Promotion, User } from '@element-plus/icons-vue'
import AiRobotIcon from './AiRobotIcon.vue'

const props = defineProps<{
  modelValue: boolean
  chatFn: (msg: string) => Promise<{ reply: string }>
  welcome?: string
}>()
const emit = defineEmits<{ 'update:modelValue': [boolean] }>()

const visible = ref(false)
const input = ref('')
const loading = ref(false)
const messages = ref<{ role: string; content: string }[]>([])
const msgRef = ref<HTMLElement>()

watch(() => props.modelValue, (v) => {
  visible.value = v
  if (v && messages.value.length === 0 && props.welcome) {
    messages.value.push({ role: 'assistant', content: props.welcome })
  }
})
watch(visible, (v) => emit('update:modelValue', v))

function formatMsg(text: string) {
  return text.replace(/\n/g, '<br>')
}

function scrollBottom() {
  nextTick(() => {
    msgRef.value?.scrollTo({ top: msgRef.value.scrollHeight, behavior: 'smooth' })
  })
}

async function send() {
  if (!input.value.trim() || loading.value) return
  const q = input.value.trim()
  messages.value.push({ role: 'user', content: q })
  input.value = ''
  loading.value = true
  scrollBottom()
  try {
    const res = await props.chatFn(q)
    messages.value.push({ role: 'assistant', content: res.reply })
  } catch {
    messages.value.push({ role: 'assistant', content: '抱歉，请稍后再试。' })
  } finally {
    loading.value = false
    scrollBottom()
  }
}
</script>

<style scoped lang="scss">
.chat-chrome {
  display: flex;
  align-items: center;
  gap: 10px;
  padding: 2px 0;
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
  box-shadow: inset 0 0 0 1px rgba(0, 0, 0, 0.12);
}

.chat-title {
  font-size: 15px;
  font-weight: 600;
  color: #1e293b;
}

.chat-badge {
  margin-left: auto;
  font-size: 11px;
  color: #3b82f6;
  background: #eff6ff;
  padding: 3px 10px;
  border-radius: 20px;
  font-weight: 500;
}

.chat-messages {
  height: 380px;
  overflow-y: auto;
  padding: 16px;
  background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
  border-radius: 12px;
  margin-bottom: 14px;

  &::-webkit-scrollbar {
    width: 6px;
  }
  &::-webkit-scrollbar-thumb {
    background: #cbd5e1;
    border-radius: 3px;
  }
}

.msg-row {
  display: flex;
  gap: 10px;
  margin-bottom: 18px;
  align-items: flex-end;

  &.user {
    flex-direction: row-reverse;
    .bubble-wrap {
      align-items: flex-end;
    }
    .bubble {
      background: linear-gradient(135deg, #3b82f6, #2563eb);
      color: #fff;
      border: none;
      box-shadow: 0 4px 14px rgba(37, 99, 235, 0.35);
    }
  }

  &.assistant .bubble {
    background: #fff;
    border: 1px solid #e2e8f0;
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.06);
  }
}

.avatar {
  flex-shrink: 0;
  width: 36px;
  height: 36px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
}

.ai-avatar {
  background: #eff6ff;
  padding: 4px;
  :deep(.ai-robot) {
    width: 28px;
    height: 28px;
    filter: none;
    margin: 0;
  }
}

.user-avatar {
  background: linear-gradient(135deg, #6366f1, #8b5cf6);
  color: #fff;
  font-size: 18px;
}

.bubble-wrap {
  display: flex;
  flex-direction: column;
  gap: 4px;
  max-width: 78%;
}

.sender-label {
  font-size: 11px;
  color: #94a3b8;
  padding-left: 4px;
}

.bubble {
  padding: 12px 16px;
  border-radius: 16px;
  font-size: 14px;
  line-height: 1.65;
  word-break: break-word;
}

.user .bubble {
  border-bottom-right-radius: 4px;
}

.assistant .bubble {
  border-bottom-left-radius: 4px;
}

.typing {
  display: flex;
  gap: 5px;
  padding: 14px 18px;
  span {
    width: 7px;
    height: 7px;
    border-radius: 50%;
    background: #94a3b8;
    animation: bounce 1.2s infinite ease-in-out;
    &:nth-child(2) {
      animation-delay: 0.15s;
    }
    &:nth-child(3) {
      animation-delay: 0.3s;
    }
  }
}

@keyframes bounce {
  0%,
  80%,
  100% {
    transform: scale(0.6);
    opacity: 0.5;
  }
  40% {
    transform: scale(1);
    opacity: 1;
  }
}

.chat-input-bar {
  display: flex;
  gap: 10px;
  align-items: flex-end;
  padding: 12px 14px;
  background: #fff;
  border: 1px solid #e2e8f0;
  border-radius: 14px;
  box-shadow: 0 2px 12px rgba(15, 23, 42, 0.06);

  :deep(.el-textarea__inner) {
    border: none;
    box-shadow: none;
    padding: 4px 0;
    font-size: 14px;
    background: transparent;
  }

  .send-btn {
    flex-shrink: 0;
    width: 40px;
    height: 40px;
    background: linear-gradient(135deg, #3b82f6, #2563eb);
    border: none;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.4);
  }
}
</style>

<style lang="scss">
.ai-chat-dialog.el-dialog {
  border-radius: 16px;
  overflow: hidden;
  padding: 0;
  box-shadow:
    0 22px 70px rgba(0, 0, 0, 0.18),
    0 0 0 1px rgba(0, 0, 0, 0.05);

  .el-dialog__header {
    margin: 0;
    padding: 14px 20px 12px;
    background: linear-gradient(180deg, #f8fafc 0%, #f1f5f9 100%);
    border-bottom: 1px solid #e2e8f0;
  }

  .el-dialog__body {
    padding: 16px 20px 20px;
  }

  .el-dialog__footer {
    display: none;
  }
}
</style>
