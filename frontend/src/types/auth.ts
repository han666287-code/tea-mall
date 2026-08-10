export interface UserInfo {
  id: number
  username: string
  nickname: string
  role: 'user' | 'admin'
  created_at: string
}

export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  password: string
  nickname: string
}

export interface TokenResponse {
  token: string
  user: UserInfo
}
