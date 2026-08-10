<template>
  <div class="cart-page">
    <AppHeader />
    <div class="tea-page cart-body">
      <div class="page-head">
        <div>
          <p class="page-eyebrow">SHOPPING CART</p>
          <h1 class="page-title">我的购物车</h1>
        </div>
        <span v-if="cartStore.items.length" class="cart-count">
          共 {{ cartStore.totalQuantity }} 件好茶
        </span>
      </div>

      <div v-loading="cartStore.loading" class="cart-layout">
        <div v-if="cartStore.items.length" class="cart-list">
          <div v-for="row in cartStore.items" :key="row.id" class="cart-row">
            <router-link :to="`/products/${row.product.id}`" class="row-media">
              <el-image
                v-if="row.product.image_url"
                :src="row.product.image_url"
                fit="cover"
                class="row-img"
              />
              <div v-else class="row-img row-ph">暂无图</div>
            </router-link>
            <div class="row-main">
              <router-link :to="`/products/${row.product.id}`" class="row-name">
                {{ row.product.name }}
              </router-link>
              <span class="row-cat">{{ row.product.category_name || '甄选好茶' }}</span>
              <div class="row-price">¥{{ Number(row.product.price).toFixed(2) }}</div>
            </div>
            <div class="qty-stepper">
              <button
                class="qty-btn"
                type="button"
                :disabled="row.quantity <= 1"
                @click="handleQuantity(row, row.quantity - 1)"
              >
                −
              </button>
              <span class="qty-num">{{ row.quantity }}</span>
              <button
                class="qty-btn"
                type="button"
                :disabled="row.quantity >= row.product.stock"
                @click="handleQuantity(row, row.quantity + 1)"
              >
                +
              </button>
            </div>
            <div class="row-subtotal">¥{{ (row.quantity * Number(row.product.price)).toFixed(2) }}</div>
            <el-button link class="row-remove" @click="handleRemove(row)">
              <el-icon><Delete /></el-icon>
            </el-button>
          </div>
        </div>
        <EmptyState v-else message="购物车还是空的，去逛逛茶叶吧" />

        <aside v-if="cartStore.items.length" class="cart-summary">
          <h3>订单小计</h3>
          <div class="summary-row">
            <span>商品件数</span>
            <b>{{ cartStore.totalQuantity }}</b>
          </div>
          <div class="summary-row">
            <span>合计金额</span>
            <b class="summary-total">¥{{ cartStore.totalPrice.toFixed(2) }}</b>
          </div>
          <el-button type="primary" size="large" class="summary-btn" @click="goCheckout">
            去结算
          </el-button>
        </aside>
      </div>
    </div>
    <AppFooter />
  </div>
</template>

<script setup lang="ts">
import { Delete } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { useRouter } from 'vue-router'

import AppFooter from '@/components/AppFooter.vue'
import AppHeader from '@/components/AppHeader.vue'
import EmptyState from '@/components/EmptyState.vue'
import { useCartStore } from '@/store/cart'
import type { CartItem } from '@/types/cart'

const cartStore = useCartStore()
const router = useRouter()

function goCheckout() {
  router.push('/checkout')
}

function handleQuantity(row: CartItem, value: number | undefined) {
  if (value !== undefined && value >= 1) {
    cartStore.updateQuantity(row.id, value)
  }
}

async function handleRemove(row: CartItem) {
  await cartStore.removeItem(row.id)
  ElMessage.success('已删除')
}
</script>

<style scoped>
.cart-body {
  padding-top: 40px;
  padding-bottom: 24px;
}

.page-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  margin-bottom: 28px;
}

.page-eyebrow {
  margin: 0 0 8px;
  font-size: 12px;
  letter-spacing: 0.4em;
  color: var(--tea-gold);
}

.page-title {
  margin: 0;
  font-family: var(--tea-font-serif);
  font-size: 30px;
  letter-spacing: 0.1em;
  color: var(--tea-ink);
}

.cart-count {
  font-size: 14px;
  color: var(--tea-muted);
}

.cart-layout {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 28px;
  align-items: start;
}

.cart-list {
  display: flex;
  flex-direction: column;
  gap: 14px;
}

.cart-row {
  display: flex;
  align-items: center;
  gap: 20px;
  padding: 18px;
  background: var(--tea-surface);
  border: 1px solid var(--tea-line-soft);
  border-radius: var(--tea-radius);
  box-shadow: var(--tea-shadow-sm);
  transition:
    transform 0.25s ease,
    box-shadow 0.25s ease,
    border-color 0.25s ease;
}

.cart-row:hover {
  transform: translateY(-2px);
  border-color: rgba(169, 126, 58, 0.4);
  box-shadow: var(--tea-shadow);
}

.row-media {
  width: 84px;
  height: 84px;
  border-radius: 10px;
  overflow: hidden;
  flex-shrink: 0;
  background: var(--tea-gold-soft);
}

.row-img {
  width: 100%;
  height: 100%;
}

.row-ph {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  color: var(--tea-muted);
}

.row-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
  gap: 6px;
}

.row-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--tea-ink);
  text-decoration: none;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
  transition: color 0.2s ease;
}

.row-name:hover {
  color: var(--tea-primary);
}

.row-cat {
  font-size: 12px;
  color: var(--tea-muted);
}

.row-price {
  font-size: 14px;
  color: var(--tea-price);
  font-weight: 600;
}

.qty-stepper {
  display: inline-flex;
  align-items: center;
  border: 1px solid var(--tea-line);
  border-radius: 9px;
  overflow: hidden;
  background: #fff;
}

.qty-btn {
  width: 32px;
  height: 32px;
  border: none;
  background: transparent;
  font-size: 16px;
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
  min-width: 34px;
  text-align: center;
  font-size: 14px;
  font-weight: 600;
}

.row-subtotal {
  min-width: 90px;
  text-align: right;
  font-size: 16px;
  font-weight: 700;
  color: var(--tea-ink);
}

.row-remove {
  color: var(--tea-muted);
  font-size: 16px;
}

.row-remove:hover {
  color: var(--tea-price);
}

.cart-summary {
  position: sticky;
  top: 92px;
  padding: 26px;
  background: var(--tea-surface);
  border: 1px solid var(--tea-line-soft);
  border-radius: var(--tea-radius);
  box-shadow: var(--tea-shadow-sm);
}

.cart-summary h3 {
  margin: 0 0 20px;
  font-family: var(--tea-font-serif);
  font-size: 18px;
  letter-spacing: 0.1em;
  color: var(--tea-ink);
}

.summary-row {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 10px 0;
  font-size: 14px;
  color: var(--tea-ink-2);
}

.summary-total {
  font-size: 24px;
  color: var(--tea-price);
  font-family: var(--tea-font-sans);
  font-variant-numeric: tabular-nums;
}

.summary-btn {
  width: 100%;
  height: 46px;
  margin-top: 18px;
  border-radius: 10px;
  letter-spacing: 0.2em;
}

@media (max-width: 900px) {
  .cart-layout {
    grid-template-columns: 1fr;
  }

  .cart-summary {
    position: static;
  }
}

@media (max-width: 640px) {
  .row-main {
    flex: none;
  }

  .cart-row {
    flex-wrap: wrap;
  }
}
</style>
