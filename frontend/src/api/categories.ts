import http from './http'
import type { Category, CategoryPayload } from '@/types/category'

export function getCategories() {
  return http.get<Category[]>('/categories')
}

export function createCategory(data: CategoryPayload) {
  return http.post<Category>('/categories', data)
}

export function updateCategory(id: number, data: Partial<CategoryPayload>) {
  return http.put<Category>(`/categories/${id}`, data)
}

export function deleteCategory(id: number) {
  return http.delete(`/categories/${id}`)
}
