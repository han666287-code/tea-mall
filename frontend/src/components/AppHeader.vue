<template>
  <header class="app-header" :class="{ 'is-scrolled': scrolled }">
    <div class="tea-page header-inner">
      <router-link to="/" class="brand" aria-label="茶叶商城首页">
        <span class="brand-mark"><TeaMark :size="26" /></span>
        <span class="brand-text">
          <span class="brand-name">茶叶商城</span>
          <span class="brand-en">TEAMALL</span>
        </span>
      </router-link>

      <div class="header-search">
        <el-input
          v-model="keyword"
          placeholder="搜索茶叶..."
          clearable
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <el-icon><Search /></el-icon>
          </template>
        </el-input>
      </div>

      <nav class="header-nav">
        <router-link to="/products" class="nav-link">全部好茶</router-link>
        <router-link to="/cart" class="nav-link">
          <el-badge :value="cartStore.totalQuantity" :hidden="cartStore.totalQuantity === 0" :max="99">
            <el-icon :size="17"><ShoppingCart /></el-icon>
          </el-badge>
          <span>购物车</span>
        </router-link>
        <router-link v-if="authStore.user" to="/orders" class="nav-link">我的订单</router-link>
        <template v-if="authStore.user?.role === 'admin'">
          <router-link to="/admin/categories" class="nav-link">分类管理</router-link>
          <router-link to="/admin/products" class="nav-link">商品管理</router-link>
          <router-link to="/admin/orders" class="nav-link">订单管理</router-link>
        </template>

        <template v-if="!authStore.user">
          <router-link to="/login" class="nav-link">登录</router-link>
          <router-link to="/register" class="nav-cta">注册</router-link>
        </template>

        <el-dropdown v-else trigger="click">
          <span class="user-chip">
            <span class="user-avatar">{{ initial }}</span>
            <span class="user-name">{{ authStore.user.nickname || authStore.user.username }}</span>
            <el-icon class="user-arrow"><ArrowDown /></el-icon>
          </span>
          <template #dropdown>
            <el-dropdown-menu>
              <el-dropdown-item @click="router.push('/orders')">我的订单</el-dropdown-item>
              <el-dropdown-item divided @click="handleLogout">退出登录</el-dropdown-item>
            </el-dropdown-menu>
          </template>
        </el-dropdown>
      </nav>
    </div>
  </header>
</template>

<script setup lang="ts">
import { ArrowDown, Search, ShoppingCart } from '@element-plus/icons-vue'
import { computed, onBeforeUnmount, onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import TeaMark from '@/components/TeaMark.vue'
import { useAuthStore } from '@/store/auth'
import { useCartStore } from '@/store/cart'

const router = useRouter()
const authStore = useAuthStore()
const cartStore = useCartStore()
const keyword = ref('')
const scrolled = ref(false)

const initial = computed(() => {
  const name = authStore.user?.nickname || authStore.user?.username || ''
  return name ? name.charAt(0).toUpperCase() : '茶'
})

function onScroll() {
  scrolled.value = window.scrollY > 8
}

function handleSearch() {
  const kw = keyword.value.trim()
  router.push(kw ? { path: '/products', query: { keyword: kw } } : '/products')
}

function handleLogout() {
  authStore.logout()
  cartStore.clear()
  router.push('/login')
}

onMounted(() => {
  window.addEventListener('scroll', onScroll, { passive: true })
  onScroll()
})

onBeforeUnmount(() => {
  window.removeEventListener('scroll', onScroll)
})
</script>

<style scoped>
.app-header {
  position: sticky;
  top: 0;
  z-index: 100;
  background: rgba(246, 242, 234, 0.86);
  backdrop-filter: blur(14px);
  -webkit-backdrop-filter: blur(14px);
  border-bottom: 1px solid transparent;
  transition:
    border-color 0.3s ease,
    box-shadow 0.3s ease;
}

.app-header.is-scrolled {
  border-bottom-color: var(--tea-line-soft);
  box-shadow: 0 6px 24px rgba(58, 66, 46, 0.08);
}

.header-inner {
  height: 72px;
  display: flex;
  align-items: center;
  gap: 28px;
}

.brand {
  display: flex;
  align-items: center;
  gap: 12px;
  text-decoration: none;
  color: var(--tea-ink);
  white-space: nowrap;
}

.brand-mark {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--tea-primary), var(--tea-primary-deep));
  color: #fff;
  box-shadow: 0 8px 18px rgba(47, 94, 67, 0.32);
}

.brand-name {
  font-family: var(--tea-font-serif);
  font-size: 21px;
  font-weight: 700;
  letter-spacing: 0.12em;
  line-height: 1.1;
}

.brand-en {
  display: block;
  margin-top: 2px;
  font-size: 10px;
  letter-spacing: 0.42em;
  color: var(--tea-gold);
}

.header-search {
  flex: 1;
  max-width: 380px;
  margin-left: auto;
}

.header-search :deep(.el-input__wrapper) {
  background: rgba(255, 255, 255, 0.78);
}

.header-nav {
  display: flex;
  align-items: center;
  gap: 6px;
}

.nav-link {
  position: relative;
  display: inline-flex;
  align-items: center;
  gap: 6px;
  padding: 9px 13px;
  color: var(--tea-ink-2);
  text-decoration: none;
  font-size: 14px;
  border-radius: 8px;
  white-space: nowrap;
  transition:
    color 0.2s ease,
    background 0.2s ease;
}

.nav-link::after {
  content: '';
  position: absolute;
  left: 13px;
  right: 13px;
  bottom: 3px;
  height: 2px;
  border-radius: 2px;
  background: var(--tea-gold);
  transform: scaleX(0);
  transform-origin: left;
  transition: transform 0.25s ease;
}

.nav-link:hover {
  color: var(--tea-primary);
  background: rgba(47, 94, 67, 0.06);
}

.nav-link:hover::after,
.nav-link.router-link-active::after {
  transform: scaleX(1);
}

.nav-link.router-link-active {
  color: var(--tea-primary);
  font-weight: 600;
}

.nav-cta {
  margin-left: 8px;
  padding: 10px 24px;
  border-radius: 999px;
  background: linear-gradient(135deg, var(--tea-primary), var(--tea-primary-deep));
  color: #fff;
  text-decoration: none;
  font-size: 14px;
  font-weight: 500;
  white-space: nowrap;
  box-shadow: 0 6px 16px rgba(47, 94, 67, 0.28);
  transition:
    transform 0.2s ease,
    box-shadow 0.2s ease;
}

.nav-cta:hover {
  transform: translateY(-1px);
  box-shadow: 0 10px 22px rgba(47, 94, 67, 0.34);
}

.user-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px 6px 6px;
  border-radius: 999px;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.7);
  border: 1px solid var(--tea-line-soft);
  transition:
    border-color 0.2s ease,
    box-shadow 0.2s ease;
}

.user-chip:hover {
  border-color: var(--tea-gold);
  box-shadow: 0 4px 14px rgba(169, 126, 58, 0.14);
}

.user-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--tea-gold), var(--tea-gold-deep));
  color: #fff;
  font-size: 13px;
  font-weight: 600;
  display: flex;
  align-items: center;
  justify-content: center;
}

.user-name {
  font-size: 14px;
  color: var(--tea-ink);
  max-width: 120px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.user-arrow {
  color: var(--tea-muted);
  font-size: 12px;
}

@media (max-width: 1100px) {
  .header-search {
    max-width: 240px;
  }

  .brand-en {
    display: none;
  }
}

@media (max-width: 900px) {
  .header-search {
    display: none;
  }

  .header-inner {
    gap: 12px;
  }

  .header-nav {
    margin-left: auto;
    overflow-x: auto;
  }
}
</style>
