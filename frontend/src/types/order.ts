export type OrderStatus = 'pending' | 'paid' | 'shipped' | 'completed' | 'cancelled'

export interface OrderItem {
  id: number
  product_id: number
  sku_id: number | null
  product_name: string
  price: string
  quantity: number
  subtotal: string
}

export interface Order {
  id: number
  order_no: string
  status: OrderStatus
  total_amount: string
  username: string | null
  receiver_name: string
  receiver_phone: string
  receiver_address: string
  created_at: string
  items: OrderItem[]
}

export interface OrderListResult {
  items: Order[]
  total: number
  page: number
  page_size: number
}

export interface OrderPayload {
  receiver_name: string
  receiver_phone: string
  receiver_address: string
}

export const ORDER_STATUS_TEXT: Record<OrderStatus, string> = {
  pending: '待支付',
  paid: '已支付',
  shipped: '已发货',
  completed: '已完成',
  cancelled: '已取消',
}

export const ORDER_STATUS_TAG: Record<OrderStatus, 'warning' | 'primary' | 'info' | 'success' | 'danger'> = {
  pending: 'warning',
  paid: 'primary',
  shipped: 'info',
  completed: 'success',
  cancelled: 'danger',
}
