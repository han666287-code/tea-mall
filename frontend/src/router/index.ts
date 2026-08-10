import { createRouter, createWebHistory, type RouteRecordRaw } from 'vue-router'

// Phase 0：空路由占位，页面路由从 Phase 1 开始添加
const routes: RouteRecordRaw[] = []

const router = createRouter({
  history: createWebHistory(),
  routes,
})

export default router
