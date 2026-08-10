<template>
  <div class="category-manage">
    <div class="page-head">
      <div>
        <h1 class="page-title">分类管理</h1>
        <p class="page-sub">维护商城茶类，排序值越小越靠前</p>
      </div>
      <el-button type="primary" @click="openCreate">
        <el-icon><Plus /></el-icon>
        新增分类
      </el-button>
    </div>

    <div class="panel">
      <div class="panel-toolbar">
        <span class="panel-count">共 {{ categories.length }} 个分类</span>
      </div>
      <el-table v-loading="loading" :data="categories" class="admin-table">
        <el-table-column prop="id" label="ID" width="80" />
        <el-table-column label="分类名称" min-width="220">
          <template #default="{ row }">
            <span class="cat-name">
              <span class="cat-dot" :style="{ background: dotColor(row.id) }"></span>
              {{ row.name }}
            </span>
          </template>
        </el-table-column>
        <el-table-column prop="sort_order" label="排序" width="100" />
        <el-table-column prop="created_at" label="创建时间" min-width="180" />
        <el-table-column label="操作" width="170" align="right">
          <template #default="{ row }">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" plain @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </div>

    <el-dialog
      v-model="dialogVisible"
      :title="editingId ? '编辑分类' : '新增分类'"
      width="440px"
      align-center
    >
      <el-form :model="form" label-width="84px">
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
</template>

<script setup lang="ts">
import { Plus } from '@element-plus/icons-vue'
import { ElMessage, ElMessageBox } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'

import { createCategory, deleteCategory, getCategories, updateCategory } from '@/api/categories'
import type { Category } from '@/types/category'

const categories = ref<Category[]>([])
const dialogVisible = ref(false)
const saving = ref(false)
const editingId = ref<number | null>(null)
const form = reactive({ name: '', sort_order: 0 })
const loading = ref(false)

const dotPalette = [
  'linear-gradient(135deg, #35684b, #28503a)',
  'linear-gradient(135deg, #b98a3f, #8f6a2c)',
  'linear-gradient(135deg, #6a5c4a, #4a3f33)',
  'linear-gradient(135deg, #7c5a3a, #5b3f26)',
  'linear-gradient(135deg, #3f6b5e, #2c4f44)',
]

function dotColor(id: number) {
  return dotPalette[id % dotPalette.length]
}

async function load() {
  loading.value = true
  try {
    const { data } = await getCategories()
    categories.value = data
  } finally {
    loading.value = false
  }
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
.page-head {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  gap: 20px;
  margin-bottom: 24px;
}

.page-title {
  margin: 0;
  font-family: var(--tea-font-serif);
  font-size: 26px;
  letter-spacing: 0.08em;
  color: var(--tea-ink);
}

.page-sub {
  margin: 8px 0 0;
  font-size: 13px;
  color: var(--tea-muted);
}

.panel {
  background: var(--tea-surface);
  border: 1px solid var(--tea-line-soft);
  border-radius: var(--tea-radius);
  box-shadow: var(--tea-shadow-sm);
  overflow: hidden;
}

.panel-toolbar {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 14px 20px;
  border-bottom: 1px solid var(--tea-line-soft);
  background: #fbf8f1;
}

.panel-count {
  font-size: 13px;
  color: var(--tea-muted);
}

.admin-table {
  padding: 0 8px 8px;
}

.cat-name {
  display: inline-flex;
  align-items: center;
  gap: 10px;
  font-weight: 500;
  color: var(--tea-ink);
}

.cat-dot {
  width: 12px;
  height: 12px;
  border-radius: 50%;
  box-shadow: 0 2px 6px rgba(58, 66, 46, 0.2);
}
</style>
