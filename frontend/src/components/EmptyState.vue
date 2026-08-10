<template>
  <el-empty :description="message" />
</template>

<script setup lang="ts">
withDefaults(defineProps<{ message?: string }>(), { message: '暂无数据' })
</script>
