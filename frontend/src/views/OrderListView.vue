<template>
  <div class="orders-page">
    <AppHeader />
    <div class="orders-content">
      <h2 class="page-title">我的订单</h2>
      <el-table v-if="orders.length" :data="orders" border stripe>
        <el-table-column prop="order_no" label="订单号" min-width="190" />
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="ORDER_STATUS_TAG[row.status as OrderStatus]">
              {{ ORDER_STATUS_TEXT[row.status as OrderStatus] }}
            </el-tag>
          </template>
        </el-table-column>
        <el-table-column label="金额" width="120">
          <template #default="{ row }">¥{{ Number(row.total_amount).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="created_at" label="下单时间" min-width="160" />
        <el-table-column label="操作" width="220">
          <template #default="{ row }">
            <el-button size="small" @click="router.push(`/orders/${row.id}`)">详情</el-button>
            <el-button
              v-if="row.status === 'pending'"
              size="small"
              type="primary"
              @click="router.push(`/orders/${row.id}/pay`)"
            >
              去支付
            </el-button>
            <el-button
              v-if="row.status === 'pending'"
              size="small"
              type="danger"
              @click="handleCancel(row)"
            >
              取消
            </el-button>
          </template>
        </el-table-column>
      </el-table>
      <EmptyState v-else message="还没有订单，去逛逛吧" />
      <PaginationBar
        :total="total"
        :page="page"
        :page-size="pageSize"
        @update:page="onPageChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { cancelOrder, getOrders } from '@/api/orders'
import AppHeader from '@/components/AppHeader.vue'
import EmptyState from '@/components/EmptyState.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import { ORDER_STATUS_TAG, ORDER_STATUS_TEXT, type Order, type OrderStatus } from '@/types/order'

const router = useRouter()
const orders = ref<Order[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 10

async function load() {
  const { data } = await getOrders(page.value, pageSize)
  orders.value = data.items
  total.value = data.total
}

function onPageChange(newPage: number) {
  page.value = newPage
  load()
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
.orders-content {
  max-width: 1100px;
  margin: 0 auto;
  padding: 20px;
}

.page-title {
  margin: 0 0 16px;
}
</style>
