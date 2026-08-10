<template>
  <div class="cashier-page">
    <AppHeader />
    <div class="tea-page cashier-body">
      <div class="page-head">
        <p class="page-eyebrow">CHECKOUT</p>
        <h1 class="page-title">收银台</h1>
      </div>
      <div v-if="order" class="cashier-card">
        <div class="pay-amount">
          <span class="pay-label">应付金额</span>
          <div class="pay-value">¥{{ Number(order.total_amount).toFixed(2) }}</div>
        </div>
        <div class="pay-info">
          <div class="pay-row"><span>订单号</span><b>{{ order.order_no }}</b></div>
          <div class="pay-row">
            <span>下单时间</span>
            <b>{{ formatTime(order.created_at) }}</b>
          </div>
          <div class="pay-row">
            <span>收货人</span>
            <b>{{ order.receiver_name }} / {{ order.receiver_phone }}</b>
          </div>
          <div class="pay-row">
            <span>收货地址</span>
            <b>{{ order.receiver_address }}</b>
          </div>
        </div>
        <div v-if="order.status === 'pending'" class="cashier-actions">
          <el-button size="large" @click="handleCancel">取消订单</el-button>
          <el-button type="primary" size="large" :loading="paying" @click="handlePay">
            确认支付
          </el-button>
        </div>
        <el-alert v-else type="info" :closable="false" show-icon>
          该订单当前状态为「{{ ORDER_STATUS_TEXT[order.status] }}」，无需支付
        </el-alert>
      </div>
      <EmptyState v-else-if="notFound" message="订单不存在" />
    </div>
    <AppFooter />
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

function formatTime(value: string) {
  const date = new Date(value.replace(' ', 'T'))
  if (Number.isNaN(date.getTime())) return value
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

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
.cashier-body {
  padding-top: 40px;
  padding-bottom: 24px;
  max-width: 720px;
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

.cashier-card {
  background: var(--tea-surface);
  border: 1px solid var(--tea-line-soft);
  border-radius: var(--tea-radius-lg);
  box-shadow: var(--tea-shadow-sm);
  padding: 34px;
}

.pay-amount {
  padding: 26px;
  margin-bottom: 22px;
  text-align: center;
  border-radius: var(--tea-radius);
  background:
    radial-gradient(420px 160px at 50% -30%, rgba(169, 126, 58, 0.2), transparent 70%),
    linear-gradient(135deg, #1c3a2a, #2f5e43);
  color: #f6f2ea;
}

.pay-label {
  display: block;
  font-size: 13px;
  letter-spacing: 0.3em;
  color: rgba(246, 242, 234, 0.7);
}

.pay-value {
  margin-top: 10px;
  font-family: var(--tea-font-sans);
  font-variant-numeric: tabular-nums;
  font-size: 40px;
  font-weight: 700;
  color: #d9b877;
}

.pay-info {
  display: flex;
  flex-direction: column;
  gap: 12px;
  padding: 20px 22px;
  border: 1px solid var(--tea-line-soft);
  border-radius: var(--tea-radius);
  background: #fbf8f1;
  margin-bottom: 24px;
}

.pay-row {
  display: flex;
  justify-content: space-between;
  gap: 20px;
  font-size: 14px;
  line-height: 1.6;
}

.pay-row span {
  color: var(--tea-muted);
  white-space: nowrap;
}

.pay-row b {
  color: var(--tea-ink);
  text-align: right;
  font-weight: 500;
}

.cashier-actions {
  display: flex;
  justify-content: flex-end;
  gap: 14px;
}

.cashier-actions .el-button {
  min-width: 130px;
  letter-spacing: 0.12em;
}

@media (max-width: 560px) {
  .pay-row {
    flex-direction: column;
    gap: 4px;
  }

  .pay-row b {
    text-align: left;
  }

  .cashier-actions {
    flex-direction: column-reverse;
  }
}
</style>
