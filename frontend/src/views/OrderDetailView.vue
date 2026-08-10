<template>
  <div class="order-detail-page">
    <AppHeader />
    <div class="tea-page detail-body">
      <el-button link class="back-btn" @click="router.push('/orders')">
        <el-icon><ArrowLeft /></el-icon>
        返回订单列表
      </el-button>
      <div v-if="order" class="detail-card">
        <div class="status-hero">
          <div class="status-text">
            <p class="status-eyebrow">ORDER STATUS</p>
            <div class="status-line">
              <h2 class="detail-title">订单详情</h2>
              <el-tag
                :type="ORDER_STATUS_TAG[order.status]"
                effect="light"
                round
                size="large"
              >
                {{ ORDER_STATUS_TEXT[order.status] }}
              </el-tag>
            </div>
          </div>
          <div class="status-meta">
            <span>订单号 {{ order.order_no }}</span>
            <span>下单时间 {{ formatTime(order.created_at) }}</span>
          </div>
        </div>

        <el-steps
          :active="statusStep"
          align-center
          finish-status="success"
          class="order-steps"
        >
          <el-step title="提交订单" />
          <el-step title="完成支付" />
          <el-step title="等待发货" />
          <el-step title="交易完成" />
        </el-steps>

        <div class="info-grid">
          <div class="info-card">
            <h4>收货信息</h4>
            <p>{{ order.receiver_name }} · {{ order.receiver_phone }}</p>
            <p>{{ order.receiver_address }}</p>
          </div>
          <div class="info-card amount-card">
            <h4>订单金额</h4>
            <p class="amount-big">¥{{ Number(order.total_amount).toFixed(2) }}</p>
          </div>
        </div>

        <div class="items-card">
          <div class="items-head">
            <span>商品</span>
            <span>单价 × 数量</span>
            <span>小计</span>
          </div>
          <div v-for="item in order.items" :key="item.id" class="item-row">
            <span class="item-name">{{ item.product_name }}</span>
            <span class="item-price">¥{{ Number(item.price).toFixed(2) }} × {{ item.quantity }}</span>
            <span class="item-subtotal">¥{{ Number(item.subtotal).toFixed(2) }}</span>
          </div>
          <div class="items-total">
            <span>合计</span>
            <b>¥{{ Number(order.total_amount).toFixed(2) }}</b>
          </div>
        </div>

        <div v-if="order.status === 'pending'" class="detail-actions">
          <el-button type="primary" size="large" @click="router.push(`/orders/${order.id}/pay`)">
            去支付
          </el-button>
        </div>
      </div>
      <EmptyState v-else-if="notFound" message="订单不存在" />
    </div>
    <AppFooter />
  </div>
</template>

<script setup lang="ts">
import { ArrowLeft } from '@element-plus/icons-vue'
import { computed, onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { getOrder } from '@/api/orders'
import AppFooter from '@/components/AppFooter.vue'
import AppHeader from '@/components/AppHeader.vue'
import EmptyState from '@/components/EmptyState.vue'
import { ORDER_STATUS_TAG, ORDER_STATUS_TEXT, type Order } from '@/types/order'

const route = useRoute()
const router = useRouter()
const order = ref<Order | null>(null)
const notFound = ref(false)

const statusStep = computed(() => {
  if (!order.value) return 0
  const steps: Record<string, number> = {
    pending: 0,
    paid: 1,
    shipped: 2,
    completed: 3,
    cancelled: 0,
  }
  return steps[order.value.status] ?? 0
})

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
</script>

<style scoped>
.detail-body {
  padding-top: 28px;
  padding-bottom: 24px;
  max-width: 960px;
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
  background: var(--tea-surface);
  border: 1px solid var(--tea-line-soft);
  border-radius: var(--tea-radius-lg);
  box-shadow: var(--tea-shadow-sm);
  padding: 32px;
}

.status-hero {
  display: flex;
  align-items: flex-start;
  justify-content: space-between;
  gap: 20px;
  padding-bottom: 24px;
  border-bottom: 1px solid var(--tea-line-soft);
}

.status-eyebrow {
  margin: 0 0 10px;
  font-size: 12px;
  letter-spacing: 0.4em;
  color: var(--tea-gold);
}

.status-line {
  display: flex;
  align-items: center;
  gap: 14px;
}

.detail-title {
  margin: 0;
  font-family: var(--tea-font-serif);
  font-size: 26px;
  letter-spacing: 0.08em;
  color: var(--tea-ink);
}

.status-meta {
  display: flex;
  flex-direction: column;
  align-items: flex-end;
  gap: 8px;
  font-size: 13px;
  color: var(--tea-muted);
}

.order-steps {
  margin: 30px 0;
}

.info-grid {
  display: grid;
  grid-template-columns: 2fr 1fr;
  gap: 16px;
}

.info-card {
  padding: 20px 22px;
  border: 1px solid var(--tea-line-soft);
  border-radius: var(--tea-radius);
  background: #fbf8f1;
}

.info-card h4 {
  margin: 0 0 12px;
  font-size: 14px;
  letter-spacing: 0.14em;
  color: var(--tea-gold-deep);
}

.info-card p {
  margin: 6px 0;
  font-size: 14px;
  line-height: 1.7;
  color: var(--tea-ink-2);
}

.amount-card {
  display: flex;
  flex-direction: column;
  justify-content: center;
}

.amount-big {
  font-family: var(--tea-font-sans);
  font-variant-numeric: tabular-nums;
  font-size: 26px;
  font-weight: 700;
  color: var(--tea-price) !important;
}

.items-card {
  margin-top: 16px;
  border: 1px solid var(--tea-line-soft);
  border-radius: var(--tea-radius);
  overflow: hidden;
}

.items-head {
  display: grid;
  grid-template-columns: 1fr 180px 120px;
  gap: 12px;
  padding: 12px 20px;
  font-size: 13px;
  font-weight: 600;
  color: var(--tea-muted);
  background: #f7f3ea;
}

.items-head span:nth-child(2),
.items-head span:nth-child(3) {
  text-align: right;
}

.item-row {
  display: grid;
  grid-template-columns: 1fr 180px 120px;
  gap: 12px;
  align-items: center;
  padding: 14px 20px;
  border-top: 1px solid var(--tea-line-soft);
  font-size: 14px;
  color: var(--tea-ink-2);
}

.item-name {
  font-weight: 500;
  color: var(--tea-ink);
}

.item-price,
.item-subtotal {
  text-align: right;
}

.items-total {
  display: flex;
  justify-content: flex-end;
  align-items: baseline;
  gap: 14px;
  padding: 16px 20px;
  border-top: 1px dashed var(--tea-line);
  font-size: 14px;
  color: var(--tea-muted);
}

.items-total b {
  font-family: var(--tea-font-sans);
  font-variant-numeric: tabular-nums;
  font-size: 22px;
  color: var(--tea-price);
}

.detail-actions {
  display: flex;
  justify-content: flex-end;
  margin-top: 22px;
}

@media (max-width: 720px) {
  .status-hero {
    flex-direction: column;
  }

  .status-meta {
    align-items: flex-start;
  }

  .info-grid {
    grid-template-columns: 1fr;
  }

  .items-head,
  .item-row {
    grid-template-columns: 1fr;
  }

  .items-head span:nth-child(2),
  .items-head span:nth-child(3),
  .item-price,
  .item-subtotal {
    text-align: left;
  }
}
</style>
