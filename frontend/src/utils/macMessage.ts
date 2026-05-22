import { ElMessage, ElMessageBox } from 'element-plus'

const MAC_ALERT_CLASS = 'mac-alert-box'
const MAC_TOAST_CLASS = 'mac-toast'

/** macOS 风格模态提示（需用户点击确认） */
export function showMacAlert(
  message: string,
  title = '提示',
  type: 'info' | 'warning' | 'error' = 'warning'
) {
  const icon =
    type === 'error' ? '⚠️' : type === 'info' ? 'ℹ️' : '⚠️'
  return ElMessageBox.alert(
    `<div class="mac-alert__content"><span class="mac-alert__icon">${icon}</span><p>${escapeHtml(message)}</p></div>`,
    title,
    {
      customClass: MAC_ALERT_CLASS,
      confirmButtonText: '好',
      showClose: true,
      closeOnClickModal: false,
      dangerouslyUseHTMLString: true,
      center: false,
      autofocus: true,
      appendTo: document.body,
    }
  )
}

/** 顶部轻提示（成功、一般信息） */
export function showMacToast(message: string, type: 'success' | 'error' | 'info' = 'success') {
  const map = {
    success: ElMessage.success,
    error: ElMessage.error,
    info: ElMessage.info,
  } as const
  map[type]({
    message,
    customClass: MAC_TOAST_CLASS,
    duration: 2800,
    showClose: true,
    grouping: true,
  })
}

function escapeHtml(text: string) {
  return text
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}
