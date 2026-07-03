<script setup lang="ts">
import { onErrorCaptured } from 'vue'

onErrorCaptured((err) => {
  console.error('Captured:', err)
  return false // prevent propagation
})
</script>

<template>
  <router-view />
</template>
