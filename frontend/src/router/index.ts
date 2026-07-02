import { createRouter, createWebHistory } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useWorkspaceStore } from '@/stores/workspace'

const routes = [
  {
    path: '/login',
    component: () => import('@/views/Login.vue'),
    meta: { public: true },
  },
  {
    path: '/register',
    component: () => import('@/views/Register.vue'),
    meta: { public: true },
  },
  {
    path: '/',
    component: () => import('@/layouts/MainLayout.vue'),
    redirect: '/dashboard',
    children: [
      {
        path: 'dashboard',
        component: () => import('@/views/Dashboard.vue'),
        meta: { title: '数据看板' },
      },
      {
        path: 'workspaces',
        component: () => import('@/views/workspaces/WorkspaceList.vue'),
        meta: { title: '工作空间' },
      },
      {
        path: 'workspaces/:id',
        component: () => import('@/views/workspaces/WorkspaceDetail.vue'),
        meta: { title: '空间详情' },
      },
      {
        path: 'prompts',
        component: () => import('@/views/prompts/PromptList.vue'),
        meta: { title: 'Prompt 管理' },
      },
      {
        path: 'prompts/create',
        component: () => import('@/views/prompts/PromptCreate.vue'),
        meta: { title: '新建 Prompt' },
      },
      {
        path: 'prompts/:id/edit',
        component: () => import('@/views/prompts/PromptEdit.vue'),
        meta: { title: '编辑 Prompt' },
      },
      {
        path: 'prompts/:id/versions',
        component: () => import('@/views/prompts/PromptVersions.vue'),
        meta: { title: '版本历史' },
      },
      {
        path: 'models',
        component: () => import('@/views/models/ModelList.vue'),
        meta: { title: 'AI 模型' },
      },
      {
        path: 'contents',
        component: () => import('@/views/contents/ContentList.vue'),
        meta: { title: '内容管理' },
      },
      {
        path: 'contents/create',
        component: () => import('@/views/contents/ContentCreate.vue'),
        meta: { title: '生成内容' },
      },
      {
        path: 'contents/:id',
        component: () => import('@/views/contents/ContentDetail.vue'),
        meta: { title: '内容详情' },
      },
      {
        path: 'reviews',
        component: () => import('@/views/reviews/ReviewCenter.vue'),
        meta: { title: '审核中心' },
      },
      {
        path: 'settings',
        component: () => import('@/views/Settings.vue'),
        meta: { title: '个人设置' },
      },
    ],
  },
]

const router = createRouter({
  history: createWebHistory(),
  routes,
})

router.beforeEach(async (to, from, next) => {
  const userStore = useUserStore()
  const workspaceStore = useWorkspaceStore()

  if (to.meta.public) {
    next()
    return
  }

  if (!userStore.token) {
    next('/login')
    return
  }

  if (!userStore.userInfo) {
    try {
      await userStore.fetchUser()
    } catch {
      next('/login')
      return
    }
  }

  // Ensure workspaces are loaded on first navigation
  if (workspaceStore.workspaces.length === 0) {
    try {
      await workspaceStore.fetchWorkspaces()
    } catch {
      // Non-critical, pages will show workspace warning
    }
  }

  next()
})

export default router
