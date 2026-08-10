<template>
  <AuthShell>
    <div class="auth-head">
      <h1 class="auth-title">欢迎回来</h1>
      <p class="auth-sub">登录茶叶商城，继续你的茶旅</p>
    </div>
    <el-form :model="form" label-width="0" size="large" @submit.prevent="handleLogin">
      <el-form-item>
        <el-input v-model="form.username" placeholder="用户名" :prefix-icon="User" />
      </el-form-item>
      <el-form-item>
        <el-input
          v-model="form.password"
          type="password"
          placeholder="密码"
          show-password
          :prefix-icon="Lock"
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" native-type="submit" :loading="loading" class="auth-btn">
          登录
        </el-button>
      </el-form-item>
    </el-form>
    <div class="auth-link">
      还没有账号？<router-link to="/register">去注册</router-link>
    </div>
  </AuthShell>
</template>

<script setup lang="ts">
import { Lock, User } from '@element-plus/icons-vue'
import { reactive, ref } from 'vue'
import { useRoute, useRouter } from 'vue-router'

import AuthShell from '@/components/AuthShell.vue'
import { useAuthStore } from '@/store/auth'
import { useCartStore } from '@/store/cart'

const router = useRouter()
const route = useRoute()
const authStore = useAuthStore()
const cartStore = useCartStore()

const form = reactive({ username: '', password: '' })
const loading = ref(false)

async function handleLogin() {
  if (!form.username || !form.password) return
  loading.value = true
  try {
    await authStore.login(form.username, form.password)
    await cartStore.fetchCart()
    const redirect = (route.query.redirect as string) || '/'
    router.push(redirect)
  } finally {
    loading.value = false
  }
}
</script>

<style scoped>
.auth-head {
  text-align: center;
  margin-bottom: 28px;
}

.auth-title {
  margin: 0;
  font-family: var(--tea-font-serif);
  font-size: 26px;
  letter-spacing: 0.08em;
  color: var(--tea-ink);
}

.auth-sub {
  margin: 10px 0 0;
  font-size: 13px;
  color: var(--tea-muted);
}

.auth-btn {
  width: 100%;
  height: 44px;
  margin-top: 6px;
  border-radius: 10px;
  font-size: 15px;
  letter-spacing: 0.3em;
}

.auth-link {
  margin-top: 18px;
  text-align: center;
  font-size: 14px;
  color: var(--tea-muted);
}

.auth-link a {
  color: var(--tea-gold);
  text-decoration: none;
  font-weight: 500;
}

.auth-link a:hover {
  color: var(--tea-gold-deep);
}
</style>
