import api from './index'

export interface BankFlow {
  id: string
  transaction_date: string
  transaction_time?: string
  amount: number
  balance?: number
  counterparty_name?: string
  counterparty_account?: string
  summary?: string
  transaction_type?: string
  match_status: 'unmatched' | 'matched' | 'ignored'
  matched_bill_id?: string
  created_at: string
}

export interface BankFlowListResponse {
  items: BankFlow[]
  total: number
  summary: {
    total_income: number
    total_expense: number
    unmatched_count: number
  }
  page: number
  page_size: number
}

export interface UploadPreviewResponse {
  preview: {
    index: number
    row_number: number
    transaction_date: string
    amount: number
    balance?: number
    counterparty_name: string
    summary: string
    is_duplicate: boolean
    raw_data: any
  }[]
  total_count: number
  valid_count: number
  error_count: number
  errors: { row: number; error: string }[]
  date_range: { start: string; end: string }
  amount_summary: { income: number; expense: number }
  detected_bank_type: string
}

export interface ImportRequest {
  preview_data: any[]
  selected_indices?: number[]
}

export interface ImportResponse {
  imported_count: number
  skipped_count: number
  import_id: string
}

export const bankFlowApi = {
  // 获取列表
  getList: (params: {
    page?: number
    page_size?: number
    start_date?: string
    end_date?: string
    match_status?: string
    keyword?: string
  }) => api.get('/bank-flows', { params }),

  // 上传预览
  upload: (file: File, bankType: string = 'auto') => {
    const formData = new FormData()
    formData.append('file', file)
    return api.post(`/bank-flows/upload?bank_type=${bankType}`, formData, {
      headers: { 'Content-Type': 'multipart/form-data' }
    })
  },

  // 确认导入
  import: (data: ImportRequest) => api.post('/bank-flows/import', data),

  // 删除
  delete: (id: string) => api.delete(`/bank-flows/${id}`),

  // 批量删除
  batchDelete: (ids: string[]) => api.post('/bank-flows/batch-delete', { ids })
}
