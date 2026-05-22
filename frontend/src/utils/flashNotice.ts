import { showMacAlert, showMacToast } from './macMessage'

const FLASH_KEY = 'app_flash_notice'

export type FlashType = 'success' | 'error' | 'info'

/** 页面刷新后仍能展示（登录/退出等会 reload） */
export function setFlashNotice(message: string, type: FlashType = 'success') {
  sessionStorage.setItem(FLASH_KEY, JSON.stringify({ message, type }))
}

export function consumeFlashNotice() {
  const raw = sessionStorage.getItem(FLASH_KEY)
  if (!raw) return
  sessionStorage.removeItem(FLASH_KEY)
  try {
    const { message, type } = JSON.parse(raw) as { message: string; type: FlashType }
    if (!message) return
    if (type === 'success') showMacToast(message, 'success')
    else if (type === 'error') showMacAlert(message, '提示', 'error')
    else showMacToast(message, 'info')
  } catch {
    /* ignore */
  }
}
