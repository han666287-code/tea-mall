<template>
  <div v-if="total > 0" class="pagination-bar">
    <el-pagination
      background
      layout="prev, pager, next, total"
      :total="total"
      :page-size="pageSize"
      :current-page="page"
      @current-change="handleChange"
    />
  </div>
</template>

<script setup lang="ts">
defineProps<{ total: number; page: number; pageSize: number }>()

const emit = defineEmits<{ (e: 'update:page', page: number): void }>()

function handleChange(page: number) {
  emit('update:page', page)
}
</script>

<style scoped>
.pagination-bar {
  display: flex;
  justify-content: center;
  margin-top: 36px;
}
</style>
