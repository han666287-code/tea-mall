<template>
  <div class="admin-page">
    <AppHeader />
    <div class="admin-content">
      <div class="admin-header">
        <h2>分类管理</h2>
        <el-button type="primary" @click="openCreate">新增分类</el-button>
      </div>

      <el-table :data="categories" border stripe>
        <el-table-column prop="id" label="ID" width="70" />
        <el-table-column prop="name" label="分类名称" />
        <el-table-column prop="sort_order" label="排序" width="90" />
        <el-table-column prop="created_at" label="创建时间" width="180" />
        <el-table-column label="操作" width="160">
          <template #default="{ row }">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <el-dialog v-model="dialogVisible" :title="editingId ? '编辑分类' : '新增分类'" width="420px">
        <el-form :model="form" label-width="80px">
          <el-form-item label="分类名称">
            <el-input v-model="form.name" placeholder="请输入分类名称" />
          </el-form-item>
          <el-form-item label="排序">
            <el-input-number v-model="form.sort_order" :min="0" />
          </el-form-item>
        </el-form>
        <template #footer>
          <el-button @click="dialogVisible = false">取消</el-button>
          <el-button type="primary" :loading="saving" @click="handleSave">保存</el-button>
        </template>
      </el-dialog>
    </div>
  </div>
</template>

<script setup lang="ts">
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'

import { createCategory, deleteCategory, getCategories, updateCategory } from '@/api/categories'
import AppHeader from '@/components/AppHeader.vue'
import type { Category } from '@/types/category'

const categories = ref<Category[]>([])
const dialogVisible = ref(false)
const saving = ref(false)
const editingId = ref<number | null>(null)
const form = reactive({ name: '', sort_order: 0 })

async function load() {
  const { data } = await getCategories()
  categories.value = data
}

function openCreate() {
  editingId.value = null
  form.name = ''
  form.sort_order = 0
  dialogVisible.value = true
}

function openEdit(row: Category) {
  editingId.value = row.id
  form.name = row.name
  form.sort_order = row.sort_order
  dialogVisible.value = true
}

async function handleSave() {
  if (!form.name.trim()) {
    ElMessage.warning('请输入分类名称')
    return
  }
  saving.value = true
  try {
    if (editingId.value) {
      await updateCategory(editingId.value, {
        name: form.name.trim(),
        sort_order: form.sort_order,
      })
    } else {
      await createCategory({ name: form.name.trim(), sort_order: form.sort_order })
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    load()
  } finally {
    saving.value = false
  }
}

async function handleDelete(row: Category) {
  try {
    await ElMessageBox.confirm(`确定删除分类「${row.name}」吗？`, '提示', { type: 'warning' })
    await deleteCategory(row.id)
    ElMessage.success('删除成功')
    load()
  } catch {
    // 用户取消，或删除失败（失败提示由 axios 拦截器统一处理）
  }
}

onMounted(load)
</script>

<style scoped>
.admin-content {
  max-width: 1100px;
  margin: 0 auto;
  padding: 20px;
}

.admin-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}

.admin-header h2 {
  margin: 0;
}
</style>
