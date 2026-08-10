import { defineStore } from 'pinia'
import { ref } from 'vue'

import { getMe, login as loginApi, register as registerApi } from '@/api/auth'
import type { RegisterRequest, UserInfo } from '@/types/auth'

export const useAuthStore = defineStore('auth', () => {
  // token 持久化到 localStorage，刷新页面不丢失
  const token = ref<string>(localStorage.getItem('token') || '')
  const user = ref<UserInfo | null>(null)

  async function login(username: string, password: string) {
    const { data } = await loginApi({ username, password })
    token.value = data.token
    user.value = data.user
    localStorage.setItem('token', data.token)
  }

  async function register(data: RegisterRequest) {
    await registerApi(data)
  }

  async function fetchMe() {
    if (!token.value) return
    const { data } = await getMe()
    user.value = data
  }

  function logout() {
    token.value = ''
    user.value = null
    localStorage.removeItem('token')
  }

  return { token, user, login, register, fetchMe, logout }
})
