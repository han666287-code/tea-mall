import type { Product } from './product'

export interface CartItem {
  id: number
  quantity: number
  product: Product
  created_at: string
}

export interface CartItemPayload {
  product_id: number
  quantity: number
}
