<template>
  <div class="cart-page">
    <AppHeader />
    <div class="cart-content">
      <h2 class="cart-title">我的购物车</h2>
      <el-table v-if="cartStore.items.length" :data="cartStore.items" border stripe>
        <el-table-column label="商品" min-width="240">
          <template #default="{ row }">
            <div class="cart-product">
              <el-image
                v-if="row.product.image_url"
                :src="row.product.image_url"
                fit="cover"
                class="cart-img"
              />
              <div v-else class="cart-img cart-img-placeholder">无图</div>
              <router-link :to="`/products/${row.product.id}`" class="cart-name">
                {{ row.product.name }}
              </router-link>
            </div>
          </template>
        </el-table-column>
        <el-table-column label="单价" width="120">
          <template #default="{ row }">¥{{ Number(row.product.price).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column label="数量" width="180">
          <template #default="{ row }">
            <el-input-number
              :model-value="row.quantity"
              :min="1"
              :max="row.product.stock"
              @change="(value: number | undefined) => handleQuantity(row, value)"
            />
          </template>
        </el-table-column>
        <el-table-column label="小计" width="130">
          <template #default="{ row }">
            ¥{{ (row.quantity * Number(row.product.price)).toFixed(2) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="100">
          <template #default="{ row }">
            <el-button size="small" type="danger" @click="handleRemove(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <EmptyState v-else message="购物车还是空的，去逛逛茶叶吧" />
      <div v-if="cartStore.items.length" class="cart-footer">
        <span class="cart-total">
          共 {{ cartStore.totalQuantity }} 件，合计
          <b class="cart-total-price">¥{{ cartStore.totalPrice.toFixed(2) }}</b>
        </span>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'

import AppHeader from '@/components/AppHeader.vue'
import EmptyState from '@/components/EmptyState.vue'
import { useCartStore } from '@/store/cart'
import type { CartItem } from '@/types/cart'

const cartStore = useCartStore()

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
.cart-content {
  max-width: 1100px;
  margin: 0 auto;
  padding: 20px;
}

.cart-title {
  margin: 0 0 16px;
}

.cart-product {
  display: flex;
  align-items: center;
  gap: 12px;
}

.cart-img {
  width: 60px;
  height: 60px;
  border-radius: 4px;
  flex-shrink: 0;
}

.cart-img-placeholder {
  display: flex;
  align-items: center;
  justify-content: center;
  background: #f5f0e8;
  color: #999;
  font-size: 12px;
}

.cart-name {
  color: #333;
  text-decoration: none;
}

.cart-name:hover {
  color: #b8860b;
}

.cart-footer {
  margin-top: 20px;
  text-align: right;
}

.cart-total-price {
  color: #d4380d;
  font-size: 22px;
}
</style>
