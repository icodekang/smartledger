import api from './index'

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
  updateSettings: (data: any) => api.put('/notifications/settings', data)
}
