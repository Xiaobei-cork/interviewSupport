import { showMacAlert, showMacToast } from '@/utils/macMessage'

/** 错误：模态弹窗，需点击确认 */
export function showErrorToast(message: string) {
  return showMacAlert(message, '提示', 'error')
}

/** 成功：顶部轻提示 */
export function showSuccessToast(message: string) {
  showMacToast(message, 'success')
}

/** 一般信息 */
export function showInfoToast(message: string) {
  showMacToast(message, 'info')
}

export function formatApiError(detail: unknown, fallback = '请求失败'): string {
  if (typeof detail === 'string') return detail
  if (Array.isArray(detail)) {
    return detail
      .map((item) => {
        if (typeof item === 'string') return item
        if (item && typeof item === 'object' && 'msg' in item) return String((item as { msg: string }).msg)
        return JSON.stringify(item)
      })
      .join('；')
  }
  return fallback
}
