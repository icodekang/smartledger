import api from './index'

export const reportApi = {
  getBalanceSheet: (customerId: string, period: string) => 
    api.get('/reports/balance-sheet', { params: { customer_id: customerId, period } }),
  getIncomeStatement: (customerId: string, period: string) => 
    api.get('/reports/income-statement', { params: { customer_id: customerId, period } }),
  getCashFlow: (customerId: string, period: string) => 
    api.get('/reports/cash-flow', { params: { customer_id: customerId, period } }),
  getSubjectBalance: (customerId: string, period: string) => 
    api.get('/reports/subject-balance', { params: { customer_id: customerId, period } })
}
