<template>
  <div class="detail-page">
    <AppHeader />
    <div class="tea-page detail-body">
      <el-button link class="back-btn" @click="router.back()">
        <el-icon><ArrowLeft /></el-icon>
        返回
      </el-button>
      <div v-if="product" v-loading="loading" class="detail-card">
        <div class="detail-media">
          <div class="media-frame">
            <el-image
              v-if="product.image_url"
              :src="product.image_url"
              fit="cover"
              class="detail-img"
            />
            <div v-else class="detail-placeholder">
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
            <span v-if="product.stock <= 0" class="soldout-ribbon">已售罄</span>
          </div>
        </div>
        <div class="detail-info">
          <p class="info-eyebrow">{{ product.category_name || '甄选好茶' }}</p>
          <h1 class="info-name">{{ product.name }}</h1>
          <div class="info-price">
            <span class="price-currency">¥</span>{{ priceText }}
          </div>
          <div class="info-stock" :class="{ low: isLowStock }">
            <el-icon>
              <CircleCheck v-if="inStock" />
              <WarningFilled v-else />
            </el-icon>
            <span>{{ stockText }}</span>
          </div>
          <div class="info-divider"></div>
          <div v-if="product.stock > 0" class="detail-buy">
            <div class="quantity-box">
              <button
                class="qty-btn"
                type="button"
                :disabled="buyQuantity <= 1"
                @click="buyQuantity--"
              >
                −
              </button>
              <span class="qty-num">{{ buyQuantity }}</span>
              <button
                class="qty-btn"
                type="button"
                :disabled="buyQuantity >= product.stock"
                @click="buyQuantity++"
              >
                +
              </button>
            </div>
            <el-button type="primary" size="large" :loading="adding" @click="handleAddToCart">
              加入购物车
            </el-button>
          </div>
          <div v-else class="soldout-tip">该商品暂时缺货，请看看其他好茶</div>
          <div class="info-desc">
            <h3>商品介绍</h3>
            <p>{{ product.description || '暂无描述' }}</p>
          </div>
        </div>
      </div>
      <EmptyState v-else-if="notFound" message="商品不存在或已下架" />
    </div>
    <AppFooter />
  </div>
</template>

<script setup lang="ts">
import { ArrowLeft, CircleCheck, WarningFilled } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { getProduct } from '@/api/products'
import AppFooter from '@/components/AppFooter.vue'
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
const inStock = computed(() => (product.value ? product.value.stock > 0 : false))
const isLowStock = computed(() => (product.value ? product.value.stock > 0 && product.value.stock <= 10 : false))
const stockText = computed(() => {
  if (!product.value) return ''
  if (product.value.stock <= 0) return '已售罄'
  if (product.value.stock <= 10) return `库存紧张，仅剩 ${product.value.stock} 件`
  return `现货充足 · 库存 ${product.value.stock} 件`
})

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
.detail-body {
  padding-top: 28px;
  padding-bottom: 24px;
  max-width: 1100px;
}

.back-btn {
  margin-bottom: 16px;
  color: var(--tea-muted);
  display: inline-flex;
  align-items: center;
}

.back-btn:hover {
  color: var(--tea-gold);
}

.detail-card {
  display: flex;
  gap: 48px;
  background: var(--tea-surface);
  padding: 36px;
  border: 1px solid var(--tea-line-soft);
  border-radius: var(--tea-radius-lg);
  box-shadow: var(--tea-shadow-sm);
}

.detail-media {
  width: 46%;
  flex-shrink: 0;
}

.media-frame {
  position: relative;
  aspect-ratio: 1 / 1;
  border-radius: var(--tea-radius);
  background: var(--tea-gold-soft);
  border: 1px solid var(--tea-line-soft);
  display: flex;
  align-items: center;
  justify-content: center;
  overflow: hidden;
}

.detail-img {
  width: 100%;
  height: 100%;
}

.detail-placeholder {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 12px;
  color: var(--tea-muted);
  font-size: 14px;
}

.detail-placeholder svg {
  width: 96px;
  height: 96px;
}

.soldout-ribbon {
  position: absolute;
  top: 18px;
  right: -38px;
  width: 150px;
  padding: 8px 0;
  transform: rotate(45deg);
  text-align: center;
  font-size: 13px;
  letter-spacing: 0.12em;
  color: #fff;
  background: rgba(176, 69, 47, 0.92);
}

.detail-info {
  flex: 1;
}

.info-eyebrow {
  margin: 0 0 10px;
  font-size: 12px;
  letter-spacing: 0.36em;
  color: var(--tea-gold);
}

.info-name {
  margin: 0;
  font-family: var(--tea-font-serif);
  font-size: 30px;
  line-height: 1.4;
  color: var(--tea-ink);
}

.info-price {
  margin-top: 22px;
  color: var(--tea-price);
  font-size: 34px;
  font-weight: 700;
  font-family: var(--tea-font-sans);
  font-variant-numeric: tabular-nums;
}

.price-currency {
  margin-right: 4px;
  font-size: 20px;
}

.info-stock {
  display: inline-flex;
  align-items: center;
  gap: 6px;
  margin-top: 16px;
  padding: 7px 14px;
  border-radius: 999px;
  font-size: 13px;
  color: var(--tea-primary);
  background: var(--tea-primary-soft);
}

.info-stock.low {
  color: var(--tea-gold-deep);
  background: var(--tea-gold-soft);
}

.info-divider {
  height: 1px;
  margin: 24px 0;
  background: var(--tea-line-soft);
}

.detail-buy {
  display: flex;
  align-items: center;
  gap: 12px;
  margin-bottom: 28px;
}

.quantity-box {
  display: inline-flex;
  align-items: center;
  border: 1px solid var(--tea-line);
  border-radius: 10px;
  overflow: hidden;
  background: #fff;
}

.qty-btn {
  width: 40px;
  height: 40px;
  border: none;
  background: transparent;
  font-size: 18px;
  color: var(--tea-ink-2);
  cursor: pointer;
  transition: background 0.2s ease, color 0.2s ease;
}

.qty-btn:hover:not(:disabled) {
  background: var(--tea-primary-soft);
  color: var(--tea-primary);
}

.qty-btn:disabled {
  color: #c9c3b4;
  cursor: not-allowed;
}

.qty-num {
  min-width: 46px;
  text-align: center;
  font-size: 15px;
  font-weight: 600;
  color: var(--tea-ink);
}

.soldout-tip {
  margin-bottom: 28px;
  padding: 14px 18px;
  border-radius: 10px;
  font-size: 14px;
  color: var(--tea-price);
  background: rgba(176, 69, 47, 0.08);
  border: 1px solid rgba(176, 69, 47, 0.18);
}

.info-desc {
  padding-top: 24px;
  border-top: 1px dashed var(--tea-line);
}

.info-desc h3 {
  margin: 0 0 12px;
  font-family: var(--tea-font-serif);
  font-size: 16px;
  letter-spacing: 0.14em;
  color: var(--tea-ink);
  position: relative;
  padding-left: 14px;
}

.info-desc h3::before {
  content: '';
  position: absolute;
  left: 0;
  top: 4px;
  bottom: 4px;
  width: 3px;
  border-radius: 3px;
  background: var(--tea-gold);
}

@media (max-width: 900px) {
  .detail-card {
    flex-direction: column;
    gap: 28px;
    padding: 24px;
  }

  .detail-media {
    width: 100%;
  }
}
</style>
