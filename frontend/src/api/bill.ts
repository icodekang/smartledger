import api from './index'

export interface Bill {
  id: string
  bill_type: string
  invoice_code?: string
  invoice_number?: string
  invoice_date?: string
  seller_name?: string
  amount?: number
  tax_amount?: number
  total_amount?: number
  process_status: string
  storage_url?: string
  ocr_confidence?: number
  created_at: string
}

export interface BillListParams {
  page?: number
  page_size?: number
  bill_type?: string
  process_status?: string
  seller_name?: string
}

export const billApi = {
  getList: (params?: BillListParams) => api.get('/invoices', { params }),
  
  getDetail: (id: string) => api.get(`/invoices/${id}`),
  
  create: (data: Partial<Bill>) => api.post('/invoices', data),
  
  update: (id: string, data: Partial<Bill>) => api.put(`/invoices/${id}`, data),
  
  delete: (id: string) => api.delete(`/invoices/${id}`),
  
  upload: (file: File, billType: string = 'invoice') => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/invoices/upload?bill_type=${billType}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  }
}
