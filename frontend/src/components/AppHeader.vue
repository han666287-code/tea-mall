<template>
  <header class="app-header">
    <div class="header-inner">
      <router-link to="/" class="logo">茶叶商城</router-link>
      <el-input
        v-model="keyword"
        class="header-search"
        placeholder="搜索茶叶..."
        clearable
        @keyup.enter="handleSearch"
      />
      <nav class="header-nav">
        <router-link to="/products">全部商品</router-link>
        <template v-if="authStore.user?.role === 'admin'">
          <router-link to="/admin/categories">分类管理</router-link>
          <router-link to="/admin/products">商品管理</router-link>
        </template>
        <span v-if="authStore.user" class="header-user">
          {{ authStore.user.nickname || authStore.user.username }}
        </span>
        <el-button v-if="authStore.user" size="small" @click="handleLogout">退出</el-button>
      </nav>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'

import { useAuthStore } from '@/store/auth'

const router = useRouter()
const authStore = useAuthStore()
const keyword = ref('')

function handleSearch() {
  const kw = keyword.value.trim()
  router.push(kw ? { path: '/products', query: { keyword: kw } } : '/products')
}

function handleLogout() {
  authStore.logout()
  router.push('/login')
}
</script>

<style scoped>
.app-header {
  background: #fff;
  border-bottom: 1px solid #ebeef5;
}

.header-inner {
  max-width: 1100px;
  margin: 0 auto;
  padding: 12px 20px;
  display: flex;
  align-items: center;
  gap: 16px;
}

.logo {
  font-size: 20px;
  font-weight: 700;
  color: #b8860b;
  text-decoration: none;
  white-space: nowrap;
}

.header-search {
  flex: 1;
  max-width: 360px;
}

.header-nav {
  display: flex;
  align-items: center;
  gap: 14px;
}

.header-nav a {
  color: #333;
  text-decoration: none;
  font-size: 14px;
}

.header-nav a.router-link-active {
  color: #b8860b;
  font-weight: 600;
}

.header-user {
  font-size: 14px;
  color: #666;
}
</style>
