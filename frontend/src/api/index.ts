import axios from 'axios'
import { ElMessage } from 'element-plus'

const api = axios.create({
  baseURL: import.meta.env.VITE_API_BASE_URL || '/api/v1',
  timeout: 30000,
  headers: {
    'Content-Type': 'application/json'
  }
})

// 请求拦截器
api.interceptors.request.use(
  (config) => {
    const token = localStorage.getItem('token')
    if (token) {
      config.headers.Authorization = `Bearer ${token}`
    }
    return config
  },
  (error) => {
    return Promise.reject(error)
  }
)

// 响应拦截器
api.interceptors.response.use(
  (response) => {
    const { code, message, data } = response.data
    // 后端返回 code: 200 表示成功
    if (code !== 200 && code !== 0) {
      ElMessage.error(message || '请求失败')
      return Promise.reject(new Error(message))
    }
    return response.data  // 返回完整响应，包含 data 字段
  },
  (error) => {
    const { response } = error
    if (response?.status === 401) {
      localStorage.removeItem('token')
      window.location.href = '/login'
    } else if (response?.status === 429) {
      ElMessage.error('请求过于频繁，请稍后再试')
    } else if (response?.status === 403) {
      // 权限错误不显示弹窗，静默处理
      console.warn('权限不足:', response?.data?.message)
    } else {
      ElMessage.error(response?.data?.message || '网络错误')
    }
    return Promise.reject(error)
  }
)

export default api
