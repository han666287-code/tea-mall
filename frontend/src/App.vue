<template>
  <div class="app">
    <main class="app-main">
      <router-view v-slot="{ Component }">
        <transition name="tea-fade" mode="out-in">
          <component :is="Component" />
        </transition>
      </router-view>
    </main>
  </div>
</template>

<script setup lang="ts">
import { onMounted } from 'vue'

import { useAuthStore } from '@/store/auth'
import { useCartStore } from '@/store/cart'

const authStore = useAuthStore()
const cartStore = useCartStore()

onMounted(() => {
  // 刷新页面后恢复购物车数据
  if (authStore.token) {
    cartStore.fetchCart()
  }
})
</script>

<style scoped>
.app {
  min-height: 100vh;
  background: var(--tea-bg);
}

.app-main {
  min-height: 100vh;
}
</style>
