<template>
  <div class="admin-page">
    <AppHeader />
    <div class="admin-content">
      <div class="admin-header">
        <h2>商品管理</h2>
        <el-button type="primary" @click="openCreate">新增商品</el-button>
      </div>

      <el-table v-loading="loading" :data="products" border stripe>
        <el-table-column prop="id" label="ID" width="60" />
        <el-table-column label="图片" width="80">
          <template #default="{ row }">
            <el-image
              v-if="row.image_url"
              :src="row.image_url"
              fit="cover"
              style="width: 50px; height: 50px; border-radius: 4px"
            />
            <span v-else class="no-image">无</span>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="名称" min-width="140" show-overflow-tooltip />
        <el-table-column prop="category_name" label="分类" width="100" />
        <el-table-column label="价格" width="100">
          <template #default="{ row }">¥{{ Number(row.price).toFixed(2) }}</template>
        </el-table-column>
        <el-table-column prop="stock" label="库存" width="80" />
        <el-table-column label="上架" width="80">
          <template #default="{ row }">
            <el-switch
              :model-value="row.is_on_sale"
              @change="(value: string | number | boolean) => toggleSale(row, value)"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="150">
          <template #default="{ row }">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>

      <PaginationBar
        :total="total"
        :page="page"
        :page-size="pageSize"
        @update:page="onPageChange"
      />

      <el-dialog v-model="dialogVisible" :title="editingId ? '编辑商品' : '新增商品'" width="560px">
        <el-form :model="form" label-width="80px">
          <el-form-item label="商品名称">
            <el-input v-model="form.name" placeholder="请输入商品名称" />
          </el-form-item>
          <el-form-item label="分类">
            <el-select v-model="form.category_id" placeholder="请选择分类" style="width: 100%">
              <el-option v-for="c in categories" :key="c.id" :label="c.name" :value="c.id" />
            </el-select>
          </el-form-item>
          <el-form-item label="价格">
            <el-input-number v-model="form.price" :min="0" :precision="2" :step="10" />
          </el-form-item>
          <el-form-item label="库存">
            <el-input-number v-model="form.stock" :min="0" />
          </el-form-item>
          <el-form-item label="描述">
            <el-input v-model="form.description" type="textarea" :rows="3" placeholder="商品描述" />
          </el-form-item>
          <el-form-item label="上架">
            <el-switch v-model="form.is_on_sale" />
          </el-form-item>
          <el-form-item label="图片">
            <el-upload
              :auto-upload="false"
              :limit="1"
              accept="image/*"
              :on-change="handleFileChange"
            >
              <el-button>选择图片</el-button>
            </el-upload>
            <div v-if="form.image_url || selectedFile" class="upload-preview">
              <el-image
                v-if="form.image_url"
                :src="form.image_url"
                fit="cover"
                style="width: 80px; height: 80px; border-radius: 4px"
              />
              <span v-if="selectedFile">{{ selectedFile.name }}</span>
            </div>
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
import type { UploadFile } from 'element-plus'
import { onMounted, reactive, ref } from 'vue'

import { getCategories } from '@/api/categories'
import {
  createProduct,
  deleteProduct,
  getProducts,
  updateProduct,
  uploadProductImage,
} from '@/api/products'
import AppHeader from '@/components/AppHeader.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import type { Category } from '@/types/category'
import type { Product } from '@/types/product'

const products = ref<Product[]>([])
const categories = ref<Category[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 10
const dialogVisible = ref(false)
const saving = ref(false)
const editingId = ref<number | null>(null)
const selectedFile = ref<File | null>(null)
const loading = ref(false)
const form = reactive({
  name: '',
  category_id: undefined as number | undefined,
  price: 0,
  stock: 0,
  description: '',
  image_url: '',
  is_on_sale: true,
})

async function load() {
  loading.value = true
  try {
    const { data } = await getProducts({
      page: page.value,
      page_size: pageSize,
      include_off_sale: true,
    })
    products.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function openCreate() {
  editingId.value = null
  Object.assign(form, {
    name: '',
    category_id: undefined,
    price: 0,
    stock: 0,
    description: '',
    image_url: '',
    is_on_sale: true,
  })
  selectedFile.value = null
  dialogVisible.value = true
}

function openEdit(row: Product) {
  editingId.value = row.id
  Object.assign(form, {
    name: row.name,
    category_id: row.category_id,
    price: Number(row.price),
    stock: row.stock,
    description: row.description,
    image_url: row.image_url,
    is_on_sale: row.is_on_sale,
  })
  selectedFile.value = null
  dialogVisible.value = true
}

function handleFileChange(file: UploadFile) {
  if (file.raw) {
    selectedFile.value = file.raw
  }
}

async function handleSave() {
  if (!form.name.trim() || form.category_id === undefined) {
    ElMessage.warning('请填写商品名称并选择分类')
    return
  }
  saving.value = true
  try {
    const payload = {
      name: form.name.trim(),
      category_id: form.category_id!,
      price: form.price,
      stock: form.stock,
      description: form.description,
      image_url: form.image_url,
      is_on_sale: form.is_on_sale,
    }
    let product: Product
    if (editingId.value) {
      const { data } = await updateProduct(editingId.value, payload)
      product = data
    } else {
      const { data } = await createProduct(payload)
      product = data
    }
    if (selectedFile.value) {
      const { data } = await uploadProductImage(product.id, selectedFile.value)
      product = data
    }
    ElMessage.success('保存成功')
    dialogVisible.value = false
    load()
  } finally {
    saving.value = false
  }
}

async function toggleSale(row: Product, value: string | number | boolean) {
  const isOnSale = Boolean(value)
  await updateProduct(row.id, { is_on_sale: isOnSale })
  ElMessage.success(isOnSale ? '已上架' : '已下架')
  load()
}

async function handleDelete(row: Product) {
  try {
    await ElMessageBox.confirm(`确定删除商品「${row.name}」吗？`, '提示', { type: 'warning' })
    await deleteProduct(row.id)
    ElMessage.success('删除成功')
    load()
  } catch {
    // 用户取消，或删除失败（失败提示由 axios 拦截器统一处理）
  }
}

function onPageChange(newPage: number) {
  page.value = newPage
  load()
}

onMounted(async () => {
  const { data } = await getCategories()
  categories.value = data
  load()
})
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

.no-image {
  color: #999;
  font-size: 12px;
}

.upload-preview {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 8px;
  color: #666;
  font-size: 13px;
}
</style>
