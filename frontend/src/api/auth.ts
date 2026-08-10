import http from './http'
import type { LoginRequest, RegisterRequest, TokenResponse, UserInfo } from '@/types/auth'

export function register(data: RegisterRequest) {
  return http.post<UserInfo>('/auth/register', data)
}

export function login(data: LoginRequest) {
  return http.post<TokenResponse>('/auth/login', data)
}

export function getMe() {
  return http.get<UserInfo>('/auth/me')
}
