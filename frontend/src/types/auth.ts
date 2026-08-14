export interface UserInfo {
  id: number
  username: string
  email: string | null
  nickname: string
  role: 'user' | 'admin'
  status: 'active' | 'disabled'
  is_root: boolean
  created_at: string
}

export interface UserListResult {
  items: UserInfo[]
  total: number
  page: number
  page_size: number
}

export interface UserStatusUpdate {
  status: 'active' | 'disabled'
}

export interface UserRoleUpdate {
  role: 'user' | 'admin'
}

export interface LoginRequest {
  username: string
  password: string
}

export interface RegisterRequest {
  username: string
  password: string
  nickname: string
  email?: string | null
}

export interface UpdateProfileRequest {
  nickname?: string
  email?: string | null
}

export interface ChangePasswordRequest {
  old_password: string
  new_password: string
}

export interface TokenResponse {
  token: string
  refresh_token: string
  token_type: string
  expires_in: number
  user: UserInfo
}
