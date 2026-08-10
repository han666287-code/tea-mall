<template>
  <div class="auth-shell">
    <div class="auth-backdrop" aria-hidden="true">
      <div class="auth-glow"></div>
      <svg class="auth-leaf auth-leaf-1" viewBox="0 0 48 48" fill="none">
        <path
          d="M24 5.5c-1.2 6.4-5.8 11.6-10.4 15.2C9 24.6 7 28.9 7 33.5c0 7.5 7.6 9.5 17 9.5s17-2 17-9.5c0-4.6-2-8.9-6.6-12.8C29.8 17.1 25.2 11.9 24 5.5Z"
          fill="currentColor"
          opacity="0.16"
        />
      </svg>
      <svg class="auth-leaf auth-leaf-2" viewBox="0 0 48 48" fill="none">
        <path
          d="M24 5.5c-1.2 6.4-5.8 11.6-10.4 15.2C9 24.6 7 28.9 7 33.5c0 7.5 7.6 9.5 17 9.5s17-2 17-9.5c0-4.6-2-8.9-6.6-12.8C29.8 17.1 25.2 11.9 24 5.5Z"
          fill="currentColor"
          opacity="0.12"
        />
      </svg>
      <div class="auth-ring auth-ring-1"></div>
      <div class="auth-ring auth-ring-2"></div>
    </div>

    <div class="auth-card">
      <router-link to="/" class="auth-brand">
        <span class="brand-mark"><TeaMark :size="24" /></span>
        <span class="brand-name">茶叶商城</span>
      </router-link>
      <slot />
      <p class="auth-foot">甄选好茶 · 用心泡好每一杯</p>
    </div>
  </div>
</template>

<script setup lang="ts">
import TeaMark from '@/components/TeaMark.vue'
</script>

<style scoped>
.auth-shell {
  position: relative;
  min-height: 100vh;
  display: flex;
  align-items: center;
  justify-content: center;
  padding: 40px 20px;
  overflow: hidden;
}

.auth-backdrop {
  position: absolute;
  inset: 0;
  background:
    radial-gradient(900px 480px at 78% -10%, rgba(169, 126, 58, 0.3), transparent 60%),
    linear-gradient(155deg, #1c3a2a 0%, #2f5e43 60%, #35684b 100%);
}

.auth-glow {
  position: absolute;
  top: -140px;
  right: -100px;
  width: 520px;
  height: 520px;
  border-radius: 50%;
  background: radial-gradient(circle, rgba(169, 126, 58, 0.26), transparent 64%);
}

.auth-leaf {
  position: absolute;
  color: #f6f2ea;
}

.auth-leaf-1 {
  top: 12%;
  left: 6%;
  width: 150px;
  transform: rotate(-24deg);
}

.auth-leaf-2 {
  right: 8%;
  bottom: 10%;
  width: 110px;
  transform: rotate(30deg);
}

.auth-ring {
  position: absolute;
  border: 1px solid rgba(246, 242, 234, 0.14);
  border-radius: 50%;
}

.auth-ring-1 {
  top: -120px;
  left: -120px;
  width: 360px;
  height: 360px;
}

.auth-ring-2 {
  right: -90px;
  bottom: -90px;
  width: 280px;
  height: 280px;
}

.auth-card {
  position: relative;
  width: 420px;
  max-width: 100%;
  padding: 44px 42px 32px;
  border-radius: var(--tea-radius-lg);
  background: rgba(255, 255, 255, 0.96);
  backdrop-filter: blur(10px);
  box-shadow: var(--tea-shadow-lg);
  animation: tea-fade-up 0.5s cubic-bezier(0.22, 0.61, 0.36, 1) both;
}

.auth-brand {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 12px;
  margin-bottom: 32px;
  text-decoration: none;
  color: var(--tea-ink);
}

.brand-mark {
  display: flex;
  align-items: center;
  justify-content: center;
  width: 44px;
  height: 44px;
  border-radius: 50%;
  background: linear-gradient(135deg, var(--tea-primary), var(--tea-primary-deep));
  color: #fff;
  box-shadow: 0 8px 18px rgba(47, 94, 67, 0.3);
}

.brand-name {
  font-family: var(--tea-font-serif);
  font-size: 22px;
  font-weight: 700;
  letter-spacing: 0.16em;
}

.auth-foot {
  margin: 28px 0 0;
  text-align: center;
  font-size: 12px;
  letter-spacing: 0.24em;
  color: var(--tea-muted);
}

@keyframes tea-fade-up {
  from {
    opacity: 0;
    transform: translateY(18px);
  }
  to {
    opacity: 1;
    transform: translateY(0);
  }
}
</style>
