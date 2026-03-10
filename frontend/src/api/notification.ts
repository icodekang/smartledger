import api from './index'

// 类型定义
export interface Notification {
  id: string
  title: string
  content: string
  type: string
  is_read: boolean
  created_at: string
}

export interface NotificationSettings {
  email_enabled: boolean
  push_enabled: boolean
  types: string[]
}

export const notificationApi = {
  // 获取通知列表
  getNotifications: (params?: any) => api.get('/notifications', { params }),

  // 标记单条已读
  markRead: (id: string) => api.post(`/notifications/${id}/read`),

  // 全部标记已读
  markAllRead: () => api.post('/notifications/mark-all-read'),

  // 删除通知
  deleteNotification: (id: string) => api.delete(`/notifications/${id}`),

  // 获取通知设置
  getSettings: () => api.get('/notifications/settings'),

  // 更新通知设置
  updateSettings: (data: NotificationSettings) => api.put('/notifications/settings', data)
}
