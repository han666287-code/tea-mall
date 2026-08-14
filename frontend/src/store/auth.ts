import { defineStore } from 'pinia'
import { ref } from 'vue'

import {
  getMe,
  login as loginApi,
  logout as logoutApi,
  refreshToken as refreshTokenApi,
  register as registerApi,
} from '@/api/auth'
import type { RegisterRequest, UserInfo } from '@/types/auth'

export const useAuthStore = defineStore('auth', () => {
  // token 持久化到 localStorage，刷新页面不丢失
  const token = ref<string>(localStorage.getItem('token') || '')
  const refreshToken = ref<string>(localStorage.getItem('refresh_token') || '')
  const user = ref<UserInfo | null>(null)

  async function login(username: string, password: string) {
    const { data } = await loginApi({ username, password })
    token.value = data.token
    refreshToken.value = data.refresh_token
    user.value = data.user
    localStorage.setItem('token', data.token)
    localStorage.setItem('refresh_token', data.refresh_token)
  }

  async function register(data: RegisterRequest) {
    await registerApi(data)
  }

  async function fetchMe() {
    if (!token.value) return
    const { data } = await getMe()
    user.value = data
  }

  function clear() {
    token.value = ''
    refreshToken.value = ''
    user.value = null
    localStorage.removeItem('token')
    localStorage.removeItem('refresh_token')
  }

  async function refreshAccessToken(): Promise<boolean> {
    const rt = refreshToken.value || localStorage.getItem('refresh_token')
    if (!rt) return false
    try {
      const { data } = await refreshTokenApi(rt)
      token.value = data.token
      refreshToken.value = data.refresh_token
      user.value = data.user
      localStorage.setItem('token', data.token)
      localStorage.setItem('refresh_token', data.refresh_token)
      return true
    } catch {
      return false
    }
  }

  function forceLogout() {
    clear()
  }

  async function logout() {
    try {
      await logoutApi(refreshToken.value || localStorage.getItem('refresh_token'))
    } catch {
      // best effort：后端登出失败也继续清理本地登录态
    } finally {
      clear()
    }
  }

  return {
    token,
    refreshToken,
    user,
    login,
    register,
    fetchMe,
    refreshAccessToken,
    logout,
    forceLogout,
  }
})
