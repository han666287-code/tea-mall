<template>
  <div class="profile-page">
    <AppHeader />
    <div class="tea-page profile-body">
      <div class="page-head">
        <div>
          <p class="page-eyebrow">MY ACCOUNT</p>
          <h1 class="page-title">个人中心</h1>
        </div>
      </div>

      <div class="profile-grid">
        <section class="profile-card">
          <h2 class="card-title">账户信息</h2>
          <el-descriptions :column="1" border>
            <el-descriptions-item label="用户名">{{ authStore.user?.username }}</el-descriptions-item>
            <el-descriptions-item label="昵称">{{ authStore.user?.nickname || '-' }}</el-descriptions-item>
            <el-descriptions-item label="邮箱">{{ authStore.user?.email || '-' }}</el-descriptions-item>
            <el-descriptions-item label="角色">
              {{ authStore.user?.role === 'admin' ? '管理员' : '普通用户' }}
            </el-descriptions-item>
            <el-descriptions-item label="注册时间">{{ formatTime(authStore.user?.created_at) }}</el-descriptions-item>
          </el-descriptions>

          <h2 class="card-title">编辑资料</h2>
          <el-form
            ref="profileFormRef"
            :model="profileForm"
            :rules="profileRules"
            label-width="80px"
            @submit.prevent="handleSaveProfile"
          >
            <el-form-item label="昵称" prop="nickname">
              <el-input v-model="profileForm.nickname" maxlength="50" placeholder="昵称（不超过 50 字）" />
            </el-form-item>
            <el-form-item label="邮箱" prop="email">
              <el-input v-model="profileForm.email" placeholder="邮箱（选填）" />
            </el-form-item>
            <el-form-item>
              <el-button type="primary" :loading="savingProfile" @click="handleSaveProfile">
                保存资料
              </el-button>
            </el-form-item>
          </el-form>
        </section>

        <section class="profile-card">
          <h2 class="card-title">修改密码</h2>
          <el-form
            ref="passwordFormRef"
            :model="passwordForm"
            :rules="passwordRules"
            label-width="80px"
            @submit.prevent="handleChangePassword"
          >
            <el-form-item label="旧密码" prop="old_password">
              <el-input
                v-model="passwordForm.old_password"
                type="password"
                show-password
                placeholder="输入当前密码"
              />
            </el-form-item>
            <el-form-item label="新密码" prop="new_password">
              <el-input
                v-model="passwordForm.new_password"
                type="password"
                show-password
                placeholder="至少 6 位"
              />
            </el-form-item>
            <el-form-item label="确认密码" prop="confirm">
              <el-input
                v-model="passwordForm.confirm"
                type="password"
                show-password
                placeholder="再次输入新密码"
              />
            </el-form-item>
            <el-form-item>
              <el-button type="danger" :loading="changingPassword" @click="handleChangePassword">
                修改密码
              </el-button>
            </el-form-item>
          </el-form>
        </section>
      </div>
    </div>
    <AppFooter />
  </div>
</template>

<script setup lang="ts">
import { ElMessage, type FormInstance, type FormRules } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'
import { useRouter } from 'vue-router'

import { changePassword, updateProfile } from '@/api/auth'
import AppFooter from '@/components/AppFooter.vue'
import AppHeader from '@/components/AppHeader.vue'
import { useAuthStore } from '@/store/auth'
import type { UpdateProfileRequest } from '@/types/auth'

const router = useRouter()
const authStore = useAuthStore()

const profileForm = reactive({ nickname: '', email: '' })
const profileFormRef = ref<FormInstance>()
const savingProfile = ref(false)

const EMAIL_RE = /^[^\s@]+@[^\s@]+\.[^\s@]+$/

const profileRules: FormRules = {
  nickname: [{ max: 50, message: '昵称不能超过 50 个字符', trigger: 'blur' }],
  email: [
    {
      validator: (_rule, value, callback) => {
        if (!value || EMAIL_RE.test(value)) {
          callback()
        } else {
          callback(new Error('邮箱格式不正确'))
        }
      },
      trigger: 'blur',
    },
  ],
}

const passwordForm = reactive({ old_password: '', new_password: '', confirm: '' })
const passwordFormRef = ref<FormInstance>()
const changingPassword = ref(false)

const passwordRules: FormRules = {
  old_password: [{ required: true, message: '请输入当前密码', trigger: 'blur' }],
  new_password: [
    { required: true, message: '请输入新密码', trigger: 'blur' },
    { min: 6, message: '新密码至少 6 位', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value && new Blob([value]).size > 72) {
          callback(new Error('新密码过长：UTF-8 编码后不能超过 72 字节'))
        } else {
          callback()
        }
      },
      trigger: 'blur',
    },
  ],
  confirm: [
    { required: true, message: '请再次输入新密码', trigger: 'blur' },
    {
      validator: (_rule, value, callback) => {
        if (value === passwordForm.new_password) {
          callback()
        } else {
          callback(new Error('两次输入的新密码不一致'))
        }
      },
      trigger: 'blur',
    },
  ],
}

function initForms() {
  profileForm.nickname = authStore.user?.nickname || ''
  profileForm.email = authStore.user?.email || ''
}

onMounted(initForms)

async function handleSaveProfile() {
  const valid = await profileFormRef.value?.validate().catch(() => false)
  if (!valid) return

  const payload: UpdateProfileRequest = {}
  if (profileForm.nickname !== (authStore.user?.nickname || '')) {
    payload.nickname = profileForm.nickname
  }
  const email = profileForm.email.trim()
  if (email !== (authStore.user?.email || '')) {
    payload.email = email || null
  }
  if (!Object.keys(payload).length) {
    ElMessage.info('没有需要保存的修改')
    return
  }

  savingProfile.value = true
  try {
    await updateProfile(payload)
    await authStore.fetchMe()
    ElMessage.success('资料已更新')
  } catch {
    // 错误提示由 http 拦截器统一处理
  } finally {
    savingProfile.value = false
  }
}

async function handleChangePassword() {
  const valid = await passwordFormRef.value?.validate().catch(() => false)
  if (!valid) return

  changingPassword.value = true
  try {
    await changePassword({
      old_password: passwordForm.old_password,
      new_password: passwordForm.new_password,
    })
    ElMessage.success('密码修改成功，请重新登录')
    authStore.forceLogout()
    router.push('/login')
  } catch {
    // 错误提示由 http 拦截器统一处理
  } finally {
    changingPassword.value = false
  }
}

function formatTime(value?: string) {
  if (!value) return '-'
  return new Date(value).toLocaleString('zh-CN', { hour12: false })
}
</script>

<style scoped>
.profile-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 24px;
  margin-top: 20px;
}

.profile-card {
  padding: 22px;
  background: rgba(255, 255, 255, 0.82);
  border: 1px solid var(--tea-line-soft);
  border-radius: 14px;
}

.card-title {
  margin: 0 0 16px;
  font-family: var(--tea-font-serif);
  font-size: 18px;
  color: var(--tea-ink);
}

.profile-card .card-title + .card-title {
  margin-top: 28px;
}

@media (max-width: 900px) {
  .profile-grid {
    grid-template-columns: 1fr;
  }
}
</style>
