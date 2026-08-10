<template>
  <div class="product-list-page">
    <AppHeader />
    <div class="list-content">
      <div class="filter-bar">
        <el-select
          v-model="categoryId"
          style="width: 180px"
          @change="applyFilter"
        >
          <el-option label="全部商品" value="" />
          <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
        </el-select>
        <el-input
          v-model="keyword"
          placeholder="搜索商品名称或描述"
          clearable
          style="width: 260px"
          @keyup.enter="applyFilter"
          @clear="applyFilter"
        />
        <el-button type="primary" @click="applyFilter">搜索</el-button>
      </div>
      <div v-loading="loading">
        <div v-if="products.length" class="product-grid">
          <ProductCard v-for="product in products" :key="product.id" :product="product" />
        </div>
        <EmptyState v-else message="没有找到相关商品" />
      </div>
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
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { getCategories } from '@/api/categories'
import { getProducts, type ProductQuery } from '@/api/products'
import AppHeader from '@/components/AppHeader.vue'
import EmptyState from '@/components/EmptyState.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import ProductCard from '@/components/ProductCard.vue'
import type { Category } from '@/types/category'
import type { Product } from '@/types/product'

const route = useRoute()
const router = useRouter()

const categories = ref<Category[]>([])
const products = ref<Product[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 12
const categoryId = ref<number | ''>('')
const keyword = ref('')
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const params: ProductQuery = { page: page.value, page_size: pageSize }
    if (categoryId.value !== '') {
      params.category_id = categoryId.value
    }
    if (keyword.value.trim()) {
      params.keyword = keyword.value.trim()
    }
    const { data } = await getProducts(params)
    products.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function applyFilter() {
  page.value = 1
  const query: Record<string, string> = {}
  if (categoryId.value !== '') {
    query.category_id = String(categoryId.value)
  }
  if (keyword.value.trim()) {
    query.keyword = keyword.value.trim()
  }
  router.replace({ query })
}

function onPageChange(newPage: number) {
  page.value = newPage
  load()
}

// 监听 URL 查询参数变化（含首次进入、顶部搜索框跳转、分类切换），自动刷新列表
watch(
  () => route.query,
  () => {
    const queryCategory = route.query.category_id
    const queryKeyword = route.query.keyword
    categoryId.value = queryCategory ? Number(queryCategory) : ''
    keyword.value = typeof queryKeyword === 'string' ? queryKeyword : ''
    page.value = 1
    load()
  },
  { immediate: true },
)

onMounted(async () => {
  const { data } = await getCategories()
  categories.value = data
})
</script>

<style scoped>
.list-content {
  max-width: 1100px;
  margin: 0 auto;
  padding: 20px;
}

.filter-bar {
  display: flex;
  gap: 12px;
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
