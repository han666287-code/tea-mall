<template>
  <div class="product-manage">
    <div class="page-head">
      <div>
        <h1 class="page-title">商品管理</h1>
        <p class="page-sub">管理商品信息、库存与上下架状态</p>
      </div>
      <el-button type="primary" @click="openCreate">
        <el-icon><Plus /></el-icon>
        新增商品
      </el-button>
    </div>

    <div class="panel">
      <div class="panel-toolbar">
        <span class="panel-count">共 {{ total }} 款商品</span>
      </div>
      <el-table v-loading="loading" :data="products" class="admin-table">
        <el-table-column prop="id" label="ID" align="center" header-align="center" />
        <el-table-column label="图片" align="center" header-align="center">
          <template #default="{ row }">
            <el-image v-if="row.image_url" :src="row.image_url" fit="cover" class="thumb" />
            <div v-else class="thumb thumb-ph">无图</div>
          </template>
        </el-table-column>
        <el-table-column prop="name" label="名称" align="center" header-align="center" show-overflow-tooltip />
        <el-table-column label="分类" align="center" header-align="center">
          <template #default="{ row }">
            <span class="cat-tag">{{ row.category_name || '-' }}</span>
          </template>
        </el-table-column>
        <el-table-column label="价格" align="center" header-align="center">
          <template #default="{ row }">
            <span class="price-cell">¥{{ Number(row.price).toFixed(2) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="库存" align="center" header-align="center">
          <template #default="{ row }">
            <span class="stock-cell" :class="{ low: row.stock <= 10 }">{{ row.stock }}</span>
          </template>
        </el-table-column>
        <el-table-column label="上架" align="center" header-align="center">
          <template #default="{ row }">
            <el-switch
              :model-value="row.is_on_sale"
              @change="(value: string | number | boolean) => toggleSale(row, value)"
            />
          </template>
        </el-table-column>
        <el-table-column label="操作" width="170" align="center" header-align="center">
          <template #default="{ row }">
            <el-button size="small" @click="openEdit(row)">编辑</el-button>
            <el-button size="small" type="danger" plain @click="handleDelete(row)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
      <PaginationBar
        :total="total"
        :page="page"
        :page-size="pageSize"
        @update:page="onPageChange"
      />
    </div>

    <el-dialog
      v-model="dialogVisible"
      :title="editingId ? '编辑商品' : '新增商品'"
      width="840px"
      align-center
    >
      <el-form :model="form" label-width="84px">
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
              class="upload-img"
            />
            <span v-if="selectedFile" class="upload-name">{{ selectedFile.name }}</span>
          </div>
        </el-form-item>
        <el-divider />
        <el-form-item label="SKU 规格">
          <div class="sku-editor">
            <el-input
              v-model="specNamesText"
              placeholder="规格名（逗号分隔），如：净含量,包装；留空表示无规格"
              class="spec-names-input"
            />
            <el-table :data="skuRows" size="small" border class="sku-table">
              <el-table-column
                v-for="(name, index) in specNames"
                :key="`${name}-${index}`"
                :label="name || '规格值'"
              >
                <template #default="{ row }">
                  <el-input v-model="row.values[index]" placeholder="如 100g" />
                </template>
              </el-table-column>
              <el-table-column label="SKU 编码" width="150">
                <template #default="{ row }">
                  <el-input v-model="row.sku_code" placeholder="留空自动生成" />
                </template>
              </el-table-column>
              <el-table-column label="价格" width="120">
                <template #default="{ row }">
                  <el-input-number
                    v-model="row.price"
                    :min="0"
                    :precision="2"
                    :controls="false"
                    class="sku-num"
                  />
                </template>
              </el-table-column>
              <el-table-column label="库存" width="110">
                <template #default="{ row }">
                  <el-input-number
                    v-model="row.stock"
                    :min="0"
                    :controls="false"
                    class="sku-num"
                  />
                </template>
              </el-table-column>
              <el-table-column label="启用" width="70" align="center">
                <template #default="{ row }">
                  <el-switch v-model="row.is_active" />
                </template>
              </el-table-column>
              <el-table-column label="操作" width="76" align="center">
                <template #default="{ row }">
                  <el-button size="small" type="danger" plain @click="removeSkuRow(row)">
                    删除
                  </el-button>
                </template>
              </el-table-column>
            </el-table>
            <div class="sku-actions">
              <el-button size="small" @click="addSkuRow">
                <el-icon><Plus /></el-icon>
                添加 SKU 行
              </el-button>
              <span class="sku-hint">多规格时价格/库存以 SKU 行为准</span>
            </div>
          </div>
        </el-form-item>
        <el-form-item label="详情图">
          <div class="detail-images">
            <div v-for="img in detailImages" :key="img.id" class="detail-img-item">
              <el-image :src="img.url" fit="cover" class="detail-img-thumb" />
              <el-button size="small" type="danger" plain @click="removeDetailImage(img)">
                删除
              </el-button>
            </div>
            <div v-for="(file, index) in selectedDetailFiles" :key="`new-${index}`" class="detail-img-item">
              <span class="detail-img-name">{{ file.name }}</span>
              <el-button size="small" plain @click="removeSelectedFile(index)">移除</el-button>
            </div>
            <el-upload
              :auto-upload="false"
              multiple
              accept="image/*"
              :show-file-list="false"
              :on-change="handleDetailFilesChange"
            >
              <el-button>选择详情图</el-button>
            </el-upload>
            <span class="sku-hint">可多选，保存时上传</span>
          </div>
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
import type { UploadFile } from 'element-plus'
import { computed, onMounted, reactive, ref } from 'vue'

import { getCategories } from '@/api/categories'
import {
  createProduct,
  deleteProduct,
  deleteProductImage,
  getProducts,
  updateProduct,
  uploadProductImages,
  uploadProductImage,
} from '@/api/products'
import PaginationBar from '@/components/PaginationBar.vue'
import type { Category } from '@/types/category'
import type { Product, ProductImage, ProductPayload } from '@/types/product'

const products = ref<Product[]>([])
const categories = ref<Category[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 10
const dialogVisible = ref(false)
const saving = ref(false)
const editingId = ref<number | null>(null)
const selectedFile = ref<File | null>(null)
const detailImages = ref<ProductImage[]>([])
const selectedDetailFiles = ref<File[]>([])
const loading = ref(false)
const specNamesText = ref('')
const skuRows = ref<
  { sku_code: string; price: number; stock: number; is_active: boolean; values: string[] }[]
>([])
const form = reactive({
  name: '',
  category_id: undefined as number | undefined,
  price: 0,
  stock: 0,
  description: '',
  image_url: '',
  is_on_sale: true,
})

const specNames = computed(() =>
  specNamesText.value
    .split(/[,，]/)
    .map((s) => s.trim())
    .filter(Boolean),
)

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
  detailImages.value = []
  selectedDetailFiles.value = []
  resetSkuEditor()
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
  detailImages.value = (row.images ?? []).filter((img) => img.kind === 'detail')
  selectedDetailFiles.value = []
  loadSkuEditor(row)
  dialogVisible.value = true
}

function handleDetailFilesChange(uploadFile: { raw?: File }) {
  if (uploadFile.raw) {
    selectedDetailFiles.value.push(uploadFile.raw)
  }
}

async function removeDetailImage(img: ProductImage) {
  if (!editingId.value) return
  try {
    await deleteProductImage(editingId.value, img.url)
    detailImages.value = detailImages.value.filter((item) => item.id !== img.id)
    ElMessage.success('已删除详情图')
  } catch {
    // 错误提示由拦截器统一处理
  }
}

function removeSelectedFile(index: number) {
  selectedDetailFiles.value.splice(index, 1)
}

function resetSkuEditor() {
  specNamesText.value = ''
  skuRows.value = [{ sku_code: '', price: 0, stock: 0, is_active: true, values: [] }]
}

function loadSkuEditor(product: Product) {
  const skus = product.skus ?? []
  if (!skus.length) {
    resetSkuEditor()
    return
  }
  const names = Array.from(new Set(skus[0].specs.map((x) => x.name)))
  specNamesText.value = names.join(',')
  skuRows.value = skus.map((sku) => ({
    sku_code: sku.sku_code,
    price: Number(sku.price),
    stock: sku.stock,
    is_active: sku.is_active,
    values: names.map((n) => sku.specs.find((x) => x.name === n)?.value ?? ''),
  }))
}

function addSkuRow() {
  skuRows.value.push({
    sku_code: '',
    price: 0,
    stock: 0,
    is_active: true,
    values: specNames.value.map(() => ''),
  })
}

function removeSkuRow(row: { sku_code: string; price: number; stock: number; is_active: boolean; values: string[] }) {
  if (skuRows.value.length <= 1) {
    ElMessage.warning('至少保留一个 SKU')
    return
  }
  skuRows.value = skuRows.value.filter((r) => r !== row)
}

function buildSkusPayload() {
  return skuRows.value.map((row) => ({
    sku_code: row.sku_code.trim() || undefined,
    price: row.price,
    stock: row.stock,
    is_active: row.is_active,
    specs: specNames.value
      .map((name, index) => ({ name, value: row.values[index] || '' }))
      .filter((x) => x.value.trim()),
  }))
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
  if (skuRows.value.length === 1) {
    // 单 SKU：商品基本信息里的价格/库存同步到 SKU 行
    skuRows.value[0].price = form.price
    skuRows.value[0].stock = form.stock
  }
  const skus = buildSkusPayload()
  if (skus.length > 1 && specNames.value.length === 0) {
    ElMessage.warning('多个 SKU 需要填写规格名（如：净含量）')
    return
  }
  saving.value = true
  try {
    const payload: ProductPayload = {
      name: form.name.trim(),
      category_id: form.category_id!,
      price: form.price,
      stock: form.stock,
      description: form.description,
      image_url: form.image_url,
      is_on_sale: form.is_on_sale,
      skus,
    }
    let product: Product
    if (editingId.value) {
      const { data } = await updateProduct(editingId.value, {
        name: payload.name,
        category_id: payload.category_id,
        description: payload.description,
        image_url: payload.image_url,
        is_on_sale: payload.is_on_sale,
        skus,
      })
      product = data
    } else {
      const { data } = await createProduct(payload)
      product = data
    }
    if (selectedFile.value) {
      const { data } = await uploadProductImage(product.id, selectedFile.value)
      product = data
    }
    if (selectedDetailFiles.value.length) {
      const { data } = await uploadProductImages(product.id, selectedDetailFiles.value)
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
  padding: 0 8px;
}

.thumb {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  width: 48px;
  height: 48px;
  border-radius: 8px;
  background: var(--tea-gold-soft);
}

.thumb-ph {
  display: inline-flex;
  align-items: center;
  justify-content: center;
  font-size: 11px;
  color: var(--tea-muted);
}

.cat-tag {
  display: inline-block;
  padding: 3px 10px;
  border-radius: 999px;
  font-size: 12px;
  color: var(--tea-primary);
  background: var(--tea-primary-soft);
}

.price-cell {
  font-weight: 600;
  color: var(--tea-price);
  font-variant-numeric: tabular-nums;
}

.stock-cell {
  font-variant-numeric: tabular-nums;
  color: var(--tea-ink-2);
}

.stock-cell.low {
  color: var(--tea-price);
  font-weight: 600;
}

.upload-preview {
  display: flex;
  align-items: center;
  gap: 10px;
  margin-top: 8px;
  color: var(--tea-muted);
  font-size: 13px;
}

.upload-img {
  width: 80px;
  height: 80px;
  border-radius: 8px;
  border: 1px solid var(--tea-line-soft);
}

.upload-name {
  max-width: 220px;
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}

.sku-editor {
  width: 100%;
}

.spec-names-input {
  margin-bottom: 10px;
}

.sku-table {
  margin-bottom: 10px;
}

.sku-num {
  width: 100%;
}

.sku-actions {
  display: flex;
  align-items: center;
  gap: 12px;
}

.sku-hint {
  font-size: 12px;
  color: var(--tea-muted);
}

.detail-images {
  display: flex;
  flex-wrap: wrap;
  gap: 10px;
  align-items: center;
  width: 100%;
}

.detail-img-item {
  display: inline-flex;
  align-items: center;
  gap: 8px;
  padding: 6px 8px 6px 6px;
  border: 1px solid var(--tea-line-soft);
  border-radius: 8px;
  background: #fff;
}

.detail-img-thumb {
  width: 56px;
  height: 56px;
  border-radius: 6px;
}

.detail-img-name {
  max-width: 120px;
  font-size: 12px;
  color: var(--tea-ink-2);
  overflow: hidden;
  text-overflow: ellipsis;
  white-space: nowrap;
}
</style>
