import axios, { type AxiosInstance, type AxiosRequestConfig } from 'axios'
import { useUserStore } from '@/stores/user'
import { showErrorToast, formatApiError } from '@/utils/message'

/** 统一响应：{ code, message, data } */
interface ApiBody<T = unknown> {
  code: number
  message: string
  data: T
}

function unwrapResponse<T>(body: unknown): T {
  if (body && typeof body === 'object' && 'code' in body && 'message' in body) {
    const wrapped = body as ApiBody<T>
    if (wrapped.code >= 400) {
      throw Object.assign(new Error(wrapped.message), { response: { data: wrapped, status: wrapped.code } })
    }
    return wrapped.data as T
  }
  return body as T
}

const instance = axios.create({
  baseURL: '/api/v1',
  timeout: 60000,
})

instance.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

instance.interceptors.response.use(
  (res) => unwrapResponse(res.data),
  (err) => {
    const status = err.response?.status
    const url: string = err.config?.url || ''
    const isAuthRequest = url.includes('/auth/login') || url.includes('/auth/register')
    const raw = err.response?.data
    const msg =
      raw?.message ||
      formatApiError(raw?.detail, err.message || '请求失败')

    if (isAuthRequest) {
      const tip = status === 401 && (msg === '请求失败' || !msg) ? '账号或密码错误' : msg
      void showErrorToast(tip)
      return Promise.reject(err)
    }

    if (status === 401) {
      const store = useUserStore()
      localStorage.removeItem('token')
      store.logout()
      store.showLoginDialog = true
      void showErrorToast(msg || '登录已过期，请重新登录')
    } else {
      void showErrorToast(msg)
    }

    return Promise.reject(err)
  }
)

type ApiClient = {
  get<T = unknown>(url: string, config?: AxiosRequestConfig): Promise<T>
  post<T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T>
  put<T = unknown>(url: string, data?: unknown, config?: AxiosRequestConfig): Promise<T>
  delete<T = unknown>(url: string, config?: AxiosRequestConfig): Promise<T>
}

const request = instance as unknown as ApiClient

export default request
