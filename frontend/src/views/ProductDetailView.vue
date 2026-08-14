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
            <span v-if="effectiveStock <= 0" class="soldout-ribbon">已售罄</span>
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
          <div v-if="hasSpecs" class="spec-selector">
            <div v-for="group in specGroups" :key="group.name" class="spec-group">
              <span class="spec-name">{{ group.name }}</span>
              <div class="spec-options">
                <button
                  v-for="option in group.options"
                  :key="option.value"
                  type="button"
                  class="spec-option"
                  :class="{ active: isSpecSelected(group.name, option.value) }"
                  :disabled="!optionSelectable(group.name, option.value)"
                  @click="selectSpec(group.name, option.value)"
                >
                  {{ option.value }}
                </button>
              </div>
            </div>
          </div>
          <div v-if="effectiveStock > 0" class="detail-buy">
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
                :disabled="buyQuantity >= effectiveStock"
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
      <div v-if="detailImages.length" class="detail-gallery">
        <h3>商品详情</h3>
        <div class="gallery-grid">
          <el-image
            v-for="img in detailImages"
            :key="img.id"
            :src="img.url"
            :preview-src-list="detailImageUrls"
            fit="cover"
            class="gallery-img"
          />
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
import type { Product, Sku } from '@/types/product'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const cartStore = useCartStore()
const product = ref<Product | null>(null)
const notFound = ref(false)
const buyQuantity = ref(1)
const adding = ref(false)
const loading = ref(true)
const selectedSpecs = ref<Record<string, string>>({})

const activeSkus = computed(() => (product.value?.skus ?? []).filter((s) => s.is_active))
const hasSpecs = computed(() => activeSkus.value.some((s) => s.specs.length > 0))

const specGroups = computed(() => {
  const groups: { name: string; options: { value: string }[] }[] = []
  if (!product.value) return groups
  const names = Array.from(
    new Set(activeSkus.value.flatMap((s) => s.specs.map((x) => x.name))),
  )
  for (const name of names) {
    const values = Array.from(
      new Set(
        activeSkus.value.flatMap((s) => s.specs.filter((x) => x.name === name).map((x) => x.value)),
      ),
    )
    groups.push({ name, options: values.map((value) => ({ value })) })
  }
  return groups
})

const detailImages = computed(() =>
  (product.value?.images ?? []).filter((img) => img.kind === 'detail'),
)
const detailImageUrls = computed(() => detailImages.value.map((img) => img.url))

function skuMatches(sku: Sku, sel: Record<string, string>) {
  return Object.entries(sel).every(([name, value]) =>
    sku.specs.some((x) => x.name === name && x.value === value),
  )
}

function isSpecSelected(name: string, value: string) {
  return selectedSpecs.value[name] === value
}

function optionSelectable(name: string, value: string) {
  const tentative = { ...selectedSpecs.value, [name]: value }
  return activeSkus.value.some((s) => skuMatches(s, tentative))
}

function selectSpec(name: string, value: string) {
  if (!optionSelectable(name, value)) return
  selectedSpecs.value = { ...selectedSpecs.value, [name]: value }
}

const effectiveSku = computed(() => {
  if (!product.value) return null
  const sel = selectedSpecs.value
  const names = Object.keys(sel)
  if (names.length === 0) return activeSkus.value[0] ?? null
  return (
    activeSkus.value.find(
      (s) => names.length === s.specs.length && skuMatches(s, sel),
    ) ?? null
  )
})

const priceText = computed(() =>
  effectiveSku.value
    ? Number(effectiveSku.value.price).toFixed(2)
    : Number(product.value?.price ?? 0).toFixed(2),
)
const effectiveStock = computed(() => effectiveSku.value?.stock ?? product.value?.stock ?? 0)
const inStock = computed(() => effectiveStock.value > 0)
const isLowStock = computed(() => effectiveStock.value > 0 && effectiveStock.value <= 10)
const stockText = computed(() => {
  if (!product.value) return ''
  if (effectiveStock.value <= 0) return '已售罄'
  if (effectiveStock.value <= 10) return `库存紧张，仅剩 ${effectiveStock.value} 件`
  return `现货充足 · 库存 ${effectiveStock.value} 件`
})

onMounted(async () => {
  try {
    const { data } = await getProduct(Number(route.params.id))
    product.value = data
    if (data.skus?.length) {
      const first = data.skus.find((s) => s.is_active) ?? data.skus[0]
      const sel: Record<string, string> = {}
      for (const spec of first.specs) {
        sel[spec.name] = spec.value
      }
      selectedSpecs.value = sel
    }
  } catch {
    notFound.value = true
  } finally {
    loading.value = false
  }
})

async function handleAddToCart() {
  if (!product.value) return
  if (hasSpecs.value && !effectiveSku.value) {
    ElMessage.warning('请选择规格')
    return
  }
  if (!authStore.token) {
    ElMessage.warning('请先登录')
    router.push({ path: '/login', query: { redirect: router.currentRoute.value.fullPath } })
    return
  }
  adding.value = true
  try {
    const skuId = effectiveSku.value?.id
    if (!skuId) {
      ElMessage.warning('请选择规格')
      return
    }
    await cartStore.addToCart(skuId, buyQuantity.value)
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

.detail-gallery {
  margin-top: 32px;
  padding: 28px;
  background: var(--tea-surface);
  border: 1px solid var(--tea-line-soft);
  border-radius: var(--tea-radius-lg);
  box-shadow: var(--tea-shadow-sm);
}

.detail-gallery h3 {
  margin: 0 0 18px;
  font-family: var(--tea-font-serif);
  font-size: 17px;
  letter-spacing: 0.14em;
  color: var(--tea-ink);
  position: relative;
  padding-left: 14px;
}

.detail-gallery h3::before {
  content: '';
  position: absolute;
  left: 0;
  top: 3px;
  bottom: 3px;
  width: 3px;
  border-radius: 3px;
  background: var(--tea-gold);
}

.gallery-grid {
  display: grid;
  grid-template-columns: repeat(3, 1fr);
  gap: 16px;
}

.gallery-img {
  width: 100%;
  aspect-ratio: 4 / 3;
  border-radius: 10px;
  border: 1px solid var(--tea-line-soft);
  cursor: zoom-in;
}

@media (max-width: 900px) {
  .gallery-grid {
    grid-template-columns: repeat(2, 1fr);
  }
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

.spec-selector {
  margin-bottom: 24px;
}

.spec-group {
  display: flex;
  align-items: center;
  gap: 12px;
  flex-wrap: wrap;
  margin-bottom: 14px;
}

.spec-group:last-child {
  margin-bottom: 0;
}

.spec-name {
  font-size: 13px;
  color: var(--tea-muted);
  min-width: 56px;
}

.spec-options {
  display: flex;
  gap: 10px;
  flex-wrap: wrap;
}

.spec-option {
  padding: 8px 16px;
  border: 1px solid var(--tea-line);
  border-radius: 999px;
  background: #fff;
  font-size: 13px;
  color: var(--tea-ink-2);
  cursor: pointer;
  transition: border-color 0.2s ease, color 0.2s ease, background 0.2s ease;
}

.spec-option:hover:not(:disabled) {
  border-color: var(--tea-gold);
  color: var(--tea-primary);
}

.spec-option.active {
  border-color: var(--tea-gold);
  background: var(--tea-gold-soft);
  color: var(--tea-primary);
  font-weight: 600;
}

.spec-option:disabled {
  color: #c9c3b4;
  cursor: not-allowed;
  background: #f7f4ec;
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
