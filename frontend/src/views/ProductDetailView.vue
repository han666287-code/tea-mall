<template>
  <div class="detail-page">
    <AppHeader />
    <div class="detail-content">
      <el-button link class="back-btn" @click="router.back()">← 返回</el-button>
      <div v-if="product" v-loading="loading" class="detail-card">
        <div class="detail-image">
          <el-image v-if="product.image_url" :src="product.image_url" fit="cover" class="detail-img" />
          <div v-else class="detail-img-placeholder">暂无图片</div>
        </div>
        <div class="detail-info">
          <h1 class="detail-name">{{ product.name }}</h1>
          <div class="detail-meta">分类：{{ product.category_name || '-' }}</div>
          <div class="detail-price">¥{{ priceText }}</div>
          <div class="detail-stock">库存：{{ product.stock }}</div>
          <div v-if="product.stock > 0" class="detail-buy">
            <el-input-number v-model="buyQuantity" :min="1" :max="product.stock" />
            <el-button type="primary" size="large" :loading="adding" @click="handleAddToCart">
              加入购物车
            </el-button>
          </div>
          <div v-else class="detail-soldout">该商品暂时缺货</div>
          <p class="detail-desc">{{ product.description || '暂无描述' }}</p>
        </div>
      </div>
      <EmptyState v-else-if="notFound" message="商品不存在或已下架" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { getProduct } from '@/api/products'
import AppHeader from '@/components/AppHeader.vue'
import EmptyState from '@/components/EmptyState.vue'
import { useAuthStore } from '@/store/auth'
import { useCartStore } from '@/store/cart'
import type { Product } from '@/types/product'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const cartStore = useCartStore()
const product = ref<Product | null>(null)
const notFound = ref(false)
const buyQuantity = ref(1)
const adding = ref(false)
const loading = ref(true)

const priceText = computed(() =>
  product.value ? Number(product.value.price).toFixed(2) : '0.00',
)

onMounted(async () => {
  try {
    const { data } = await getProduct(Number(route.params.id))
    product.value = data
  } catch {
    notFound.value = true
  } finally {
    loading.value = false
  }
})

async function handleAddToCart() {
  if (!product.value) return
  if (!authStore.token) {
    ElMessage.warning('请先登录')
    router.push({ path: '/login', query: { redirect: router.currentRoute.value.fullPath } })
    return
  }
  adding.value = true
  try {
    await cartStore.addToCart(product.value.id, buyQuantity.value)
    ElMessage.success('已加入购物车')
  } finally {
    adding.value = false
  }
}
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

.detail-buy {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 16px;
}

.detail-soldout {
  color: #d4380d;
  margin-bottom: 16px;
}

.detail-desc {
  color: #333;
  line-height: 1.8;
  white-space: pre-wrap;
}
</style>
