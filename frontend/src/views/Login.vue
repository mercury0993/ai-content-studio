<script setup lang="ts">
import { ref } from 'vue'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'
import { Message, Lock } from '@element-plus/icons-vue'
import AuthLayout from '@/components/AuthLayout.vue'

const userStore = useUserStore()
const form = ref({ email: '', password: '' })
const loading = ref(false)
const passwordRef = ref<any>(null)

function onEmailEnter() {
  passwordRef.value?.focus()
}

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
  <AuthLayout title="AI Content Studio" subtitle="登录以继续使用">
    <el-form @submit.prevent="handleLogin" class="login-form">
      <el-form-item>
        <el-input
          v-model="form.email"
          placeholder="邮箱"
          :prefix-icon="Message"
          size="large"
          @keyup.enter="onEmailEnter"
        />
      </el-form-item>
      <el-form-item>
        <el-input
          ref="passwordRef"
          v-model="form.password"
          type="password"
          placeholder="密码"
          :prefix-icon="Lock"
          size="large"
          show-password
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" native-type="submit" :loading="loading" size="large" class="login-btn">
          登录
        </el-button>
      </el-form-item>
    </el-form>

    <template #footer>
      没有账号？<router-link to="/register">注册</router-link>
    </template>
  </AuthLayout>
</template>

<style scoped>
.login-form {
  margin-bottom: 0;
}

.login-btn {
  width: 100%;
  font-weight: 500;
}
</style>
