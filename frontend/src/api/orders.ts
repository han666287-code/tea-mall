import http from './http'
import type { Order, OrderListResult, OrderPayload } from '@/types/order'

export function createOrder(data: OrderPayload) {
  return http.post<Order>('/orders', data)
}

export function getOrders(page = 1, pageSize = 10) {
  return http.get<OrderListResult>('/orders', { params: { page, page_size: pageSize } })
}

export function getOrder(id: number) {
  return http.get<Order>(`/orders/${id}`)
}

export function payOrder(id: number) {
  return http.post<Order>(`/orders/${id}/pay`)
}

export function cancelOrder(id: number) {
  return http.post<Order>(`/orders/${id}/cancel`)
}
