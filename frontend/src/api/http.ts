import axios from 'axios'
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

// 响应拦截器：统一弹出错误提示
http.interceptors.response.use(
  (response) => response,
  (error) => {
    const message = error.response?.data?.detail || error.message || '请求失败'
    ElMessage.error(message)
    return Promise.reject(error)
  },
)

export default http
