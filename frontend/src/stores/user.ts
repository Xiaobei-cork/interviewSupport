import { defineStore } from 'pinia'
import { ref } from 'vue'
import { authApi, userApi, messageApi } from '@/api'
import { setFlashNotice } from '@/utils/flashNotice'

export interface UserInfo {
  id: number
  username: string
  account: string
  phone?: string
  email?: string
  avatar_url?: string
  address?: string
}

export const useUserStore = defineStore('user', () => {
  const user = ref<UserInfo | null>(null)
  const showLoginDialog = ref(false)
  const showRegisterDialog = ref(false)
  const unreadCount = ref(0)
  /** 登录/注册成功后递增，供各页面监听并刷新数据 */
  const sessionTick = ref(0)
  /** 全局「编辑个人信息」弹窗 */
  const showProfileEditDialog = ref(false)

  const isLoggedIn = () => !!localStorage.getItem('token') && !!user.value

  async function refreshUnread() {
    if (!localStorage.getItem('token')) return
    try {
      const res = await messageApi.unreadCount() as { count: number }
      unreadCount.value = res.count
    } catch {
      unreadCount.value = 0
    }
  }

  async function fetchUser() {
    const token = localStorage.getItem('token')
    if (!token) {
      user.value = null
      return
    }
    try {
      user.value = await userApi.me() as UserInfo
    } catch {
      logout()
    }
  }

  /** 登录/注册成功后：拉用户信息、消息数，通知页面刷新 */
  async function refreshSession() {
    await fetchUser()
    if (user.value) {
      await refreshUnread()
      sessionTick.value++
    }
    showLoginDialog.value = false
    showRegisterDialog.value = false
  }

  async function login(account: string, password: string) {
    const res = await authApi.login({ account, password }) as { access_token: string }
    localStorage.setItem('token', res.access_token)
    await refreshSession()
    reloadAfterAuth('登录成功')
  }

  async function register(data: object) {
    const res = await authApi.register(data) as { access_token: string }
    localStorage.setItem('token', res.access_token)
    await refreshSession()
    reloadAfterAuth('注册成功，已自动登录')
  }

  /** 登录/注册成功后刷新页面，确保侧边栏用户信息立即展示 */
  function reloadAfterAuth(flashMessage?: string) {
    if (typeof window !== 'undefined' && user.value) {
      if (flashMessage) setFlashNotice(flashMessage, 'success')
      window.location.reload()
    }
  }

  function logout(options?: { reload?: boolean; flashMessage?: string }) {
    localStorage.removeItem('token')
    user.value = null
    unreadCount.value = 0
    sessionTick.value++
    if (options?.reload && typeof window !== 'undefined') {
      if (options.flashMessage) setFlashNotice(options.flashMessage, 'success')
      window.location.reload()
    }
  }

  async function openProfileEdit() {
    if (!localStorage.getItem('token')) {
      showLoginDialog.value = true
      return
    }
    if (!user.value) {
      await fetchUser()
    }
    if (!user.value) {
      showLoginDialog.value = true
      return
    }
    showProfileEditDialog.value = true
  }

  function requireLogin(): boolean {
    if (!isLoggedIn()) {
      showLoginDialog.value = true
      return false
    }
    return true
  }

  return {
    user,
    showLoginDialog,
    showRegisterDialog,
    unreadCount,
    sessionTick,
    showProfileEditDialog,
    openProfileEdit,
    isLoggedIn,
    fetchUser,
    refreshUnread,
    refreshSession,
    login,
    register,
    logout,
    requireLogin,
  }
})
