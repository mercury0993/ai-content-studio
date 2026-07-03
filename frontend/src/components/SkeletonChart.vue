<template>
  <div class="skeleton-chart">
    <div class="skeleton-block skeleton-title"></div>
    <div class="skeleton-block skeleton-body"></div>
  </div>
</template>

<style scoped>
.skeleton-chart {
  background: #fff;
  border-radius: 8px;
  border: 1px solid var(--el-border-color);
  padding: 20px;
}
.skeleton-block {
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
}
.skeleton-title {
  height: 16px;
  width: 30%;
  margin-bottom: 16px;
}
.skeleton-body {
  height: 280px;
  width: 100%;
}
@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>
