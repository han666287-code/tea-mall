<template>
  <div class="product-list-page">
    <AppHeader />

    <div class="page-hero">
      <div class="tea-page">
        <p class="hero-eyebrow">TEAMALL · COLLECTION</p>
        <h1 class="hero-title">全部好茶</h1>
        <p class="hero-sub">按茶系与风味，找到属于你的那一杯</p>
      </div>
    </div>

    <div class="tea-page list-body">
      <div class="filter-card">
        <div class="filter-item">
          <span class="filter-label">茶系</span>
          <el-select v-model="categoryId" placeholder="全部商品" @change="applyFilter">
            <el-option label="全部商品" value="" />
            <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
          </el-select>
        </div>
        <div class="filter-item grow">
          <span class="filter-label">搜索</span>
          <el-input
            v-model="keyword"
            placeholder="搜索商品名称或描述"
            clearable
            @keyup.enter="applyFilter"
            @clear="applyFilter"
          >
            <template #prefix>
              <el-icon><Search /></el-icon>
            </template>
          </el-input>
        </div>
        <el-button type="primary" @click="applyFilter">搜索</el-button>
        <span class="result-count">共 {{ total }} 款好茶</span>
      </div>

      <div v-loading="loading" class="results">
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
    <AppFooter />
  </div>
</template>

<script setup lang="ts">
import { Search } from '@element-plus/icons-vue'
import { onMounted, ref, watch } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { getCategories } from '@/api/categories'
import { getProducts, type ProductQuery } from '@/api/products'
import AppFooter from '@/components/AppFooter.vue'
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
.page-hero {
  padding: 64px 0;
  background:
    radial-gradient(760px 280px at 88% -30%, rgba(169, 126, 58, 0.24), transparent 60%),
    linear-gradient(150deg, #1c3a2a 0%, #2f5e43 70%, #35684b 100%);
  color: #f6f2ea;
}

.hero-eyebrow {
  margin: 0 0 12px;
  font-size: 12px;
  letter-spacing: 0.42em;
  color: #d9b877;
}

.hero-title {
  margin: 0;
  font-family: var(--tea-font-serif);
  font-size: 36px;
  letter-spacing: 0.1em;
}

.hero-sub {
  margin: 12px 0 0;
  font-size: 14px;
  color: rgba(246, 242, 234, 0.72);
}

.list-body {
  padding-top: 32px;
  padding-bottom: 24px;
}

.filter-card {
  display: flex;
  align-items: center;
  gap: 18px;
  flex-wrap: wrap;
  padding: 18px 22px;
  margin-bottom: 28px;
  background: var(--tea-surface);
  border: 1px solid var(--tea-line-soft);
  border-radius: var(--tea-radius);
  box-shadow: var(--tea-shadow-sm);
}

.filter-item {
  display: flex;
  align-items: center;
  gap: 10px;
}

.filter-item.grow {
  flex: 1;
  min-width: 220px;
}

.filter-item :deep(.el-select),
.filter-item :deep(.el-input) {
  width: 190px;
}

.filter-item.grow :deep(.el-input) {
  width: 100%;
}

.filter-label {
  font-size: 13px;
  color: var(--tea-muted);
  white-space: nowrap;
}

.result-count {
  margin-left: auto;
  font-size: 13px;
  color: var(--tea-muted);
}

.results {
  min-height: 200px;
}

.product-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 22px;
}

@media (max-width: 900px) {
  .product-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .result-count {
    margin-left: 0;
    width: 100%;
  }
}
</style>
