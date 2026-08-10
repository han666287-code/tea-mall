<template>
  <footer class="app-footer">
    <div class="tea-page footer-inner">
      <div class="footer-brand">
        <router-link to="/" class="footer-logo">
          <span class="footer-mark"><TeaMark :size="26" /></span>
          <span class="footer-name">茶叶商城</span>
        </router-link>
        <p class="footer-slogan">甄选好茶，用心泡好每一杯。</p>
      </div>
      <div class="footer-col">
        <h4>逛逛</h4>
        <router-link to="/products">全部好茶</router-link>
        <router-link to="/cart">购物车</router-link>
      </div>
      <div class="footer-col">
        <h4>账户</h4>
        <router-link to="/login">登录</router-link>
        <router-link to="/register">注册</router-link>
      </div>
      <div class="footer-col">
        <h4>服务</h4>
        <router-link to="/orders">我的订单</router-link>
      </div>
    </div>
    <div class="footer-bottom">
      <div class="tea-page">
        <span>© {{ year }} 茶叶商城 TeaMall · 学习项目</span>
      </div>
    </div>
  </footer>
</template>

<script setup lang="ts">
import TeaMark from '@/components/TeaMark.vue'

const year = new Date().getFullYear()
</script>

<style scoped>
.app-footer {
  margin-top: 72px;
  background:
    radial-gradient(1200px 320px at 20% -20%, rgba(169, 126, 58, 0.14), transparent 60%),
    #20382a;
  color: rgba(246, 242, 234, 0.86);
}

.footer-inner {
  display: flex;
  gap: 56px;
  padding-top: 56px;
  padding-bottom: 48px;
}

.footer-brand {
  flex: 1;
  max-width: 320px;
}

.footer-logo {
  display: inline-flex;
  align-items: center;
  gap: 12px;
  text-decoration: none;
  color: #f6f2ea;
}

.footer-mark {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 46px;
  height: 46px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--tea-gold), var(--tea-gold-deep));
  color: #fff;
  box-shadow: 0 8px 20px rgba(0, 0, 0, 0.25);
}

.footer-name {
  font-family: var(--tea-font-serif);
  font-size: 22px;
  font-weight: 700;
  letter-spacing: 0.14em;
}

.footer-slogan {
  margin: 16px 0 0;
  font-size: 14px;
  line-height: 1.8;
  color: rgba(246, 242, 234, 0.62);
}

.footer-col h4 {
  margin: 0 0 16px;
  font-size: 13px;
  font-weight: 600;
  letter-spacing: 0.16em;
  color: var(--tea-gold);
}

.footer-col {
  display: flex;
  flex-direction: column;
  gap: 10px;
  min-width: 120px;
}

.footer-col a {
  color: rgba(246, 242, 234, 0.8);
  text-decoration: none;
  font-size: 14px;
  transition: color 0.2s ease, transform 0.2s ease;
}

.footer-col a:hover {
  color: #fff;
  transform: translateX(3px);
}

.footer-bottom {
  border-top: 1px solid rgba(246, 242, 234, 0.1);
  padding: 18px 0;
  font-size: 13px;
  color: rgba(246, 242, 234, 0.5);
}

@media (max-width: 760px) {
  .footer-inner {
    flex-direction: column;
    gap: 28px;
  }
}
</style>
