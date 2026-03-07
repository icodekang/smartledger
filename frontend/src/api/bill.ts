import api from './index'

export interface BillItem {
  id?: string
  name: string
  spec?: string
  unit?: string
  quantity?: number
  unit_price?: number
  amount?: number
  tax_rate?: string
  tax_amount?: number
}

export interface BillDetail {
  id: string
  invoice_code?: string
  invoice_number?: string
  invoice_date?: string
  invoice_type?: string
  amount?: number
  tax_amount?: number
  total_amount?: number
  seller_name?: string
  seller_tax_no?: string
  seller_address?: string
  seller_bank?: string
  buyer_name?: string
  buyer_tax_no?: string
  buyer_address?: string
  buyer_bank?: string
  items: BillItem[]
  image_url?: string
  ocr_result?: any
  process_status: string
  created_at: string
}

export const billApi = {
  // 获取列表
  getList: (params: {
    page?: number
    page_size?: number
    bill_type?: string
    process_status?: string
    seller_name?: string
  }) => api.get('/invoices', { params }),

  // 获取详情
  getDetail: (id: string) => api.get(`/invoices/${id}/detail`),

  // 更新票据
  update: (id: string, data: Partial<BillDetail>) => api.put(`/invoices/${id}`, data),

  // 更新明细项
  updateItems: (id: string, items: BillItem[]) => api.put(`/invoices/${id}/items`, { items }),

  // 删除票据
  delete: (id: string) => api.delete(`/invoices/${id}`),

  // 上传票据
  upload: (file: File) => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post('/invoices/upload', formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  }
}
