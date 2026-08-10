export interface Product {
  id: number
  name: string
  category_id: number
  category_name: string | null
  price: number
  stock: number
  description: string
  image_url: string
  is_on_sale: boolean
  created_at: string
}

export interface ProductListResult {
  items: Product[]
  total: number
  page: number
  page_size: number
}

export interface ProductPayload {
  name: string
  category_id: number
  price: number
  stock: number
  description: string
  image_url: string
  is_on_sale: boolean
}
