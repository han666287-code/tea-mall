<template>
  <div class="empty-state">
    <el-empty :description="message">
      <template #image>
        <svg viewBox="0 0 96 96" fill="none" aria-hidden="true">
          <circle cx="48" cy="48" r="42" stroke="#e7e0d1" stroke-width="2" stroke-dasharray="4 8" />
          <path
            d="M48 24c-4 10-14 18-20 23-6 5-8 10-8 15 0 8 12 10 28 10s28-2 28-10c0-5-2-10-8-15-6-5-16-13-20-23Z"
            fill="#d9d2c0"
          />
          <path d="M48 27v35" stroke="#fff" stroke-width="3" stroke-linecap="round" />
          <path d="M48 36c-4 3-7 8-8 13M48 36c4 3 7 8 8 13" stroke="#fff" stroke-width="2.4" stroke-linecap="round" stroke-opacity="0.7" />
        </svg>
      </template>
    </el-empty>
  </div>
</template>

<script setup lang="ts">
withDefaults(defineProps<{ message?: string }>(), { message: '暂无数据' })
</script>

<style scoped>
.empty-state {
  padding: 40px 0;
}

.empty-state :deep(.el-empty__image) {
  width: 120px;
}

.empty-state :deep(.el-empty__description p) {
  color: var(--tea-muted);
  font-size: 14px;
}
</style>
