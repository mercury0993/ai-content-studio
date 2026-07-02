<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'

const userStore = useUserStore()
const router = useRouter()
const isCollapse = ref(false)

function handleCommand(command: string) {
  if (command === 'logout') {
    userStore.logout()
  } else if (command === 'settings') {
    router.push('/settings')
  }
}
</script>

<template>
  <el-container class="app-shell">
    <el-aside :width="isCollapse ? '64px' : '220px'" class="app-sidebar">
      <div class="sidebar-brand">
        <span v-if="!isCollapse" class="brand-text">AI Studio</span>
        <span v-else class="brand-icon">AI</span>
      </div>

      <el-menu
        :default-active="$route.path"
        :collapse="isCollapse"
        background-color="transparent"
        text-color="var(--sidebar-text)"
        active-text-color="var(--sidebar-active-text)"
        router
        class="sidebar-menu"
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataBoard /></el-icon>
          <template #title>数据看板</template>
        </el-menu-item>
        <el-menu-item index="/workspaces">
          <el-icon><Folder /></el-icon>
          <template #title>工作空间</template>
        </el-menu-item>
        <el-menu-item index="/prompts">
          <el-icon><Document /></el-icon>
          <template #title>Prompt 管理</template>
        </el-menu-item>
        <el-menu-item index="/contents">
          <el-icon><EditPen /></el-icon>
          <template #title>内容管理</template>
        </el-menu-item>
        <el-menu-item index="/reviews">
          <el-icon><Checked /></el-icon>
          <template #title>审核中心</template>
        </el-menu-item>
        <el-menu-item index="/models">
          <el-icon><Cpu /></el-icon>
          <template #title>AI 模型</template>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <template #title>个人设置</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container class="app-main">
      <el-header class="app-header">
        <el-icon class="collapse-btn" @click="isCollapse = !isCollapse">
          <Fold v-if="!isCollapse" />
          <Expand v-else />
        </el-icon>

        <div class="header-right">
          <el-dropdown @command="handleCommand" trigger="click">
            <span class="user-trigger">
              <span class="user-avatar">{{ userStore.userInfo?.username?.charAt(0)?.toUpperCase() }}</span>
              <span class="user-name">{{ userStore.userInfo?.username }}</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="settings">
                  <el-icon><Setting /></el-icon>个人设置
                </el-dropdown-item>
                <el-dropdown-item command="logout" divided>
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="app-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.app-shell {
  height: 100vh;
}

.app-sidebar {
  background: var(--sidebar-bg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: width 0.2s ease;
}

.sidebar-brand {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #e5e7eb;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.02em;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  flex-shrink: 0;
}

.sidebar-menu {
  flex: 1;
  border-right: none;
  padding-top: 8px;
}

.sidebar-menu .el-menu-item {
  margin: 2px 8px;
  border-radius: 6px;
  height: 40px;
  line-height: 40px;
  font-size: 14px;
  transition: all 0.15s ease;
}

.sidebar-menu .el-menu-item:hover {
  background: var(--sidebar-hover-bg);
}

.sidebar-menu .el-menu-item.is-active {
  background: var(--sidebar-active-bg);
  font-weight: 500;
}

.app-main {
  display: flex;
  flex-direction: column;
}

.app-header {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: #fff;
  border-bottom: 1px solid var(--el-border-color);
  flex-shrink: 0;
}

.collapse-btn {
  cursor: pointer;
  font-size: 18px;
  color: var(--el-text-color-secondary);
  transition: color 0.15s;
}

.collapse-btn:hover {
  color: var(--el-text-color-primary);
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-trigger {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: background 0.15s;
}

.user-trigger:hover {
  background: var(--el-bg-color-page);
}

.user-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--el-color-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
}

.user-name {
  font-size: 14px;
  color: var(--el-text-color-primary);
}

.app-content {
  background: var(--el-bg-color-page);
  padding: 24px;
  overflow-y: auto;
}
</style>
