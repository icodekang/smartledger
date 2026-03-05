import api from './index'

export interface LoginParams {
  username: string
  password: string
}

export interface UserInfo {
  id: string
  username: string
  name: string
  role: string
}

export const authApi = {
  login: (data: LoginParams) => {
    const params = new URLSearchParams()
    params.append('username', data.username)
    params.append('password', data.password)
    return api.post('/auth/login', params, {
      headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    })
  },
  
  getMe: () => api.get('/auth/me'),
  
  register: (data: { username: string; password: string; name: string }) =>
    api.post('/auth/register', data)
}
