<template>
  <div class="user-manage">
    <div class="toolbar">
      <el-input
        v-model="keyword"
        placeholder="搜索用户名 / 昵称 / 邮箱"
        clearable
        class="search-input"
        @keyup.enter="onSearch"
        @clear="onSearch"
      >
        <template #prefix>
          <el-icon><Search /></el-icon>
        </template>
      </el-input>
      <el-button type="primary" @click="onSearch">搜索</el-button>
    </div>

    <el-table v-loading="loading" :data="users" stripe class="user-table">
      <el-table-column prop="id" label="ID" width="70" />
      <el-table-column prop="username" label="用户名" min-width="120" />
      <el-table-column prop="nickname" label="昵称" min-width="120" />
      <el-table-column prop="email" label="邮箱" min-width="160">
        <template #default="{ row }">{{ row.email || '-' }}</template>
      </el-table-column>
      <el-table-column label="角色" width="110">
        <template #default="{ row }">
          <el-tag :type="row.is_root ? 'danger' : row.role === 'admin' ? 'warning' : 'info'" effect="light" round>
            {{ row.is_root ? '主账号' : row.role === 'admin' ? '管理员' : '普通用户' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="110">
        <template #default="{ row }">
          <el-tag :type="row.status === 'active' ? 'success' : 'danger'" effect="light" round>
            {{ row.status === 'active' ? '正常' : '已禁用' }}
          </el-tag>
        </template>
      </el-table-column>
      <el-table-column prop="created_at" label="注册时间" min-width="160">
        <template #default="{ row }">{{ formatTime(row.created_at) }}</template>
      </el-table-column>
      <el-table-column label="操作" width="230" fixed="right">
        <template #default="{ row }">
          <template v-if="row.id !== authStore.user?.id">
            <span v-if="row.is_root" class="self-tag">主账号（受保护）</span>
            <el-button
              v-else-if="row.status === 'active'"
              size="small"
              type="danger"
              plain
              @click="handleToggleStatus(row, 'disabled')"
            >
              禁用
            </el-button>
            <el-button
              v-else-if="row.status === 'disabled'"
              size="small"
              type="success"
              plain
              @click="handleToggleStatus(row, 'active')"
            >
              启用
            </el-button>
            <el-button
              v-if="!row.is_root && row.role === 'user'"
              size="small"
              type="warning"
              plain
              @click="handleToggleRole(row, 'admin')"
            >
              设为管理员
            </el-button>
            <el-button
              v-else-if="!row.is_root && row.role === 'admin'"
              size="small"
              plain
              @click="handleToggleRole(row, 'user')"
            >
              取消管理员
            </el-button>
          </template>
          <span v-else class="self-tag">当前账号</span>
        </template>
      </el-table-column>
    </el-table>

    <div class="pager">
      <el-pagination
        background
        layout="total, prev, pager, next"
        :total="total"
        :page-size="pageSize"
        :current-page="page"
        @current-change="onPageChange"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
import { Search } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, ref } from 'vue'

import { getAdminUsers, updateUserRole, updateUserStatus } from '@/api/admin'
import { useAuthStore } from '@/store/auth'
import type { UserInfo } from '@/types/auth'

const authStore = useAuthStore()

const keyword = ref('')
const users = ref<UserInfo[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 10
const loading = ref(false)

async function loadUsers() {
  loading.value = true
  try {
    const { data } = await getAdminUsers({
      keyword: keyword.value.trim() || undefined,
      page: page.value,
      page_size: pageSize,
    })
    users.value = data.items
    total.value = data.total
  } catch {
    // 错误提示由 http 拦截器统一处理
  } finally {
    loading.value = false
  }
}

function onSearch() {
  page.value = 1
  loadUsers()
}

function onPageChange(next: number) {
  page.value = next
  loadUsers()
}

async function handleToggleStatus(row: UserInfo, status: 'active' | 'disabled') {
  const action = status === 'disabled' ? '禁用' : '启用'
  try {
    await ElMessageBox.confirm(`确定要${action}用户「${row.username}」吗？`, '操作确认', {
      type: 'warning',
    })
  } catch {
    return
  }
  try {
    await updateUserStatus(row.id, { status })
    ElMessage.success(`已${action}`)
    loadUsers()
  } catch {
    // 拦截器提示
  }
}

async function handleToggleRole(row: UserInfo, role: 'user' | 'admin') {
  const action = role === 'admin' ? '设为管理员' : '取消管理员'
  try {
    await ElMessageBox.confirm(
      `确定要${action}「${row.username}」吗？`,
      '操作确认',
      { type: 'warning' },
    )
  } catch {
    return
  }
  try {
    await updateUserRole(row.id, { role })
    ElMessage.success(`已${action}`)
    loadUsers()
  } catch {
    // 拦截器提示
  }
}

function formatTime(value: string) {
  return new Date(value).toLocaleString('zh-CN', { hour12: false })
}

onMounted(loadUsers)
</script>

<style scoped>
.toolbar {
  display: flex;
  gap: 10px;
  margin-bottom: 16px;
}

.search-input {
  width: 300px;
}

.pager {
  display: flex;
  justify-content: flex-end;
  margin-top: 16px;
}

.self-tag {
  color: var(--tea-muted);
  font-size: 13px;
}
</style>
