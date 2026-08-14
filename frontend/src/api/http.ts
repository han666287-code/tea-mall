import axios, { type AxiosError, type AxiosRequestConfig } from 'axios'
import { ElMessage } from 'element-plus'

// 统一 axios 实例：基础路径 /api，由 Vite 代理转发到后端
const http = axios.create({
  baseURL: '/api',
  timeout: 10000,
})

// 请求拦截器：自动附带登录 token
http.interceptors.request.use((config) => {
  const token = localStorage.getItem('token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

// 从后端错误响应中提取可读信息，兼容 {detail: string} / {detail: [...]} / 无响应体
function extractErrorMessage(error: unknown): string {
  const data = (error as { response?: { data?: unknown } })?.response?.data as
    | { detail?: unknown; message?: string }
    | undefined
  const detail = data?.detail

  if (typeof detail === 'string' && detail) return detail
  if (Array.isArray(detail) && detail.length > 0) {
    const first = detail[0] as { loc?: unknown[]; msg?: string }
    const field = (first.loc ?? []).filter((part) => part !== 'body').join('.')
    const msg = first.msg || '输入格式不正确'
    return field ? `${field}: ${msg}` : msg
  }
  if (detail && typeof detail === 'object') {
    const message = (detail as { message?: string }).message
    if (message) return message
  }
  if (data?.message) return data.message
  return (error as { message?: string })?.message || '请求失败'
}

interface RetriableConfig extends AxiosRequestConfig {
  _retried?: boolean
}

function isAuthUrl(url?: string): boolean {
  if (!url) return false
  return (
    url.includes('/auth/login') ||
    url.includes('/auth/register') ||
    url.includes('/auth/refresh')
  )
}

// 单飞刷新：并发 401 只触发一次刷新请求
let refreshPromise: Promise<boolean> | null = null

// 响应拦截器：统一弹出错误提示
http.interceptors.response.use(
  (response) => response,
  async (error: AxiosError) => {
    const config = error.config as RetriableConfig | undefined
    if (error.response?.status === 401 && config && !config._retried && !isAuthUrl(config.url)) {
      const data = error.response.data as { code?: string } | undefined
      // 账号被禁用：不走刷新重放，直接退出登录
      if (data?.code === 'ACCOUNT_DISABLED') {
        const { useAuthStore } = await import('@/store/auth')
        useAuthStore().forceLogout()
        ElMessage.error('账号已被禁用，请联系管理员')
        if (window.location.pathname !== '/login') {
          window.location.href = `/login?redirect=${encodeURIComponent(
            window.location.pathname + window.location.search,
          )}`
        }
        return Promise.reject(error)
      }
      config._retried = true
      // 动态导入避免 http.ts <-> store/auth.ts 循环依赖
      const { useAuthStore } = await import('@/store/auth')
      const auth = useAuthStore()
      if (!refreshPromise) {
        refreshPromise = auth.refreshAccessToken().finally(() => {
          refreshPromise = null
        })
      }
      const ok = await refreshPromise
      if (ok) {
        return http(config)
      }
      auth.forceLogout()
      ElMessage.error('登录已过期，请重新登录')
      if (window.location.pathname !== '/login') {
        window.location.href = `/login?redirect=${encodeURIComponent(
          window.location.pathname + window.location.search,
        )}`
      }
    } else {
      ElMessage.error(extractErrorMessage(error))
    }
    return Promise.reject(error)
  },
)

export default http
