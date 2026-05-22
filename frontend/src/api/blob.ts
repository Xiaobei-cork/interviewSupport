import axios from 'axios'
import { showMacAlert } from '@/utils/macMessage'

/** 带 Token 下载文件流（预览/导出） */
export async function fetchAuthBlob(path: string): Promise<Blob> {
  const token = localStorage.getItem('token')
  const res = await axios.get(path, {
    baseURL: '/api/v1',
    responseType: 'blob',
    headers: token ? { Authorization: `Bearer ${token}` } : {},
  })
  const blob = res.data as Blob
  if (blob.type?.includes('json') || blob.size < 500) {
    try {
      const text = await blob.text()
      const json = JSON.parse(text) as { message?: string }
      if (json.message) {
        void showMacAlert(json.message, '提示', 'warning')
        throw new Error(json.message)
      }
    } catch (e) {
      if (e instanceof Error && e.message !== 'Unexpected token') throw e
    }
  }
  return blob
}
