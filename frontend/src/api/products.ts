import http from './http'
import type { Product, ProductListResult, ProductPayload } from '@/types/product'

export interface ProductQuery {
  category_id?: number
  keyword?: string
  page?: number
  page_size?: number
  include_off_sale?: boolean
}

export function getProducts(params: ProductQuery) {
  return http.get<ProductListResult>('/products', { params })
}

export function getProduct(id: number) {
  return http.get<Product>(`/products/${id}`)
}

export function createProduct(data: ProductPayload) {
  return http.post<Product>('/products', data)
}

export function updateProduct(id: number, data: Partial<ProductPayload>) {
  return http.put<Product>(`/products/${id}`, data)
}

export function deleteProduct(id: number) {
  return http.delete(`/products/${id}`)
}

export function uploadProductImage(id: number, file: File) {
  const formData = new FormData()
  formData.append('file', file)
  return http.post<Product>(`/products/${id}/image`, formData)
}
