import http from './http'
import type { CartItem, CartItemPayload } from '@/types/cart'

export function getCartItems() {
  return http.get<CartItem[]>('/cart/items')
}

export function addCartItem(data: CartItemPayload) {
  return http.post<CartItem>('/cart/items', data)
}

export function updateCartItem(id: number, quantity: number) {
  return http.put<CartItem>(`/cart/items/${id}`, { quantity })
}

export function deleteCartItem(id: number) {
  return http.delete(`/cart/items/${id}`)
}
