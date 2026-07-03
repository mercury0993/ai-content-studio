<template>
  <div class="auth-page">
    <div class="auth-panel">
      <div class="auth-header">
        <h1>{{ title }}</h1>
        <p>{{ subtitle }}</p>
      </div>
      <slot />
      <div class="auth-footer">
        <slot name="footer" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
defineProps<{ title: string; subtitle: string }>()
</script>

<style scoped>
.auth-page {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: #f0f2f5;
}
.auth-panel {
  width: 400px;
  padding: 40px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06), 0 4px 24px rgba(0, 0, 0, 0.04);
}
.auth-header {
  text-align: center;
  margin-bottom: 32px;
}
.auth-header h1 {
  font-size: 24px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  margin: 0 0 8px;
  letter-spacing: -0.02em;
}
.auth-header p {
  font-size: 14px;
  color: var(--el-text-color-secondary);
  margin: 0;
}
.auth-footer {
  text-align: center;
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin-top: 24px;
}
.auth-footer a {
  color: var(--el-color-primary);
  text-decoration: none;
  font-weight: 500;
}
.auth-footer a:hover {
  text-decoration: underline;
}
</style>
