import { defineStore } from 'pinia'
import { ref, computed } from 'vue'
import { authApi, type UserInfo } from '../api/auth'

export const useAuthStore = defineStore('auth', () => {
  const token = ref(localStorage.getItem('token') || '')
  const user = ref<UserInfo | null>(null)
  const isLoggedIn = computed(() => !!token.value)
  
  const login = async (accessToken: string, userInfo: UserInfo) => {
    token.value = accessToken
    user.value = userInfo
    localStorage.setItem('token', accessToken)
  }
  
  const fetchUserInfo = async () => {
    if (!token.value) return
    try {
      const res = await authApi.getMe()
      user.value = res.data
      return res.data
    } catch (error) {
      logout()
      throw error
    }
  }
  
  const logout = () => {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
  }
  
  return { 
    token, 
    user, 
    isLoggedIn,
    login, 
    logout,
    fetchUserInfo
  }
})
