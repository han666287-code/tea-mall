<template>
  <div class="admin-page">
    <AppHeader />
    <div class="admin-content">
      <div class="admin-header">
        <h2>订单管理</h2>
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

      <el-table :data="orders" border stripe>
        <el-table-column prop="order_no" label="订单号" min-width="190" />
        <el-table-column prop="username" label="买家" width="120" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="ORDER_STATUS_TAG[row.status as OrderStatus]">
              {{ ORDER_STATUS_TEXT[row.status as OrderStatus] }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="金额" width="110">
          <template #default="{ row }">¥{{ Number(row.total_amount).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="created_at" label="下单时间" min-width="160" />
        <el-table-column label="操作" width="280">
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

      <el-dialog v-model="detailVisible" title="订单详情" width="640px">
        <template v-if="detailOrder">
          <p>订单号：{{ detailOrder.order_no }}｜买家：{{ detailOrder.username }}</p>
          <p>
            收货人：{{ detailOrder.receiver_name }} / {{ detailOrder.receiver_phone }}｜
            {{ detailOrder.receiver_address }}
          </p>
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
  </div>
</template>

<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, ref } from 'vue'

import { getAdminOrders, updateOrderStatus } from '@/api/admin'
import AppHeader from '@/components/AppHeader.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import { ORDER_STATUS_TAG, ORDER_STATUS_TEXT, type Order, type OrderStatus } from '@/types/order'

const orders = ref<Order[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 10
const statusFilter = ref('')
const detailVisible = ref(false)
const detailOrder = ref<Order | null>(null)

async function load() {
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
}

function onStatusChange() {
  page.value = 1
  load()
}

function onPageChange(newPage: number) {
  page.value = newPage
  load()
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
.admin-content {
  max-width: 1100px;
  margin: 0 auto;
  padding: 20px;
}

.admin-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.admin-header h2 {
  margin: 0;
}

.detail-total {
  text-align: right;
  margin-top: 12px;
}

.detail-amount {
  color: #d4380d;
  font-size: 20px;
}
</style>
