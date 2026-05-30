<script setup lang="ts">
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
</script>

<template>
  <div>
    <h2>数据看板</h2>
    <p>欢迎, {{ userStore.userInfo?.username }}！</p>
    <p>角色: {{ userStore.userInfo?.role }}</p>
  </div>
</template>
