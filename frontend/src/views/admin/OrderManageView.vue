<template>
  <div class="order-manage">
    <div class="page-head">
      <div>
        <h1 class="page-title">订单管理</h1>
        <p class="page-sub">查看全部订单并按状态流转处理</p>
      </div>
      <el-select
        v-model="statusFilter"
        placeholder="全部状态"
        clearable
        style="width: 160px"
        @change="onStatusChange"
      >
        <el-option label="待支付" value="pending" />
        <el-option label="已支付" value="paid" />
        <el-option label="已发货" value="shipped" />
        <el-option label="已完成" value="completed" />
        <el-option label="已取消" value="cancelled" />
      </el-select>
    </div>

    <div class="stats-grid">
      <div
        v-for="stat in stats"
        :key="stat.label"
        class="stat-card"
        :style="{ '--stat-color': stat.color }"
      >
        <span class="stat-label">{{ stat.label }}</span>
        <b class="stat-value">{{ stat.value }}</b>
      </div>
    </div>

    <div class="panel">
      <div class="panel-toolbar">
        <span class="panel-count">本页统计（按当前列表）</span>
      </div>
      <el-table v-loading="loading" :data="orders" class="admin-table">
        <el-table-column prop="order_no" label="订单号" min-width="180" />
        <el-table-column prop="username" label="买家" width="110" />
        <el-table-column label="状态" width="110">
          <template #default="{ row }">
            <el-tag :type="ORDER_STATUS_TAG[row.status as OrderStatus]" effect="light" round>
              {{ ORDER_STATUS_TEXT[row.status as OrderStatus] }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="金额" width="110">
          <template #default="{ row }">
            <span class="price-cell">¥{{ Number(row.total_amount).toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="下单时间" min-width="160">
          <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
        </el-table-column>
        <el-table-column label="操作" width="300" align="right">
          <template #default="{ row }">
            <el-button size="small" @click="showDetail(row)">详情</el-button>
            <el-button
              v-if="row.status === 'pending'"
              size="small"
              type="success"
              @click="updateStatus(row, 'paid')"
            >
              标记已支付
            </el-button>
            <el-button
              v-if="row.status === 'pending' || row.status === 'paid'"
              size="small"
              type="danger"
              plain
              @click="updateStatus(row, 'cancelled')"
            >
              取消
            </el-button>
            <el-button
              v-if="row.status === 'paid'"
              size="small"
              type="primary"
              @click="updateStatus(row, 'shipped')"
            >
              发货
            </el-button>
            <el-button
              v-if="row.status === 'shipped'"
              size="small"
              type="success"
              @click="updateStatus(row, 'completed')"
            >
              完成
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <PaginationBar
        :total="total"
        :page="page"
        :page-size="pageSize"
        @update:page="onPageChange"
      />
    </div>

    <el-dialog v-model="detailVisible" title="订单详情" width="640px" align-center>
      <template v-if="detailOrder">
        <div class="detail-info">
          <p>订单号：{{ detailOrder.order_no }}｜买家：{{ detailOrder.username }}</p>
          <p>
            收货人：{{ detailOrder.receiver_name }} / {{ detailOrder.receiver_phone }}｜
            {{ detailOrder.receiver_address }}
          </p>
        </div>
        <el-table :data="detailOrder.items" border size="small">
          <el-table-column prop="product_name" label="商品" min-width="180" />
          <el-table-column label="单价" width="110">
            <template #default="{ row }">¥{{ Number(row.price).toFixed(2) }}</template>
          </el-table-column>
          <el-table-column prop="quantity" label="数量" width="80" />
          <el-table-column label="小计" width="110">
            <template #default="{ row }">¥{{ Number(row.subtotal).toFixed(2) }}</template>
          </el-table-column>
        </el-table>
        <p class="detail-total">
          合计：<b class="detail-amount">¥{{ Number(detailOrder.total_amount).toFixed(2) }}</b>
        </p>
      </template>
    </el-dialog>
  </div>
</template>

<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import { computed, onMounted, ref } from 'vue'

import { getAdminOrders, updateOrderStatus } from '@/api/admin'
import PaginationBar from '@/components/PaginationBar.vue'
import { ORDER_STATUS_TAG, ORDER_STATUS_TEXT, type Order, type OrderStatus } from '@/types/order'

const orders = ref<Order[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 10
const statusFilter = ref('')
const detailVisible = ref(false)
const detailOrder = ref<Order | null>(null)
const loading = ref(false)

const stats = computed(() => {
  const count = (status: OrderStatus) =>
    orders.value.filter((order) => order.status === status).length
  return [
    { label: '全部订单', value: orders.value.length, color: '#2f5e43' },
    { label: '待支付', value: count('pending'), color: '#b98a3f' },
    { label: '已支付', value: count('paid'), color: '#4e7a55' },
    { label: '已发货', value: count('shipped'), color: '#5f8269' },
    { label: '已完成', value: count('completed'), color: '#2f5e43' },
    { label: '已取消', value: count('cancelled'), color: '#b0452f' },
  ]
})

async function load() {
  loading.value = true
  try {
    const params: { status?: string; page?: number; page_size?: number } = {
      page: page.value,
      page_size: pageSize,
    }
    if (statusFilter.value) {
      params.status = statusFilter.value
    }
    const { data } = await getAdminOrders(params)
    orders.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function onStatusChange() {
  page.value = 1
  load()
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

function showDetail(row: Order) {
  detailOrder.value = row
  detailVisible.value = true
}

async function updateStatus(row: Order, status: OrderStatus) {
  const actionText: Record<string, string> = {
    paid: '标记为已支付',
    shipped: '发货',
    completed: '标记为已完成',
    cancelled: '取消该订单',
  }
  try {
    await ElMessageBox.confirm(
      `确定对订单 ${row.order_no} 执行「${actionText[status]}」吗？`,
      '提示',
      { type: 'warning' },
    )
    await updateOrderStatus(row.id, status)
    ElMessage.success('操作成功')
    load()
  } catch {
    // 用户取消或操作失败（失败提示由拦截器统一处理）
  }
}

onMounted(load)
</script>

<style scoped>
.page-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 24px;
}

.page-title {
  margin: 0;
  font-family: var(--tea-font-serif);
  font-size: 26px;
  letter-spacing: 0.08em;
  color: var(--tea-ink);
}

.page-sub {
  margin: 8px 0 0;
  font-size: 13px;
  color: var(--tea-muted);
}

.stats-grid {
  display: grid;
  grid-template-columns: repeat(6, 1fr);
  gap: 14px;
  margin-bottom: 22px;
}

.stat-card {
  padding: 18px 20px;
  background: var(--tea-surface);
  border: 1px solid var(--tea-line-soft);
  border-radius: var(--tea-radius);
  box-shadow: var(--tea-shadow-sm);
  border-top: 3px solid var(--stat-color);
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease;
}

.stat-card:hover {
  transform: translateY(-2px);
  box-shadow: var(--tea-shadow);
}

.stat-label {
  display: block;
  font-size: 13px;
  color: var(--tea-muted);
}

.stat-value {
  display: block;
  margin-top: 8px;
  font-family: var(--tea-font-sans);
  font-size: 28px;
  line-height: 1;
  font-weight: 700;
  font-variant-numeric: tabular-nums;
  color: var(--tea-ink);
}

.panel {
  background: var(--tea-surface);
  border: 1px solid var(--tea-line-soft);
  border-radius: var(--tea-radius);
  box-shadow: var(--tea-shadow-sm);
  overflow: hidden;
}

.panel-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  border-bottom: 1px solid var(--tea-line-soft);
  background: #fbf8f1;
}

.panel-count {
  font-size: 13px;
  color: var(--tea-muted);
}

.admin-table {
  padding: 0 8px;
}

.price-cell {
  font-weight: 600;
  color: var(--tea-price);
  font-variant-numeric: tabular-nums;
}

.detail-info {
  padding: 12px 16px;
  margin-bottom: 14px;
  border: 1px solid var(--tea-line-soft);
  border-radius: 10px;
  background: #fbf8f1;
  font-size: 14px;
  line-height: 1.9;
  color: var(--tea-ink-2);
}

.detail-total {
  text-align: right;
  margin-top: 12px;
  font-size: 14px;
  color: var(--tea-muted);
}

.detail-amount {
  color: var(--tea-price);
  font-size: 20px;
  font-variant-numeric: tabular-nums;
}

@media (max-width: 1200px) {
  .stats-grid {
    grid-template-columns: repeat(3, 1fr);
  }
}

@media (max-width: 720px) {
  .stats-grid {
    grid-template-columns: repeat(2, 1fr);
  }
}
</style>
