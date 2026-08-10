<template>
  <div class="checkout-page">
    <AppHeader />
    <div class="tea-page checkout-body">
      <div class="page-head">
        <p class="page-eyebrow">CONFIRM ORDER</p>
        <h1 class="page-title">确认订单</h1>
      </div>
      <div v-if="cartStore.items.length" class="checkout-wrap">
        <div class="checkout-layout">
          <div class="checkout-main">
            <div class="panel">
              <h3 class="panel-title">商品清单</h3>
              <div v-for="row in cartStore.items" :key="row.id" class="item-row">
                <el-image
                  v-if="row.product.image_url"
                  :src="row.product.image_url"
                  fit="cover"
                  class="item-img"
                />
                <div v-else class="item-img item-ph">暂无图</div>
                <span class="item-name">{{ row.product.name }}</span>
                <span class="item-price">¥{{ Number(row.product.price).toFixed(2) }} × {{ row.quantity }}</span>
                <span class="item-subtotal">¥{{ (row.quantity * Number(row.product.price)).toFixed(2) }}</span>
              </div>
            </div>
            <div class="panel">
              <h3 class="panel-title">收货信息</h3>
              <el-form :model="form" label-position="top" class="receiver-form">
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
                    :rows="3"
                    placeholder="请输入收货地址"
                  />
                </el-form-item>
              </el-form>
            </div>
          </div>
          <aside class="checkout-summary">
            <h3>订单汇总</h3>
            <div class="summary-row">
              <span>商品件数</span>
              <b>{{ cartStore.totalQuantity }}</b>
            </div>
            <div class="summary-row">
              <span>应付金额</span>
              <b class="summary-total">¥{{ cartStore.totalPrice.toFixed(2) }}</b>
            </div>
            <el-button
              type="primary"
              size="large"
              class="summary-btn"
              :loading="submitting"
              @click="handleSubmit"
            >
              提交订单
            </el-button>
          </aside>
        </div>
      </div>
      <div v-else>
        <EmptyState message="购物车是空的，无法结算" />
        <div class="empty-action">
          <el-button type="primary" @click="router.push('/')">去逛逛</el-button>
        </div>
      </div>
    </div>
    <AppFooter />
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { createOrder } from '@/api/orders'
import AppFooter from '@/components/AppFooter.vue'
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
.checkout-body {
  padding-top: 40px;
  padding-bottom: 24px;
}

.page-head {
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

.checkout-layout {
  display: grid;
  grid-template-columns: 1fr 320px;
  gap: 28px;
  align-items: start;
}

.checkout-main {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.panel {
  padding: 24px;
  background: var(--tea-surface);
  border: 1px solid var(--tea-line-soft);
  border-radius: var(--tea-radius);
  box-shadow: var(--tea-shadow-sm);
}

.panel-title {
  margin: 0 0 18px;
  font-family: var(--tea-font-serif);
  font-size: 17px;
  letter-spacing: 0.1em;
  color: var(--tea-ink);
  position: relative;
  padding-left: 14px;
}

.panel-title::before {
  content: '';
  position: absolute;
  left: 0;
  top: 3px;
  bottom: 3px;
  width: 3px;
  border-radius: 3px;
  background: var(--tea-gold);
}

.item-row {
  display: grid;
  grid-template-columns: 52px 1fr 130px 100px;
  gap: 14px;
  align-items: center;
  padding: 10px 0;
}

.item-row + .item-row {
  border-top: 1px dashed var(--tea-line);
}

.item-img {
  width: 52px;
  height: 52px;
  border-radius: 8px;
  overflow: hidden;
  background: var(--tea-gold-soft);
}

.item-ph {
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  color: var(--tea-muted);
}

.item-name {
  font-size: 14px;
  color: var(--tea-ink);
  font-weight: 500;
}

.item-price {
  text-align: right;
  font-size: 13px;
  color: var(--tea-muted);
}

.item-subtotal {
  text-align: right;
  font-size: 14px;
  font-weight: 600;
  color: var(--tea-ink);
}

.receiver-form {
  margin-top: 0;
}

.checkout-summary {
  position: sticky;
  top: 92px;
  padding: 26px;
  background: var(--tea-surface);
  border: 1px solid var(--tea-line-soft);
  border-radius: var(--tea-radius);
  box-shadow: var(--tea-shadow-sm);
}

.checkout-summary h3 {
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

.empty-action {
  margin-top: 20px;
  text-align: center;
}

@media (max-width: 900px) {
  .checkout-layout {
    grid-template-columns: 1fr;
  }

  .checkout-summary {
    position: static;
  }
}

@media (max-width: 640px) {
  .item-row {
    grid-template-columns: 44px 1fr;
  }

  .item-price,
  .item-subtotal {
    grid-column: 2;
    text-align: left;
  }
}

</style>
