<template>
  <div class="cashier-page">
    <AppHeader />
    <div class="cashier-content">
      <h2 class="page-title">收银台</h2>
      <div v-if="order" class="cashier-card">
        <div class="cashier-info">
          <p>订单号：{{ order.order_no }}</p>
          <p>下单时间：{{ order.created_at }}</p>
          <p>收货人：{{ order.receiver_name }} / {{ order.receiver_phone }}</p>
          <p>收货地址：{{ order.receiver_address }}</p>
          <p>
            应付金额：<b class="amount">¥{{ Number(order.total_amount).toFixed(2) }}</b>
          </p>
        </div>
        <div v-if="order.status === 'pending'" class="cashier-actions">
          <el-button type="primary" size="large" :loading="paying" @click="handlePay">
            确认支付
          </el-button>
          <el-button size="large" @click="handleCancel">取消订单</el-button>
        </div>
        <el-alert v-else type="info" :closable="false" show-icon>
          该订单当前状态为「{{ ORDER_STATUS_TEXT[order.status] }}」，无需支付
        </el-alert>
      </div>
      <EmptyState v-else-if="notFound" message="订单不存在" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ElMessage } from 'element-plus'
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { cancelOrder, getOrder, payOrder } from '@/api/orders'
import AppHeader from '@/components/AppHeader.vue'
import EmptyState from '@/components/EmptyState.vue'
import { ORDER_STATUS_TEXT, type Order } from '@/types/order'

const route = useRoute()
const router = useRouter()
const order = ref<Order | null>(null)
const notFound = ref(false)
const paying = ref(false)

onMounted(async () => {
  try {
    const { data } = await getOrder(Number(route.params.id))
    order.value = data
  } catch {
    notFound.value = true
  }
})

async function handlePay() {
  if (!order.value) return
  paying.value = true
  try {
    await payOrder(order.value.id)
    ElMessage.success('支付成功')
    router.push(`/orders/${order.value.id}`)
  } finally {
    paying.value = false
  }
}

async function handleCancel() {
  if (!order.value) return
  await cancelOrder(order.value.id)
  ElMessage.success('订单已取消')
  router.push('/orders')
}
</script>

<style scoped>
.cashier-content {
  max-width: 700px;
  margin: 0 auto;
  padding: 20px;
}

.page-title {
  margin: 0 0 16px;
}

.cashier-card {
  background: #fff;
  padding: 24px;
  border-radius: 8px;
}

.cashier-info {
  color: #333;
  line-height: 2;
  margin-bottom: 20px;
}

.amount {
  color: #d4380d;
  font-size: 26px;
}

.cashier-actions {
  display: flex;
  gap: 12px;
  justify-content: flex-end;
}
</style>
