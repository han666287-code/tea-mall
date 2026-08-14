import axios from 'axios'
import http from './http'
import type {
  ChangePasswordRequest,
  LoginRequest,
  RegisterRequest,
  TokenResponse,
  UpdateProfileRequest,
  UserInfo,
} from '@/types/auth'

export function register(data: RegisterRequest) {
  return http.post<UserInfo>('/auth/register', data)
}

export function login(data: LoginRequest) {
  return http.post<TokenResponse>('/auth/login', data)
}

export function getMe() {
  return http.get<UserInfo>('/auth/me')
}

export function updateProfile(data: UpdateProfileRequest) {
  return http.put<UserInfo>('/auth/me', data)
}

export function changePassword(data: ChangePasswordRequest) {
  return http.put<{ detail: string }>('/auth/me/password', data)
}

// 刷新走裸 axios：避免命中 http 拦截器的 401 重试逻辑
export function refreshToken(refresh_token: string) {
  return axios.post<TokenResponse>('/api/auth/refresh', { refresh_token })
}

// 登出走裸 axios：即使 access 过期也尽力撤销 refresh token，不触发刷新重放
export function logout(refresh_token?: string | null) {
  const token = localStorage.getItem('token')
  return axios.post(
    '/api/auth/logout',
    refresh_token ? { refresh_token } : {},
    {
      headers: token ? { Authorization: `Bearer ${token}` } : {},
    },
  )
}
