<script setup lang="ts">
import { ref, reactive } from 'vue'
import { updateProfile, changePassword } from '@/api/auth'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

const userStore = useUserStore()

const profileForm = reactive({
  username: userStore.userInfo?.username || '',
  email: userStore.userInfo?.email || '',
})
const profileLoading = ref(false)

const passwordForm = reactive({
  current_password: '',
  new_password: '',
  confirm_password: '',
})
const passwordLoading = ref(false)

async function handleUpdateProfile() {
  if (!profileForm.username || !profileForm.email) {
    ElMessage.warning('请填写完整信息')
    return
  }
  profileLoading.value = true
  try {
    await updateProfile({ username: profileForm.username, email: profileForm.email })
    await userStore.fetchUser()
    ElMessage.success('个人资料已更新')
  } catch {
    // handled by interceptor
  } finally {
    profileLoading.value = false
  }
}

async function handleChangePassword() {
  if (!passwordForm.current_password || !passwordForm.new_password) {
    ElMessage.warning('请填写密码')
    return
  }
  if (passwordForm.new_password !== passwordForm.confirm_password) {
    ElMessage.warning('两次输入的新密码不一致')
    return
  }
  if (passwordForm.new_password.length < 8) {
    ElMessage.warning('新密码长度至少 8 位')
    return
  }
  passwordLoading.value = true
  try {
    await changePassword({
      current_password: passwordForm.current_password,
      new_password: passwordForm.new_password,
    })
    ElMessage.success('密码已修改，下次登录请使用新密码')
    passwordForm.current_password = ''
    passwordForm.new_password = ''
    passwordForm.confirm_password = ''
  } catch {
    // handled by interceptor
  } finally {
    passwordLoading.value = false
  }
}
</script>

<template>
  <div class="settings-page">
    <h3 class="settings-title">个人设置</h3>

    <el-card class="settings-card">
      <template #header><span class="card-header-title">个人资料</span></template>
      <el-form label-width="100px">
        <el-form-item label="用户名">
          <el-input v-model="profileForm.username" placeholder="用户名" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="profileForm.email" placeholder="邮箱" />
        </el-form-item>
        <el-form-item label="角色">
          <el-tag>{{ userStore.userInfo?.role }}</el-tag>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="profileLoading" @click="handleUpdateProfile">保存修改</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card>
      <template #header><span class="card-header-title">修改密码</span></template>
      <el-form label-width="100px">
        <el-form-item label="当前密码">
          <el-input v-model="passwordForm.current_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="passwordForm.new_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="确认密码">
          <el-input v-model="passwordForm.confirm_password" type="password" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="passwordLoading" @click="handleChangePassword">修改密码</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.settings-page {
  max-width: 600px;
}
.settings-title {
  margin-bottom: 24px;
}
.settings-card {
  margin-bottom: 24px;
}
.card-header-title {
  font-weight: bold;
}
</style>
