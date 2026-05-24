import request from './request'

export const authApi = {
  register: (data: object) => request.post('/auth/register', data),
  login: (data: object) => request.post('/auth/login', data),
}

export const userApi = {
  me: () => request.get('/users/me'),
  update: (data: object) => request.put('/users/me', data),
  changePassword: (data: object) => request.put('/users/me/password', data),
  uploadAvatar: (file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return request.post('/users/me/avatar', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
  },
  presetAvatars: () => request.get('/users/avatars/presets'),
}

export const interviewApi = {
  list: (params: object) => request.get('/interviews', { params }),
  get: (id: number) => request.get(`/interviews/${id}`),
  create: (data: object) => request.post('/interviews', data),
  update: (id: number, data: object) => request.put(`/interviews/${id}`, data),
  remove: (id: number) => request.delete(`/interviews/${id}`),
  uploadAudio: (id: number, file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return request.post(`/interviews/${id}/audio`, fd, { headers: { 'Content-Type': 'multipart/form-data' } })
  },
  analyze: (id: number) => request.post(`/interviews/${id}/ai/analyze`),
  pollTask: (taskId: string) =>
    request.get<{ progress?: number; status?: string; result?: unknown }>(`/interviews/ai/tasks/${taskId}`),
  score: (id: number, score: number) => request.put(`/interviews/${id}/score`, { score }),
  adoptAi: (id: number, score?: number) =>
    request.post(`/interviews/${id}/ai/adopt`, score != null ? { score } : {}),
  chat: (id: number, message: string) => request.post(`/interviews/${id}/ai/chat`, { message }),
}

export const resumeApi = {
  list: (params: object) => request.get('/resumes', { params }),
  get: (id: number) => request.get<Record<string, unknown>>(`/resumes/${id}`),
  upload: (file: File) => {
    const fd = new FormData()
    fd.append('file', file)
    return request.post('/resumes', fd, { headers: { 'Content-Type': 'multipart/form-data' } })
  },
  remove: (id: number) => request.delete(`/resumes/${id}`),
  analyze: (id: number) => request.post(`/resumes/${id}/ai/analyze`),
  adoptAi: (id: number, score?: number) =>
    request.post(`/resumes/${id}/ai/adopt`, score != null ? { score } : {}),
  pollTask: (taskId: string) =>
    request.get<{ progress?: number; status?: string; result?: unknown }>(`/resumes/ai/tasks/${taskId}`),
  chat: (id: number, message: string) => request.post(`/resumes/${id}/ai/chat`, { message }),
  deepOptimize: (id: number, requirement: string) =>
    request.post(`/resumes/${id}/ai/deep-optimize`, { requirement }),
  saveOptimizedPreview: (id: number, preview: object) =>
    request.put(`/resumes/${id}/optimized-preview`, { preview }),
  previewBlob: (id: number) => import('./blob').then((m) => m.fetchAuthBlob(`/resumes/${id}/preview`)),
  exportBlob: (id: number, format: string) =>
    import('./blob').then((m) => m.fetchAuthBlob(`/resumes/${id}/export?format=${format}`)),
}

export const shareApi = {
  feed: (params: object) => request.get('/share/feed', { params }),
  detail: (id: number) => request.get(`/share/${id}`),
  like: (id: number) => request.post(`/share/${id}/like`),
  favorite: (id: number) => request.post(`/share/${id}/favorite`),
  comments: (id: number, limit?: number) => request.get(`/share/${id}/comments`, { params: { limit } }),
  addComment: (id: number, data: object) => request.post(`/share/${id}/comments`, data),
}

export const messageApi = {
  list: (params: object) => request.get('/messages', { params }),
  unreadCount: () => request.get('/messages/unread-count'),
  markRead: (id: number) => request.put(`/messages/${id}/read`),
}

export const profileApi = {
  get: (userId: number) => request.get(`/profile/${userId}`),
}
