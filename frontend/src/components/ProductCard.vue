<template>
  <article class="product-card" @click="goDetail">
    <div class="card-media">
      <el-image
        v-if="product.image_url"
        :src="product.image_url"
        fit="cover"
        class="card-img"
      />
      <div v-else class="card-placeholder">
        <svg viewBox="0 0 48 48" fill="none" aria-hidden="true">
          <path
            d="M24 5.5c-1.2 6.4-5.8 11.6-10.4 15.2C9 24.6 7 28.9 7 33.5c0 7.5 7.6 9.5 17 9.5s17-2 17-9.5c0-4.6-2-8.9-6.6-12.8C29.8 17.1 25.2 11.9 24 5.5Z"
            fill="#d9d2c0"
          />
          <path d="M24 7v35" stroke="#fff" stroke-width="2.4" stroke-linecap="round" />
          <path d="M24 16.5c-3.6 3.4-6.4 8.2-7.2 14M24 16.5c3.6 3.4 6.4 8.2 7.2 14" stroke="#fff" stroke-width="2" stroke-linecap="round" stroke-opacity="0.7" />
        </svg>
        <span>暂无图片</span>
      </div>
      <span v-if="product.stock <= 0" class="badge badge-out">已售罄</span>
      <span v-else-if="product.category_name" class="badge badge-cat">
        {{ product.category_name }}
      </span>
      <div class="card-actions">
        <el-button
          type="primary"
          size="small"
          round
          :disabled="product.stock <= 0"
          :loading="adding"
          @click.stop="handleAddToCart"
        >
          {{ canDirectAdd ? '加入购物车' : '选规格' }}
        </el-button>
      </div>
    </div>
    <div class="card-body">
      <h3 class="card-name" :title="product.name">{{ product.name }}</h3>
      <div class="card-meta">
        <span class="card-price"><em>¥</em>{{ priceText }}</span>
        <span class="card-stock" :class="{ out: product.stock <= 0 }">{{ stockText }}</span>
      </div>
    </div>
  </article>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { computed, ref } from 'vue'
import { useRouter } from 'vue-router'

import { useAuthStore } from '@/store/auth'
import { useCartStore } from '@/store/cart'
import type { Product } from '@/types/product'

const props = defineProps<{ product: Product }>()
const router = useRouter()
const authStore = useAuthStore()
const cartStore = useCartStore()
const adding = ref(false)

const activeSkus = computed(() => (props.product.skus ?? []).filter((s) => s.is_active))
const canDirectAdd = computed(() => activeSkus.value.length === 1)
const priceText = computed(() => Number(props.product.price).toFixed(2))
const stockText = computed(() =>
  props.product.stock > 0 ? `库存 ${props.product.stock}` : '已售罄',
)

function goDetail() {
  router.push(`/products/${props.product.id}`)
}

async function handleAddToCart() {
  if (!canDirectAdd.value) {
    goDetail()
    return
  }
  const skuId = activeSkus.value[0]?.id
  if (!skuId) return
  if (!authStore.token) {
    ElMessage.warning('请先登录')
    router.push({ path: '/login', query: { redirect: router.currentRoute.value.fullPath } })
    return
  }
  adding.value = true
  try {
    await cartStore.addToCart(skuId, 1)
    ElMessage.success('已加入购物车')
  } finally {
    adding.value = false
  }
}
</script>

<style scoped>
.product-card {
  background: var(--tea-surface);
  border: 1px solid var(--tea-line-soft);
  border-radius: var(--tea-radius);
  overflow: hidden;
  cursor: pointer;
  transition:
    transform 0.3s cubic-bezier(0.22, 0.61, 0.36, 1),
    box-shadow 0.3s ease,
    border-color 0.3s ease;
}

.product-card:hover {
  transform: translateY(-6px);
  border-color: rgba(169, 126, 58, 0.4);
  box-shadow: var(--tea-shadow);
}

.card-media {
  position: relative;
  aspect-ratio: 4 / 3;
  background: var(--tea-gold-soft);
  overflow: hidden;
}

.card-img {
  width: 100%;
  height: 100%;
  transition: transform 0.5s ease;
}

.product-card:hover .card-img {
  transform: scale(1.06);
}

.card-placeholder {
  position: absolute;
  inset: 0;
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  gap: 10px;
  color: var(--tea-muted);
  font-size: 13px;
}

.card-placeholder svg {
  width: 56px;
  height: 56px;
}

.badge {
  position: absolute;
  top: 12px;
  padding: 4px 12px;
  border-radius: 999px;
  font-size: 12px;
  letter-spacing: 0.04em;
  color: #fff;
}

.badge-cat {
  left: 12px;
  background: rgba(36, 74, 52, 0.78);
  backdrop-filter: blur(4px);
}

.badge-out {
  left: 12px;
  background: rgba(176, 69, 47, 0.88);
}

.card-actions {
  position: absolute;
  left: 0;
  right: 0;
  bottom: 0;
  display: flex;
  justify-content: center;
  padding: 18px;
  background: linear-gradient(0deg, rgba(24, 32, 22, 0.55), transparent);
  opacity: 0;
  transform: translateY(10px);
  transition:
    opacity 0.28s ease,
    transform 0.28s ease;
}

.product-card:hover .card-actions {
  opacity: 1;
  transform: translateY(0);
}

.card-body {
  padding: 16px;
}

.card-name {
  margin: 0;
  font-size: 15px;
  font-weight: 600;
  color: var(--tea-ink);
  line-height: 1.45;
  white-space: nowrap;
  overflow: hidden;
  text-overflow: ellipsis;
  transition: color 0.2s ease;
}

.product-card:hover .card-name {
  color: var(--tea-primary);
}

.card-meta {
  margin-top: 10px;
  display: flex;
  justify-content: space-between;
  align-items: center;
}

.card-price em {
  margin-right: 2px;
  font-size: 13px;
  font-style: normal;
  font-weight: 600;
}

.card-stock {
  color: var(--tea-muted);
  font-size: 12px;
}

.card-stock.out {
  color: var(--tea-price);
}

@media (max-width: 900px) {
  .card-actions {
    opacity: 1;
    transform: none;
    background: rgba(24, 32, 22, 0.32);
  }
}
</style>
