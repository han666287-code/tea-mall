<template>
  <svg
    class="tea-mark"
    :style="{ width: `${size}px`, height: `${size}px` }"
    viewBox="0 0 48 48"
    fill="none"
    aria-hidden="true"
  >
    <path
      d="M24 5.5c-1.2 6.4-5.8 11.6-10.4 15.2C9 24.6 7 28.9 7 33.5c0 7.5 7.6 9.5 17 9.5s17-2 17-9.5c0-4.6-2-8.9-6.6-12.8C29.8 17.1 25.2 11.9 24 5.5Z"
      fill="currentColor"
      opacity="0.9"
    />
    <path
      d="M24 7v35"
      stroke="#fff"
      stroke-opacity="0.75"
      stroke-width="2.4"
      stroke-linecap="round"
    />
    <path
      d="M24 16.5c-3.6 3.4-6.4 8.2-7.2 14"
      stroke="#fff"
      stroke-opacity="0.6"
      stroke-width="2"
      stroke-linecap="round"
    />
    <path
      d="M24 16.5c3.6 3.4 6.4 8.2 7.2 14"
      stroke="#fff"
      stroke-opacity="0.6"
      stroke-width="2"
      stroke-linecap="round"
    />
  </svg>
</template>

<script setup lang="ts">
withDefaults(defineProps<{ size?: number }>(), { size: 24 })
</script>
