<template>
  <div class="home-page">
    <AppHeader />

    <!-- Hero 横幅 -->
    <section class="hero">
      <div class="hero-art" aria-hidden="true">
        <div class="hero-glow"></div>
        <svg class="hero-mountains" viewBox="0 0 1440 320" preserveAspectRatio="none">
          <path
            d="M0 320 L0 190 Q 180 70 380 155 Q 560 235 720 145 Q 900 65 1080 165 Q 1240 235 1440 125 L1440 320 Z"
            fill="rgba(255,255,255,0.06)"
          />
          <path
            d="M0 320 L0 235 Q 240 135 480 205 Q 720 285 960 195 Q 1200 115 1440 215 L1440 320 Z"
            fill="rgba(255,255,255,0.05)"
          />
        </svg>
      </div>
      <div class="tea-page hero-inner">
        <p class="hero-eyebrow tea-animate">TEA · 甄选好茶</p>
        <h1 class="hero-title tea-animate">
          一盏清茶<br /><span>品尽山水风韵</span>
        </h1>
        <p class="hero-sub tea-animate">从山野茶园到你的杯盏，每一片茶叶都值得被认真对待。</p>
        <div class="hero-actions tea-animate">
          <el-button type="primary" size="large" round @click="goProducts">选购好茶</el-button>
          <el-button class="hero-ghost" size="large" round plain @click="scrollToCategories">
            浏览分类
          </el-button>
        </div>
        <div class="hero-stats tea-animate">
          <div class="stat">
            <b>{{ categories.length }}</b>
            <span>大茶类</span>
          </div>
          <div class="stat-divider"></div>
          <div class="stat">
            <b>{{ total }}</b>
            <span>款好茶</span>
          </div>
        </div>
      </div>
    </section>

    <!-- 茶类展示 -->
    <section id="categories" class="section">
      <div class="tea-page">
        <div class="section-head tea-animate">
          <p class="section-eyebrow">CATEGORIES</p>
          <h2 class="section-title">茶类甄选</h2>
          <p class="section-sub">按茶系挑选你钟爱的风味</p>
        </div>
        <div class="category-grid">
          <button
            class="category-card all"
            :class="{ active: activeCategoryId === null }"
            type="button"
            @click="selectCategory(null)"
          >
            <span class="category-mark all">全</span>
            <span class="category-name">全部</span>
          </button>
          <button
            v-for="(category, index) in categories"
            :key="category.id"
            class="category-card"
            :class="{ active: activeCategoryId === category.id }"
            type="button"
            @click="selectCategory(category.id)"
          >
            <span class="category-mark" :style="{ background: markStyle(index) }">
              {{ category.name.charAt(0) }}
            </span>
            <span class="category-name">{{ category.name }}</span>
          </button>
        </div>
      </div>
    </section>

    <!-- 商品推荐 -->
    <section class="section products-section">
      <div class="tea-page">
        <div class="section-head head-row tea-animate">
          <div>
            <p class="section-eyebrow">FEATURED</p>
            <h2 class="section-title">当季推荐</h2>
          </div>
          <el-button class="more-link" link @click="goProducts">
            查看全部
            <el-icon><ArrowRight /></el-icon>
          </el-button>
        </div>
        <div v-loading="loading">
          <div v-if="products.length" class="product-grid">
            <ProductCard v-for="product in products" :key="product.id" :product="product" />
          </div>
          <EmptyState v-else message="暂无商品" />
        </div>
        <PaginationBar
          :total="total"
          :page="page"
          :page-size="pageSize"
          @update:page="onPageChange"
        />
      </div>
    </section>

    <!-- 品牌介绍 -->
    <section class="section story-section">
      <div class="tea-page story-inner">
        <div class="story-art" aria-hidden="true">
          <div class="art-ring art-ring-1"></div>
          <div class="art-ring art-ring-2"></div>
          <TeaMark :size="110" class="art-leaf" />
        </div>
        <div class="story-text">
          <p class="section-eyebrow">OUR STORY</p>
          <h2 class="section-title">茶，是时间的艺术</h2>
          <p class="story-p">
            好茶讲究天时、地利与手艺。我们相信，一杯值得回味的茶，
            来自对原料的挑剔，也来自对每一道工序的耐心。
          </p>
          <p class="story-p">
            从绿茶、红茶到乌龙、普洱，每一片茶叶都有自己的性格。
            选对茶，也选对喝茶的心情。
          </p>
        </div>
      </div>
    </section>

    <AppFooter />
  </div>
</template>

<script setup lang="ts">
import { ArrowRight } from '@element-plus/icons-vue'
import { onMounted, ref } from 'vue'
import { useRouter } from 'vue-router'

import { getCategories } from '@/api/categories'
import { getProducts } from '@/api/products'
import AppFooter from '@/components/AppFooter.vue'
import AppHeader from '@/components/AppHeader.vue'
import EmptyState from '@/components/EmptyState.vue'
import PaginationBar from '@/components/PaginationBar.vue'
import ProductCard from '@/components/ProductCard.vue'
import TeaMark from '@/components/TeaMark.vue'
import type { Category } from '@/types/category'
import type { Product } from '@/types/product'

const router = useRouter()
const categories = ref<Category[]>([])
const products = ref<Product[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = 12
const activeCategoryId = ref<number | null>(null)
const loading = ref(false)

const markPalette = [
  'linear-gradient(135deg, #35684b, #28503a)',
  'linear-gradient(135deg, #b98a3f, #8f6a2c)',
  'linear-gradient(135deg, #6a5c4a, #4a3f33)',
  'linear-gradient(135deg, #7c5a3a, #5b3f26)',
  'linear-gradient(135deg, #3f6b5e, #2c4f44)',
  'linear-gradient(135deg, #8d6f4f, #6b4f32)',
]

function markStyle(index: number) {
  return markPalette[index % markPalette.length]
}

async function loadCategories() {
  const { data } = await getCategories()
  categories.value = data
}

async function loadProducts() {
  loading.value = true
  try {
    const { data } = await getProducts({
      category_id: activeCategoryId.value ?? undefined,
      page: page.value,
      page_size: pageSize,
    })
    products.value = data.items
    total.value = data.total
  } finally {
    loading.value = false
  }
}

function selectCategory(categoryId: number | null) {
  activeCategoryId.value = categoryId
  page.value = 1
  loadProducts()
}

function onPageChange(newPage: number) {
  page.value = newPage
  loadProducts()
}

function goProducts() {
  router.push('/products')
}

function scrollToCategories() {
  document.getElementById('categories')?.scrollIntoView({ behavior: 'smooth' })
}

onMounted(() => {
  loadCategories()
  loadProducts()
})
</script>

<style scoped>
.hero {
  position: relative;
  overflow: hidden;
  background:
    radial-gradient(900px 420px at 82% -10%, rgba(169, 126, 58, 0.32), transparent 60%),
    linear-gradient(160deg, #1c3a2a 0%, #2f5e43 55%, #3a6f50 100%);
  color: #f6f2ea;
}

.hero-art {
  position: absolute;
  inset: 0;
  pointer-events: none;
}

.hero-glow {
  position: absolute;
  top: -120px;
  right: -80px;
  width: 480px;
  height: 480px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(169, 126, 58, 0.28), transparent 65%);
}

.hero-mountains {
  position: absolute;
  left: 0;
  right: 0;
  bottom: -1px;
  width: 100%;
  height: 280px;
}

.hero-inner {
  position: relative;
  padding-top: 96px;
  padding-bottom: 120px;
  max-width: 1200px;
}

.hero-eyebrow {
  margin: 0 0 18px;
  font-size: 13px;
  letter-spacing: 0.42em;
  color: #d9b877;
}

.hero-title {
  margin: 0;
  font-family: var(--tea-font-serif);
  font-size: 52px;
  line-height: 1.28;
  font-weight: 700;
  letter-spacing: 0.06em;
}

.hero-title span {
  color: #d9b877;
}

.hero-sub {
  margin: 22px 0 0;
  font-size: 16px;
  line-height: 1.9;
  color: rgba(246, 242, 234, 0.78);
  max-width: 520px;
}

.hero-actions {
  display: flex;
  gap: 14px;
  margin-top: 36px;
}

.hero-ghost {
  background: rgba(255, 255, 255, 0.14);
  border: 1px solid rgba(255, 255, 255, 0.85);
  color: #ffffff;
  box-shadow: none;
}

.hero-ghost:hover,
.hero-ghost:focus {
  background: rgba(255, 255, 255, 0.24);
  border-color: #ffffff;
  color: #ffffff;
}

.hero-stats {
  display: flex;
  align-items: center;
  gap: 28px;
  margin-top: 52px;
}

.stat {
  display: flex;
  align-items: baseline;
  gap: 8px;
}

.stat b {
  font-family: var(--tea-font-serif);
  font-size: 32px;
  line-height: 1;
  font-variant-numeric: tabular-nums;
  color: #d9b877;
  display: inline-block;
  min-width: 48px;
  text-align: center;
}

.stat span {
  font-size: 13px;
  color: rgba(246, 242, 234, 0.68);
}

.stat-divider {
  width: 1px;
  height: 30px;
  background: rgba(246, 242, 234, 0.2);
}

.section {
  padding-top: 76px;
}

.section-head {
  text-align: center;
  margin-bottom: 40px;
}

.section-eyebrow {
  margin: 0 0 10px;
  font-size: 12px;
  letter-spacing: 0.4em;
  color: var(--tea-gold);
}

.section-title {
  margin: 0;
  font-family: var(--tea-font-serif);
  font-size: 32px;
  font-weight: 700;
  letter-spacing: 0.1em;
  color: var(--tea-ink);
}

.section-sub {
  margin: 12px 0 0;
  font-size: 14px;
  color: var(--tea-muted);
}

.head-row {
  display: flex;
  align-items: flex-end;
  justify-content: space-between;
  text-align: left;
}

.more-link {
  color: var(--tea-gold);
  font-size: 14px;
}

.category-grid {
  display: grid;
  grid-template-columns: repeat(auto-fill, minmax(150px, 1fr));
  gap: 18px;
}

.category-card {
  display: flex;
  flex-direction: column;
  align-items: center;
  gap: 14px;
  padding: 26px 16px;
  border: 1px solid var(--tea-line-soft);
  border-radius: var(--tea-radius);
  background: var(--tea-surface);
  cursor: pointer;
  font-family: inherit;
  transition:
    transform 0.25s ease,
    box-shadow 0.25s ease,
    border-color 0.25s ease;
}

.category-card:hover {
  transform: translateY(-4px);
  border-color: rgba(169, 126, 58, 0.45);
  box-shadow: var(--tea-shadow);
}

.category-card.active {
  border-color: var(--tea-gold);
  box-shadow: 0 0 0 3px rgba(169, 126, 58, 0.14), var(--tea-shadow);
}

.category-mark {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 56px;
  height: 56px;
  border-radius: 50%;
  color: #fff;
  font-family: var(--tea-font-serif);
  font-size: 22px;
  font-weight: 700;
  box-shadow: 0 8px 18px rgba(58, 66, 46, 0.18);
}

.category-mark.all {
  background: linear-gradient(135deg, #8b887c, #6b675c);
}

.category-name {
  font-size: 15px;
  font-weight: 600;
  color: var(--tea-ink);
}

.product-grid {
  display: grid;
  grid-template-columns: repeat(4, 1fr);
  gap: 22px;
}

.products-section {
  padding-bottom: 20px;
}

.story-section {
  margin-top: 72px;
  background: linear-gradient(180deg, var(--tea-bg) 0%, var(--tea-bg-deep) 100%);
  padding-bottom: 88px;
}

.story-inner {
  display: grid;
  grid-template-columns: 1fr 1.15fr;
  gap: 72px;
  align-items: center;
}

.story-art {
  position: relative;
  display: flex;
  align-items: center;
  justify-content: center;
  min-height: 320px;
}

.art-ring {
  position: absolute;
  border-radius: 50%;
  border: 1px solid rgba(169, 126, 58, 0.35);
}

.art-ring-1 {
  width: 300px;
  height: 300px;
}

.art-ring-2 {
  width: 230px;
  height: 230px;
  border-style: dashed;
  border-color: rgba(169, 126, 58, 0.28);
}

.art-leaf {
  color: var(--tea-gold);
  filter: drop-shadow(0 14px 28px rgba(169, 126, 58, 0.28));
}

.story-p {
  margin: 20px 0 0;
  font-size: 15px;
  line-height: 2;
  color: var(--tea-ink-2);
}

@media (max-width: 1024px) {
  .hero-title {
    font-size: 42px;
  }
}

@media (max-width: 900px) {
  .product-grid {
    grid-template-columns: repeat(2, 1fr);
  }

  .story-inner {
    grid-template-columns: 1fr;
    gap: 36px;
  }
}

@media (max-width: 640px) {
  .hero-inner {
    padding-top: 64px;
    padding-bottom: 80px;
  }

  .hero-title {
    font-size: 32px;
  }

  .hero-actions {
    flex-direction: column;
    align-items: flex-start;
  }
}
</style>
