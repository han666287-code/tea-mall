<template>
  <div class="detail-page">
    <AppHeader />
    <div class="detail-content">
      <el-button link class="back-btn" @click="router.back()">← 返回</el-button>
      <div v-if="product" class="detail-card">
        <div class="detail-image">
          <el-image v-if="product.image_url" :src="product.image_url" fit="cover" class="detail-img" />
          <div v-else class="detail-img-placeholder">暂无图片</div>
        </div>
        <div class="detail-info">
          <h1 class="detail-name">{{ product.name }}</h1>
          <div class="detail-meta">分类：{{ product.category_name || '-' }}</div>
          <div class="detail-price">¥{{ priceText }}</div>
          <div class="detail-stock">库存：{{ product.stock }}</div>
          <p class="detail-desc">{{ product.description || '暂无描述' }}</p>
        </div>
      </div>
      <EmptyState v-else-if="notFound" message="商品不存在或已下架" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { getProduct } from '@/api/products'
import AppHeader from '@/components/AppHeader.vue'
import EmptyState from '@/components/EmptyState.vue'
import type { Product } from '@/types/product'

const route = useRoute()
const router = useRouter()
const product = ref<Product | null>(null)
const notFound = ref(false)

const priceText = computed(() =>
  product.value ? Number(product.value.price).toFixed(2) : '0.00',
)

onMounted(async () => {
  try {
    const { data } = await getProduct(Number(route.params.id))
    product.value = data
  } catch {
    notFound.value = true
  }
})
</script>

<style scoped>
.detail-content {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;
}

.back-btn {
  margin-bottom: 12px;
}

.detail-card {
  display: flex;
  gap: 24px;
  background: #fff;
  padding: 24px;
  border-radius: 8px;
}

.detail-image {
  width: 380px;
  height: 380px;
  border-radius: 8px;
  background: #f5f0e8;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
  flex-shrink: 0;
}

.detail-img {
  width: 100%;
  height: 100%;
}

.detail-img-placeholder {
  color: #999;
}

.detail-info {
  flex: 1;
}

.detail-name {
  margin: 0 0 12px;
  font-size: 24px;
}

.detail-meta {
  color: #666;
  margin-bottom: 8px;
}

.detail-price {
  color: #d4380d;
  font-size: 28px;
  font-weight: 700;
  margin-bottom: 8px;
}

.detail-stock {
  color: #666;
  margin-bottom: 16px;
}

.detail-desc {
  color: #333;
  line-height: 1.8;
  white-space: pre-wrap;
}
</style>
