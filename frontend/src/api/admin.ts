import http from './http'
import type { Order, OrderListResult, OrderStatus } from '@/types/order'
import type {
  UserInfo,
  UserListResult,
  UserRoleUpdate,
  UserStatusUpdate,
} from '@/types/auth'

export function getAdminOrders(params: { status?: string; page?: number; page_size?: number }) {
  return http.get<OrderListResult>('/admin/orders', { params })
}

export function updateOrderStatus(id: number, status: OrderStatus) {
  return http.patch<Order>(`/admin/orders/${id}/status`, { status })
}

export function getAdminUsers(params: {
  keyword?: string
  page?: number
  page_size?: number
}) {
  return http.get<UserListResult>('/admin/users', { params })
}

export function updateUserStatus(userId: number, data: UserStatusUpdate) {
  return http.patch<UserInfo>(`/admin/users/${userId}/status`, data)
}

export function updateUserRole(userId: number, data: UserRoleUpdate) {
  return http.patch<UserInfo>(`/admin/users/${userId}/role`, data)
}
