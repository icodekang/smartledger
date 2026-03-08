import api from './index'

export const contractApi = {
  getList: (customerId: string) => api.get(`/contracts/customer/${customerId}`),
  create: (customerId: string, data: any) => api.post(`/contracts/customer/${customerId}`, data),
  delete: (id: string) => api.delete(`/contracts/${id}`),
  getPayments: (contractId: string) => api.get(`/contracts/${contractId}/payments`),
  recordPayment: (paymentId: string, data: any) => 
    api.post(`/contracts/payments/${paymentId}/pay`, data),
  recordInvoice: (paymentId: string, data: any) => 
    api.post(`/contracts/payments/${paymentId}/invoice`, data)
}
