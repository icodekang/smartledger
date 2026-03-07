import api from './index'

export interface VoucherItem {
  id?: string
  line_no: number
  subject_code: string
  subject_name: string
  summary: string
  debit_amount: number
  credit_amount: number
}

export interface Voucher {
  id: string
  voucher_no: string
  voucher_date: string
  period: string
  summary: string
  status: 'draft' | 'pending' | 'approved' | 'rejected'
  ai_confidence?: number
  items: VoucherItem[]
  created_at: string
}

export const voucherApi = {
  // 获取列表
  getList: (params: {
    page?: number
    page_size?: number
    status?: string
    period?: string
  }) => api.get('/vouchers', { params }),

  // 获取详情
  getDetail: (id: string) => api.get(`/vouchers/${id}/detail`),

  // 更新凭证
  update: (id: string, data: Partial<Voucher> & { items?: VoucherItem[] }) => 
    api.put(`/vouchers/${id}`, data),

  // 生成凭证
  generate: (billIds: string[]) => api.post('/vouchers/generate', { bill_ids: billIds }),

  // 审核凭证
  audit: (id: string, action: string, note?: string) => 
    api.post(`/vouchers/${id}/audit`, { action, note })
}
