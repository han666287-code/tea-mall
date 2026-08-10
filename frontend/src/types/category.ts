export interface Category {
  id: number
  name: string
  sort_order: number
  created_at: string
}

export interface CategoryPayload {
  name: string
  sort_order: number
}
