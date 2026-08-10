<template>
  <div class="home">
    <AppHeader />
    <div class="home-content">
      <div class="category-nav">
        <el-button :type="activeCategoryId === null ? 'primary' : ''" @click="selectCategory(null)">
          全部
        </el-button>
        <el-button
          v-for="category in categories"
          :key="category.id"
          :type="activeCategoryId === category.id ? 'primary' : ''"
          @click="selectCategory(category.id)"
        >
          {{ category.name }}
        </el-button>
      </div>
      <div v-if="products.length" class="product-grid">
        <ProductCard v-for="product in products" :key="product.id" :product="product" />
      </div>
      <EmptyState v-else message="暂无商品" />
      <PaginationBar
        :total="total"
        :page="page"
        :page-size="pageSize"
        @update:page="onPageChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'

import { getCategories } from '@/api/categories'
import { getProducts } from '@/api/products'
import AppHeader from '@/components/AppHeader.vue'
import EmptyState from '@/components/EmptyState.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import ProductCard from '@/components/ProductCard.vue'
import type { Category } from '@/types/category'
import type { Product } from '@/types/product'

const categories = ref<Category[]>([])
const products = ref<Product[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 12
const activeCategoryId = ref<number | null>(null)

async function loadCategories() {
  const { data } = await getCategories()
  categories.value = data
}

async function loadProducts() {
  const { data } = await getProducts({
    category_id: activeCategoryId.value ?? undefined,
    page: page.value,
    page_size: pageSize,
  })
  products.value = data.items
  total.value = data.total
}

function selectCategory(categoryId: number | null) {
  activeCategoryId.value = categoryId
  page.value = 1
  loadProducts()
}

function onPageChange(newPage: number) {
  page.value = newPage
  loadProducts()
}

onMounted(() => {
  loadCategories()
  loadProducts()
})
</script>

<style scoped>
.home-content {
  max-width: 1100px;
  margin: 0 auto;
  padding: 20px;
}

.category-nav {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  margin-bottom: 20px;
}

.product-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 16px;
}

@media (max-width: 900px) {
  .product-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
