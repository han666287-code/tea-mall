<template>
  <div class="orders-page">
    <AppHeader />
    <div class="tea-page orders-body">
      <div class="page-head">
        <div>
          <p class="page-eyebrow">MY ORDERS</p>
          <h1 class="page-title">我的订单</h1>
        </div>
      </div>
      <div v-loading="loading">
        <div v-if="orders.length" class="order-list">
          <div v-for="order in orders" :key="order.id" class="order-card">
            <div class="order-head">
              <div class="order-no">
                <span class="no-label">订单号</span>
                <span class="no-value">{{ order.order_no }}</span>
              </div>
              <el-tag
                :type="ORDER_STATUS_TAG[order.status as OrderStatus]"
                effect="light"
                round
              >
                {{ ORDER_STATUS_TEXT[order.status as OrderStatus] }}
              </el-tag>
            </div>
            <div class="order-body">
              <div class="order-time">
                <el-icon><Clock /></el-icon>
                <span>{{ formatTime(order.created_at) }}</span>
              </div>
              <div class="order-amount">
                <span class="amount-label">实付</span>
                <b class="amount-value">¥{{ Number(order.total_amount).toFixed(2) }}</b>
              </div>
              <div class="order-actions">
                <el-button size="small" @click="router.push(`/orders/${order.id}`)">
                  查看详情
                </el-button>
                <el-button
                  v-if="order.status === 'pending'"
                  size="small"
                  type="primary"
                  @click="router.push(`/orders/${order.id}/pay`)"
                >
                  去支付
                </el-button>
                <el-button
                  v-if="order.status === 'pending'"
                  size="small"
                  plain
                  type="danger"
                  @click="handleCancel(order)"
                >
                  取消订单
                </el-button>
              </div>
            </div>
          </div>
        </div>
        <EmptyState v-else message="还没有订单，去逛逛吧" />
      </div>
      <PaginationBar
        :total="total"
        :page="page"
        :page-size="pageSize"
        @update:page="onPageChange"
      />
    </div>
    <AppFooter />
  </div>
</template>

<script setup lang="ts">
import { Clock } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { cancelOrder, getOrders } from '@/api/orders'
import AppFooter from '@/components/AppFooter.vue'
import AppHeader from '@/components/AppHeader.vue'
import EmptyState from '@/components/EmptyState.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import { ORDER_STATUS_TAG, ORDER_STATUS_TEXT, type Order, type OrderStatus } from '@/types/order'

const router = useRouter()
const orders = ref<Order[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 10
const loading = ref(false)

async function load() {
  loading.value = true
  try {
    const { data } = await getOrders(page.value, pageSize)
    orders.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function onPageChange(newPage: number) {
  page.value = newPage
  load()
}

function formatTime(value: string) {
  const date = new Date(value.replace(' ', 'T'))
  if (Number.isNaN(date.getTime())) return value
  const pad = (n: number) => String(n).padStart(2, '0')
  return `${date.getFullYear()}-${pad(date.getMonth() + 1)}-${pad(date.getDate())} ${pad(date.getHours())}:${pad(date.getMinutes())}`
}

async function handleCancel(row: Order) {
  try {
    await ElMessageBox.confirm(`确定取消订单 ${row.order_no} 吗？`, '提示', { type: 'warning' })
    await cancelOrder(row.id)
    ElMessage.success('订单已取消')
    load()
  } catch {
    // 用户取消或操作失败（提示由拦截器统一处理）
  }
}

onMounted(load)
</script>

<style scoped>
.orders-body {
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

.order-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.order-card {
  background: var(--tea-surface);
  border: 1px solid var(--tea-line-soft);
  border-radius: var(--tea-radius);
  box-shadow: var(--tea-shadow-sm);
  overflow: hidden;
  transition:
    transform 0.25s ease,
    box-shadow 0.25s ease;
}

.order-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--tea-shadow);
}

.order-head {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 22px;
  background: linear-gradient(90deg, #f7f3ea, #fbf8f1);
  border-bottom: 1px solid var(--tea-line-soft);
}

.order-no {
  display: flex;
  align-items: baseline;
  gap: 10px;
}

.no-label {
  font-size: 12px;
  color: var(--tea-muted);
}

.no-value {
  font-size: 14px;
  font-weight: 600;
  color: var(--tea-ink);
  letter-spacing: 0.04em;
}

.order-body {
  display: flex;
  align-items: center;
  gap: 28px;
  padding: 18px 22px;
}

.order-time {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  font-size: 14px;
  color: var(--tea-ink-2);
}

.order-time .el-icon {
  color: var(--tea-gold);
}

.order-amount {
  margin-left: auto;
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.amount-label {
  font-size: 13px;
  color: var(--tea-muted);
}

.amount-value {
  font-size: 20px;
  font-family: var(--tea-font-sans);
  font-variant-numeric: tabular-nums;
  color: var(--tea-price);
}

.order-actions {
  display: flex;
  gap: 8px;
}

@media (max-width: 720px) {
  .order-body {
    flex-direction: column;
    align-items: flex-start;
    gap: 14px;
  }

  .order-amount {
    margin-left: 0;
  }
}
</style>
