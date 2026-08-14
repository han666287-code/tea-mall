import type { Product, Sku } from './product'

export interface CartItem {
  id: number
  quantity: number
  product: Product
  sku: Sku
  created_at: string
}

export interface CartItemPayload {
  sku_id: number
  quantity: number
}
