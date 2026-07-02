<script setup lang="ts">
import { ref } from 'vue'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import { Message, Lock } from '@element-plus/icons-vue'

const userStore = useUserStore()
const form = ref({ email: '', password: '' })
const loading = ref(false)

async function handleLogin() {
  if (loading.value) return
  if (!form.value.email || !form.value.password) {
    ElMessage.warning('请输入邮箱和密码')
    return
  }
  loading.value = true
  try {
    await userStore.login(form.value.email, form.value.password)
    ElMessage.success('登录成功')
  } catch {
    // error handled by interceptor
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div class="login-container">
    <el-card class="login-card">
      <h2>AI Content Studio</h2>
      <el-form @submit.prevent="handleLogin">
        <el-form-item>
          <el-input v-model="form.email" placeholder="邮箱" :prefix-icon="Message" />
        </el-form-item>
        <el-form-item>
          <el-input v-model="form.password" type="password" placeholder="密码" :prefix-icon="Lock" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" native-type="submit" :loading="loading" style="width:100%">登录</el-button>
        </el-form-item>
        <div style="text-align:center">
          <router-link to="/register">没有账号？注册</router-link>
        </div>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.login-container {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: #f0f2f5;
}
.login-card {
  width: 400px;
}
.login-card h2 {
  text-align: center;
  margin-bottom: 24px;
}
</style>
