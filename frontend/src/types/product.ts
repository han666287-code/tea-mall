export interface SkuSpecItem {
  name: string
  value: string
}

export interface Sku {
  id: number
  product_id: number
  sku_code: string
  price: number
  stock: number
  is_active: boolean
  specs: SkuSpecItem[]
  created_at: string
}

export interface SkuPayload {
  sku_code?: string
  price: number
  stock: number
  is_active: boolean
  specs: SkuSpecItem[]
}

export interface ProductImage {
  id: number
  url: string
  kind: 'main' | 'detail'
  sort_order: number
}

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
  skus: Sku[]
  images: ProductImage[]
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
  skus?: SkuPayload[]
}
