<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { register } from '@/api/auth'
import { ElMessage } from 'element-plus'
import { User, Message, Lock } from '@element-plus/icons-vue'
import AuthLayout from '@/components/AuthLayout.vue'

const router = useRouter()
const form = ref({ username: '', email: '', password: '' })
const loading = ref(false)
const emailRef = ref<any>(null)
const passwordRef = ref<any>(null)

function onUsernameEnter() {
  emailRef.value?.focus()
}
function onEmailEnter() {
  passwordRef.value?.focus()
}

async function handleRegister() {
  if (loading.value) return
  if (!form.value.username || !form.value.email || !form.value.password) {
    ElMessage.warning('请填写所有字段')
    return
  }
  if (form.value.password.length < 8) {
    ElMessage.warning('密码长度至少 8 位')
    return
  }
  loading.value = true
  try {
    await register(form.value.username, form.value.email, form.value.password)
    ElMessage.success('注册成功，请登录')
    router.push('/login')
  } catch {
    // error handled by interceptor
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <AuthLayout title="创建账号" subtitle="注册后即可开始使用">
    <el-form @submit.prevent="handleRegister" class="register-form">
      <el-form-item>
        <el-input
          v-model="form.username"
          placeholder="用户名"
          :prefix-icon="User"
          size="large"
          @keyup.enter="onUsernameEnter"
        />
      </el-form-item>
      <el-form-item>
        <el-input
          ref="emailRef"
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
          placeholder="密码（至少8位）"
          :prefix-icon="Lock"
          size="large"
          show-password
        />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" native-type="submit" :loading="loading" size="large" class="register-btn">
          注册
        </el-button>
      </el-form-item>
    </el-form>

    <template #footer>
      已有账号？<router-link to="/login">登录</router-link>
    </template>
  </AuthLayout>
</template>

<style scoped>
.register-form {
  margin-bottom: 0;
}

.register-btn {
  width: 100%;
  font-weight: 500;
}
</style>
