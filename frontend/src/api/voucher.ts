import api from './index'

export interface Voucher {
  id: string
  voucher_no?: string
  voucher_date?: string
  period?: string
  summary?: string
  status: string
  items: VoucherItem[]
  ai_confidence?: number
  created_at: string
}

export interface VoucherItem {
  id: string
  line_no: number
  subject_code: string
  subject_name: string
  debit_amount: number
  credit_amount: number
  summary?: string
}

export const voucherApi = {
  getList: (params?: { page?: number; page_size?: number; status?: string }) =>
    api.get('/vouchers', { params }),
  
  getDetail: (id: string) => api.get(`/vouchers/${id}`),
  
  generate: (billIds: string[]) =>
    api.post('/vouchers/generate', { bill_ids: billIds }),
  
  audit: (id: string, data: { action: string; note?: string }) =>
    api.post(`/vouchers/${id}/audit`, data)
}
