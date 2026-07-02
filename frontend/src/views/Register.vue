<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { register } from '@/api/auth'
import { ElMessage } from 'element-plus'
import { User, Message, Lock } from '@element-plus/icons-vue'

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
  <div class="login-page">
    <div class="login-panel">
      <div class="login-header">
        <h1>创建账号</h1>
        <p>注册后即可开始使用</p>
      </div>

      <el-form @submit.prevent="handleRegister" class="login-form">
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
          <el-button type="primary" native-type="submit" :loading="loading" size="large" class="login-btn">
            注册
          </el-button>
        </el-form-item>
      </el-form>

      <div class="login-footer">
        已有账号？<router-link to="/login">登录</router-link>
      </div>
    </div>
  </div>
</template>

<style scoped>
.login-page {
  display: flex;
  justify-content: center;
  align-items: center;
  height: 100vh;
  background: #f0f2f5;
}

.login-panel {
  width: 400px;
  padding: 40px;
  background: #fff;
  border-radius: 12px;
  box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06), 0 4px 24px rgba(0, 0, 0, 0.04);
}

.login-header {
  text-align: center;
  margin-bottom: 32px;
}

.login-header h1 {
  font-size: 24px;
  font-weight: 700;
  color: var(--el-text-color-primary);
  margin: 0 0 8px;
  letter-spacing: -0.02em;
}

.login-header p {
  font-size: 14px;
  color: var(--el-text-color-secondary);
  margin: 0;
}

.login-form {
  margin-bottom: 0;
}

.login-btn {
  width: 100%;
  font-weight: 500;
}

.login-footer {
  text-align: center;
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin-top: 24px;
}

.login-footer a {
  color: var(--el-color-primary);
  text-decoration: none;
  font-weight: 500;
}

.login-footer a:hover {
  text-decoration: underline;
}
</style>
