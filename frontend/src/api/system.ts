import api from './index'

export const systemApi = {
  // 用户管理
  getUsers: (params?: any) => api.get('/sys/users', { params }),
  createUser: (data: any) => api.post('/sys/users', data),
  updateUser: (id: string, data: any) => api.put(`/sys/users/${id}`, data),
  deleteUser: (id: string) => api.delete(`/sys/users/${id}`),
  
  // 角色权限
  getRoles: () => api.get('/sys/roles'),
  
  // 操作日志
  getLogs: (params?: any) => api.get('/sys/logs', { params }),
  
  // 系统配置
  getConfig: () => api.get('/sys/config'),
  updateConfig: (data: any) => api.put('/sys/config', data),

  // 租户管理
  getTenants: (params?: any) => api.get('/sys/tenants', { params }),
  createTenant: (data: any) => api.post('/sys/tenants', data),
  updateTenant: (id: string, data: any) => api.put(`/sys/tenants/${id}`, data),
  deleteTenant: (id: string) => api.delete(`/sys/tenants/${id}`),

  // 备份管理
  getBackupTasks: (params?: any) => api.get('/sys/backup/tasks', { params }),
  createBackupTask: (data: any) => api.post('/sys/backup/tasks', data),
  updateBackupTask: (id: string, data: any) => api.put(`/sys/backup/tasks/${id}`, data),
  deleteBackupTask: (id: string) => api.delete(`/sys/backup/tasks/${id}`),
  getBackupRecords: (params?: any) => api.get('/sys/backup/records', { params }),
  deleteBackupRecord: (id: string) => api.delete(`/sys/backup/records/${id}`),

  // 定时任务
  getScheduledTasks: (params?: any) => api.get('/sys/scheduled-tasks', { params }),
  createScheduledTask: (data: any) => api.post('/sys/scheduled-tasks', data),
  updateScheduledTask: (id: string, data: any) => api.put(`/sys/scheduled-tasks/${id}`, data),
  deleteScheduledTask: (id: string) => api.delete(`/sys/scheduled-tasks/${id}`),
  getTaskHistory: (params?: any) => api.get('/sys/scheduled-tasks/history', { params })
}
