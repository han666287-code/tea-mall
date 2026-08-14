<template>
  <AuthShell>
    <div class="auth-head">
      <h1 class="auth-title">创建账号</h1>
      <p class="auth-sub">开启你的茶叶之旅</p>
    </div>
    <el-form
      ref="formRef"
      :model="form"
      :rules="rules"
      label-width="0"
      size="large"
      @submit.prevent="handleRegister"
    >
      <el-form-item prop="username">
        <el-input v-model="form.username" placeholder="用户名（至少 3 个字符）" :prefix-icon="User" />
      </el-form-item>
      <el-form-item prop="nickname">
        <el-input v-model="form.nickname" placeholder="昵称（可选）" :prefix-icon="Postcard" />
      </el-form-item>
      <el-form-item prop="email">
        <el-input v-model="form.email" placeholder="邮箱（选填）" :prefix-icon="Message" />
      </el-form-item>
      <el-form-item prop="password">
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
import { Lock, Message, Postcard, User } from '@element-plus/icons-vue'
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import AuthShell from '@/components/AuthShell.vue'
import { useAuthStore } from '@/store/auth'

const router = useRouter()
const authStore = useAuthStore()

const form = reactive({ username: '', password: '', nickname: '', email: '' })
const formRef = ref<FormInstance>()
const loading = ref(false)

const rules: FormRules = {
  username: [
    { required: true, message: '请输入用户名', trigger: 'blur' },
    { min: 3, max: 50, message: '用户名长度为 3-50 个字符', trigger: 'blur' },
  ],
  password: [
    { required: true, message: '请输入密码', trigger: 'blur' },
    { min: 6, message: '密码至少 6 位', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value && new Blob([value]).size > 72) {
          callback(new Error('密码过长：UTF-8 编码后不能超过 72 字节'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
  nickname: [{ max: 50, message: '昵称不能超过 50 个字符', trigger: 'blur' }],
  email: [
    {
      validator: (_rule, value, callback) => {
        if (!value || /^[^\s@]+@[^\s@]+\.[^\s@]+$/.test(value)) {
          callback()
        } else {
          callback(new Error('邮箱格式不正确'))
        }
      },
      trigger: 'blur',
    },
  ],
}

async function handleRegister() {
  const valid = await formRef.value?.validate().catch(() => false)
  if (!valid) return
  loading.value = true
  try {
    await authStore.register({ ...form, email: form.email.trim() || null })
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
