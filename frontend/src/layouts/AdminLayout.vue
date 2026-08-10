<template>
  <div class="admin-layout">
    <aside class="admin-aside" :class="{ collapsed }">
      <router-link to="/" class="aside-brand">
        <span class="brand-mark"><TeaMark :size="24" /></span>
        <span class="brand-text">
          <span class="brand-name">茶叶商城</span>
          <span class="brand-en">ADMIN</span>
        </span>
      </router-link>

      <nav class="aside-nav">
        <router-link
          v-for="item in menuItems"
          :key="item.path"
          :to="item.path"
          class="nav-item"
          :class="{ active: route.path === item.path }"
        >
          <el-icon :size="18"><component :is="item.icon" /></el-icon>
          <span class="nav-label">{{ item.label }}</span>
        </router-link>
      </nav>

      <div class="aside-foot">
        <router-link to="/" class="nav-item">
          <el-icon :size="18"><Shop /></el-icon>
          <span class="nav-label">返回商城</span>
        </router-link>
      </div>
    </aside>

    <div class="admin-main">
      <header class="admin-topbar">
        <button class="collapse-btn" type="button" @click="collapsed = !collapsed">
          <el-icon><Expand v-if="collapsed" /><Fold v-else /></el-icon>
        </button>
        <div class="topbar-title">
          <span class="title-current">{{ currentTitle }}</span>
          <span class="title-breadcrumb">管理后台</span>
        </div>
        <div class="topbar-right">
          <el-dropdown trigger="click">
            <span class="user-chip">
              <span class="user-avatar">{{ initial }}</span>
              <span class="user-name">
                {{ authStore.user?.nickname || authStore.user?.username }}
              </span>
              <el-icon class="user-arrow"><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item @click="router.push('/')">返回商城</el-dropdown-item>
                <el-dropdown-item divided @click="handleLogout">退出登录</el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </header>

      <main class="admin-content">
        <router-view />
      </main>
    </div>
  </div>
</template>

<script setup lang="ts">
import {
  ArrowDown,
  Collection,
  Expand,
  Fold,
  Goods,
  Shop,
  Tickets,
} from '@element-plus/icons-vue'
import { computed, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import TeaMark from '@/components/TeaMark.vue'
import { useAuthStore } from '@/store/auth'
import { useCartStore } from '@/store/cart'

const route = useRoute()
const router = useRouter()
const authStore = useAuthStore()
const cartStore = useCartStore()
const collapsed = ref(false)

const menuItems = [
  { path: '/admin/products', label: '商品管理', icon: Goods },
  { path: '/admin/categories', label: '分类管理', icon: Collection },
  { path: '/admin/orders', label: '订单管理', icon: Tickets },
]

const titleMap: Record<string, string> = {
  '/admin/products': '商品管理',
  '/admin/categories': '分类管理',
  '/admin/orders': '订单管理',
}

const currentTitle = computed(() => titleMap[route.path] ?? '管理后台')

const initial = computed(() => {
  const name = authStore.user?.nickname || authStore.user?.username || ''
  return name ? name.charAt(0).toUpperCase() : '管'
})

function handleLogout() {
  authStore.logout()
  cartStore.clear()
  router.push('/login')
}
</script>

<style scoped>
.admin-layout {
  display: flex;
  min-height: 100vh;
}

.admin-aside {
  position: sticky;
  top: 0;
  height: 100vh;
  width: 232px;
  flex-shrink: 0;
  display: flex;
  flex-direction: column;
  background:
    radial-gradient(360px 240px at 15% -5%, rgba(169, 126, 58, 0.2), transparent 62%),
    linear-gradient(180deg, #1c3a2a 0%, #20382a 100%);
  color: rgba(246, 242, 234, 0.78);
  z-index: 50;
  transition: width 0.25s ease;
}

.admin-aside.collapsed {
  width: 72px;
}

.aside-brand {
  display: flex;
  align-items: center;
  gap: 12px;
  height: 72px;
  padding: 0 18px;
  text-decoration: none;
  color: #f6f2ea;
  border-bottom: 1px solid rgba(255, 255, 255, 0.08);
  white-space: nowrap;
  overflow: hidden;
}

.brand-mark {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 40px;
  height: 40px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--tea-gold), var(--tea-gold-deep));
  color: #fff;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.24);
  flex-shrink: 0;
}

.brand-name {
  font-family: var(--tea-font-serif);
  font-size: 19px;
  font-weight: 700;
  letter-spacing: 0.14em;
  line-height: 1.1;
}

.brand-en {
  display: block;
  margin-top: 2px;
  font-size: 10px;
  letter-spacing: 0.4em;
  color: #d9b877;
}

.aside-nav {
  flex: 1;
  display: flex;
  flex-direction: column;
  gap: 6px;
  padding: 20px 14px;
}

.nav-item {
  position: relative;
  display: flex;
  align-items: center;
  gap: 12px;
  padding: 12px 14px;
  border-radius: 10px;
  color: rgba(246, 242, 234, 0.75);
  text-decoration: none;
  font-size: 14px;
  white-space: nowrap;
  overflow: hidden;
  transition:
    background 0.2s ease,
    color 0.2s ease,
    transform 0.2s ease;
}

.nav-item:hover {
  background: rgba(255, 255, 255, 0.07);
  color: #fff;
}

.nav-item.active {
  background: linear-gradient(135deg, #35684b, #28503a);
  color: #fff;
  box-shadow: 0 6px 16px rgba(0, 0, 0, 0.22);
}

.nav-item.active::before {
  content: '';
  position: absolute;
  left: -14px;
  top: 22%;
  bottom: 22%;
  width: 4px;
  border-radius: 4px;
  background: var(--tea-gold);
}

.aside-foot {
  padding: 12px 14px 20px;
  border-top: 1px solid rgba(255, 255, 255, 0.08);
}

.admin-main {
  flex: 1;
  min-width: 0;
  display: flex;
  flex-direction: column;
}

.admin-topbar {
  position: sticky;
  top: 0;
  z-index: 40;
  height: 64px;
  display: flex;
  align-items: center;
  gap: 16px;
  padding: 0 26px;
  background: rgba(255, 255, 255, 0.9);
  backdrop-filter: blur(10px);
  -webkit-backdrop-filter: blur(10px);
  border-bottom: 1px solid var(--tea-line-soft);
}

.collapse-btn {
  width: 36px;
  height: 36px;
  border: 1px solid var(--tea-line);
  border-radius: 9px;
  background: #fff;
  color: var(--tea-ink-2);
  cursor: pointer;
  display: flex;
  align-items: center;
  justify-content: center;
  transition:
    border-color 0.2s ease,
    color 0.2s ease,
    box-shadow 0.2s ease;
}

.collapse-btn:hover {
  border-color: var(--tea-gold);
  color: var(--tea-gold);
  box-shadow: 0 4px 12px rgba(169, 126, 58, 0.14);
}

.topbar-title {
  display: flex;
  flex-direction: column;
  gap: 2px;
}

.title-breadcrumb {
  font-size: 11px;
  letter-spacing: 0.14em;
  color: var(--tea-muted);
}

.title-current {
  font-family: var(--tea-font-serif);
  font-size: 17px;
  font-weight: 600;
  color: var(--tea-ink);
}

.topbar-right {
  margin-left: auto;
  display: flex;
  align-items: center;
}

.user-chip {
  display: flex;
  align-items: center;
  gap: 8px;
  padding: 6px 12px 6px 6px;
  border-radius: 999px;
  cursor: pointer;
  background: rgba(255, 255, 255, 0.8);
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

.admin-content {
  flex: 1;
  padding: 28px;
}

@media (max-width: 900px) {
  .admin-aside {
    width: 72px;
  }

  .admin-aside .brand-text,
  .admin-aside .nav-label {
    display: none;
  }
}
</style>
