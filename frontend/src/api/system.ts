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
  updateConfig: (data: any) => api.put('/sys/config', data)
}
