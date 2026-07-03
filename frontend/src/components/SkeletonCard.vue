<template>
  <div class="skeleton-card">
    <div class="skeleton-block skeleton-value"></div>
    <div class="skeleton-block skeleton-label"></div>
  </div>
</template>

<style scoped>
.skeleton-card {
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  border: 1px solid var(--el-border-color);
  text-align: center;
}
.skeleton-block {
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
  margin: 0 auto;
}
.skeleton-value {
  height: 36px;
  width: 60%;
  margin-bottom: 12px;
}
.skeleton-label {
  height: 14px;
  width: 40%;
}
@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>
