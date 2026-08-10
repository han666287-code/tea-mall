<template>
  <el-card
    class="product-card"
    shadow="hover"
    :body-style="{ padding: '12px' }"
    @click="goDetail"
  >
    <div class="product-image">
      <el-image v-if="product.image_url" :src="product.image_url" fit="cover" class="product-img" />
      <div v-else class="product-img-placeholder">暂无图片</div>
    </div>
    <div class="product-name" :title="product.name">{{ product.name }}</div>
    <div class="product-meta">
      <span class="product-price">¥{{ priceText }}</span>
      <span class="product-stock" :class="{ out: product.stock <= 0 }">
        {{ product.stock > 0 ? `库存 ${product.stock}` : '缺货' }}
      </span>
    </div>
  </el-card>
</template>

<script setup lang="ts">
import { computed } from 'vue'
import { useRouter } from 'vue-router'

import type { Product } from '@/types/product'

const props = defineProps<{ product: Product }>()
const router = useRouter()

const priceText = computed(() => Number(props.product.price).toFixed(2))

function goDetail() {
  router.push(`/products/${props.product.id}`)
}
</script>

<style scoped>
.product-card {
  cursor: pointer;
}

.product-image {
  height: 180px;
  border-radius: 6px;
  background: #f5f0e8;
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.product-img {
  width: 100%;
  height: 100%;
}

.product-img-placeholder {
  color: #999;
  font-size: 14px;
}

.product-name {
  margin-top: 10px;
  font-size: 15px;
  font-weight: 600;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
}

.product-meta {
  margin-top: 8px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.product-price {
  color: #d4380d;
  font-size: 18px;
  font-weight: 700;
}

.product-stock {
  color: #999;
  font-size: 12px;
}

.product-stock.out {
  color: #d4380d;
}
</style>
