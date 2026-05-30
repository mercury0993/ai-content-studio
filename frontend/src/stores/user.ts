import { defineStore } from 'pinia'
import { ref } from 'vue'
import { login as loginApi, getMe } from '@/api/auth'
import router from '@/router'

export interface UserInfo {
  id: string
  username: string
  email: string
  role: 'admin' | 'editor' | 'viewer'
}

export const useUserStore = defineStore('user', () => {
  const token = ref(localStorage.getItem('access_token') || '')
  const userInfo = ref<UserInfo | null>(null)

  async function login(email: string, password: string) {
    const data: any = await loginApi(email, password)
    token.value = data.access_token
    localStorage.setItem('access_token', data.access_token)
    localStorage.setItem('refresh_token', data.refresh_token)
    await fetchUser()
    router.push('/dashboard')
  }

  async function fetchUser() {
    const data: any = await getMe()
    userInfo.value = data
  }

  function logout() {
    token.value = ''
    userInfo.value = null
    localStorage.removeItem('access_token')
    localStorage.removeItem('refresh_token')
    router.push('/login')
  }

  return { token, userInfo, login, fetchUser, logout }
})
