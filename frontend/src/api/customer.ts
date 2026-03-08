import api from './index'

export interface Customer {
  id: string
  code: string
  name: string
  short_name?: string
  company_type?: string
  industry?: string
  scale?: string
  tax_no?: string
  tax_type?: string
  phone?: string
  email?: string
  fax?: string
  website?: string
  status: string
  service_start_date?: string
  service_end_date?: string
  assigned_accountant_id?: string
  remark?: string
  created_at: string
}

export interface CustomerContact {
  id?: string
  name: string
  title?: string
  department?: string
  phone?: string
  tel?: string
  email?: string
  wechat?: string
  is_primary: boolean
  remark?: string
}

export interface CustomerAddress {
  id?: string
  address_type: string
  province?: string
  city?: string
  district?: string
  detail?: string
  postcode?: string
  is_primary: boolean
}

export interface CustomerInvoiceInfo {
  id?: string
  title: string
  tax_no: string
  address?: string
  phone?: string
  bank_name?: string
  bank_account?: string
  is_default: boolean
}

export const customerApi = {
  // 获取列表
  getList: (params: {
    page?: number
    page_size?: number
    keyword?: string
    status?: string
    industry?: string
    assigned_accountant_id?: string
  }) => api.get('/customers', { params }),

  // 获取详情
  getDetail: (id: string) => api.get(`/customers/${id}`),

  // 创建客户
  create: (data: Partial<Customer>) => api.post('/customers', data),

  // 更新客户
  update: (id: string, data: Partial<Customer>) => api.put(`/customers/${id}`, data),

  // 删除客户
  delete: (id: string) => api.delete(`/customers/${id}`),

  // 添加联系人
  addContact: (customerId: string, data: CustomerContact) => 
    api.post(`/customers/${customerId}/contacts`, data),

  // 删除联系人
  deleteContact: (contactId: string) => 
    api.delete(`/customers/contacts/${contactId}`),

  // 添加地址
  addAddress: (customerId: string, data: CustomerAddress) => 
    api.post(`/customers/${customerId}/addresses`, data),

  // 删除地址
  deleteAddress: (addressId: string) => 
    api.delete(`/customers/addresses/${addressId}`),

  // 添加开票信息
  addInvoiceInfo: (customerId: string, data: CustomerInvoiceInfo) => 
    api.post(`/customers/${customerId}/invoice-infos`, data),

  // 删除开票信息
  deleteInvoiceInfo: (infoId: string) => 
    api.delete(`/customers/invoice-infos/${infoId}`)
}
