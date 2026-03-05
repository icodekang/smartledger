import api from './index'

export interface AuditTask {
  voucher_id: string
  voucher_no?: string
  voucher_date?: string
  summary?: string
  total_amount: number
  status: string
  submitter: string
  created_at: string
}

export interface AuditStats {
  pending_count: number
  assigned_count: number
  my_assigned: number
}

export const auditApi = {
  getPendingTasks: (params?: { page?: number; page_size?: number; status?: string }) =>
    api.get('/audit/pending', { params }),
  
  batchAudit: (voucherIds: string[], action: 'approve' | 'reject', note?: string) =>
    api.post('/audit/batch-audit', { voucher_ids: voucherIds, action, note }),
  
  autoAssign: () => api.post('/audit/auto-assign'),
  
  getStatistics: () => api.get('/audit/statistics')
}
