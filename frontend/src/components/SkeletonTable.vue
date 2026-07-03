<template>
  <div class="skeleton-table">
    <div class="skeleton-row" v-for="i in 5" :key="i">
      <div class="skeleton-block" :style="{ width: widths[i % widths.length] }"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
const widths = ['60%', '40%', '50%', '35%', '55%']
</script>

<style scoped>
.skeleton-table {
  background: #fff;
  border-radius: 8px;
  border: 1px solid var(--el-border-color);
  padding: 16px;
}
.skeleton-row {
  padding: 12px 0;
  border-bottom: 1px solid var(--el-border-color-light);
}
.skeleton-row:last-child {
  border-bottom: none;
}
.skeleton-block {
  height: 16px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
}
@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>
