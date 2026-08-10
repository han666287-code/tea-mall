<template>
  <div class="order-detail-page">
    <AppHeader />
    <div class="order-detail-content">
      <el-button link class="back-btn" @click="router.push('/orders')">← 返回订单列表</el-button>
      <div v-if="order" class="detail-card">
        <div class="detail-head">
          <h2 class="detail-title">订单详情</h2>
          <el-tag :type="ORDER_STATUS_TAG[order.status]">
            {{ ORDER_STATUS_TEXT[order.status] }}
          </el-tag>
        </div>
        <div class="detail-meta">
          <p>订单号：{{ order.order_no }}</p>
          <p>下单时间：{{ order.created_at }}</p>
          <p>收货人：{{ order.receiver_name }} / {{ order.receiver_phone }}</p>
          <p>收货地址：{{ order.receiver_address }}</p>
        </div>

        <el-table :data="order.items" border stripe>
          <el-table-column prop="product_name" label="商品" min-width="200" />
          <el-table-column label="单价" width="120">
            <template #default="{ row }">¥{{ Number(row.price).toFixed(2) }}</template>
          </el-table-column>
          <el-table-column prop="quantity" label="数量" width="100" />
          <el-table-column label="小计" width="130">
            <template #default="{ row }">¥{{ Number(row.subtotal).toFixed(2) }}</template>
          </el-table-column>
        </el-table>

        <div class="detail-footer">
          <span class="total">
            合计：<b class="total-price">¥{{ Number(order.total_amount).toFixed(2) }}</b>
          </span>
          <el-button
            v-if="order.status === 'pending'"
            type="primary"
            @click="router.push(`/orders/${order.id}/pay`)"
          >
            去支付
          </el-button>
        </div>
      </div>
      <EmptyState v-else-if="notFound" message="订单不存在" />
    </div>
  </div>
</template>

<script setup lang="ts">
import { onMounted, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import { getOrder } from '@/api/orders'
import AppHeader from '@/components/AppHeader.vue'
import EmptyState from '@/components/EmptyState.vue'
import { ORDER_STATUS_TAG, ORDER_STATUS_TEXT, type Order } from '@/types/order'

const route = useRoute()
const router = useRouter()
const order = ref<Order | null>(null)
const notFound = ref(false)

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
.order-detail-content {
  max-width: 900px;
  margin: 0 auto;
  padding: 20px;
}

.back-btn {
  margin-bottom: 12px;
}

.detail-card {
  background: #fff;
  padding: 24px;
  border-radius: 8px;
}

.detail-head {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 12px;
}

.detail-title {
  margin: 0;
}

.detail-meta {
  color: #666;
  line-height: 1.9;
  margin-bottom: 16px;
}

.detail-footer {
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
</style>
