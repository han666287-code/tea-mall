<template>
  <div class="checkout-page">
    <AppHeader />
    <div class="checkout-content">
      <h2 class="page-title">确认订单</h2>
      <div v-if="cartStore.items.length" class="checkout-body">
        <el-table :data="cartStore.items" border stripe>
          <el-table-column label="商品" min-width="220">
            <template #default="{ row }">
              <div class="cart-product">
                <el-image
                  v-if="row.product.image_url"
                  :src="row.product.image_url"
                  fit="cover"
                  class="cart-img"
                />
                <div v-else class="cart-img cart-img-placeholder">无图</div>
                <span>{{ row.product.name }}</span>
              </div>
            </template>
          </el-table-column>
          <el-table-column label="单价" width="120">
            <template #default="{ row }">¥{{ Number(row.product.price).toFixed(2) }}</template>
          </el-table-column>
          <el-table-column prop="quantity" label="数量" width="100" />
          <el-table-column label="小计" width="130">
            <template #default="{ row }">
              ¥{{ (row.quantity * Number(row.product.price)).toFixed(2) }}
            </template>
          </el-table-column>
        </el-table>

        <el-form :model="form" label-width="80px" class="receiver-form">
          <el-form-item label="收货人">
            <el-input v-model="form.receiver_name" placeholder="请输入收货人姓名" />
          </el-form-item>
          <el-form-item label="手机号">
            <el-input v-model="form.receiver_phone" placeholder="请输入手机号" />
          </el-form-item>
          <el-form-item label="收货地址">
            <el-input
              v-model="form.receiver_address"
              type="textarea"
              :rows="2"
              placeholder="请输入收货地址"
            />
          </el-form-item>
        </el-form>

        <div class="checkout-footer">
          <span class="total-label">
            合计：<b class="total-price">¥{{ cartStore.totalPrice.toFixed(2) }}</b>
          </span>
          <el-button type="primary" size="large" :loading="submitting" @click="handleSubmit">
            提交订单
          </el-button>
        </div>
      </div>
      <div v-else>
        <EmptyState message="购物车是空的，无法结算" />
        <div class="empty-action">
          <el-button type="primary" @click="router.push('/')">去逛逛</el-button>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { createOrder } from '@/api/orders'
import AppHeader from '@/components/AppHeader.vue'
import EmptyState from '@/components/EmptyState.vue'
import { useCartStore } from '@/store/cart'

const router = useRouter()
const cartStore = useCartStore()
const submitting = ref(false)
const form = reactive({ receiver_name: '', receiver_phone: '', receiver_address: '' })

async function handleSubmit() {
  if (!form.receiver_name.trim() || !form.receiver_phone.trim() || !form.receiver_address.trim()) {
    ElMessage.warning('请完整填写收货信息')
    return
  }
  submitting.value = true
  try {
    const { data } = await createOrder({
      receiver_name: form.receiver_name.trim(),
      receiver_phone: form.receiver_phone.trim(),
      receiver_address: form.receiver_address.trim(),
    })
    await cartStore.fetchCart() // 下单后购物车已被清空，同步前端状态
    ElMessage.success('下单成功')
    router.push(`/orders/${data.id}/pay`)
  } finally {
    submitting.value = false
  }
}
</script>

<style scoped>
.checkout-content {
  max-width: 1100px;
  margin: 0 auto;
  padding: 20px;
}

.page-title {
  margin: 0 0 16px;
}

.cart-product {
  display: flex;
  align-items: center;
  gap: 12px;
}

.cart-img {
  width: 56px;
  height: 56px;
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

.receiver-form {
  margin-top: 20px;
  max-width: 520px;
}

.checkout-footer {
  display: flex;
  justify-content: flex-end;
  align-items: center;
  gap: 16px;
  margin-top: 20px;
}

.total-price {
  color: #d4380d;
  font-size: 22px;
}

.empty-action {
  margin-top: 16px;
}
</style>
