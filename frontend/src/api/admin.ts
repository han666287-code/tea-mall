import http from './http'
import type { Order, OrderListResult, OrderStatus } from '@/types/order'

export function getAdminOrders(params: { status?: string; page?: number; page_size?: number }) {
  return http.get<OrderListResult>('/admin/orders', { params })
}

export function updateOrderStatus(id: number, status: OrderStatus) {
  return http.patch<Order>(`/admin/orders/${id}/status`, { status })
}
