import api from './index'

export const bankAccountApi = {
  // 获取支持的银行列表
  getSupportedBanks: () => api.get('/bank-accounts/banks'),
  
  // 获取银行账户列表
  getList: () => api.get('/bank-accounts'),
  
  // 创建银行账户
  create: (data: {
    bank_code: string
    account_no: string
    account_name?: string
    account_type?: string
  }) => api.post('/bank-accounts', data),
  
  // 同步银行流水
  sync: (accountId: string, params?: { start_date?: string; end_date?: string }) => 
    api.post(`/bank-accounts/${accountId}/sync`, {}, { params }),
  
  // 更新同步配置
  updateConfig: (accountId: string, data: { auto_sync: boolean; sync_range_days: number }) => 
    api.put(`/bank-accounts/${accountId}/sync-config`, data),
  
  // 删除银行账户
  delete: (accountId: string) => api.delete(`/bank-accounts/${accountId}`)
}
