<template>
  <AuthShell>
    <div class="auth-head">
      <h1 class="auth-title">创建账号</h1>
      <p class="auth-sub">开启你的茶叶之旅</p>
    </div>
    <el-form :model="form" label-width="0" size="large" @submit.prevent="handleRegister">
      <el-form-item>
        <el-input v-model="form.username" placeholder="用户名（至少 3 个字符）" :prefix-icon="User" />
      </el-form-item>
      <el-form-item>
        <el-input v-model="form.nickname" placeholder="昵称（可选）" :prefix-icon="Postcard" />
      </el-form-item>
      <el-form-item>
        <el-input
          v-model="form.password"
          type="password"
          placeholder="密码（至少 6 位）"
          show-password
          :prefix-icon="Lock"
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" native-type="submit" :loading="loading" class="auth-btn">
          注册
        </el-button>
      </el-form-item>
    </el-form>
    <div class="auth-link">
      已有账号？<router-link to="/login">去登录</router-link>
    </div>
  </AuthShell>
</template>

<script setup lang="ts">
import { Lock, Postcard, User } from '@element-plus/icons-vue'
import { ElMessage } from 'element-plus'
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import AuthShell from '@/components/AuthShell.vue'
import { useAuthStore } from '@/store/auth'

const router = useRouter()
const authStore = useAuthStore()

const form = reactive({ username: '', password: '', nickname: '' })
const loading = ref(false)

async function handleRegister() {
  if (!form.username || form.password.length < 6) return
  loading.value = true
  try {
    await authStore.register(form)
    ElMessage.success('注册成功，请登录')
    router.push('/login')
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
