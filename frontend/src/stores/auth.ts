import { defineStore } from 'pinia'
import { ref } from 'vue'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref({})
  
  const login = async (username: string, password: string) => {
    // 模拟登录
    token.value = 'mock-token'
    user.value = { username, role: 'admin' }
    localStorage.setItem('token', token.value)
  }
  
  const logout = () => {
    token.value = ''
    user.value = {}
    localStorage.removeItem('token')
  }
  
  return { token, user, login, logout }
})
