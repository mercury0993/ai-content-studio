import { useUserStore } from '@/stores/user'

const roleMenus: Record<string, string[]> = {
  admin: ['/dashboard', '/workspaces', '/prompts', '/contents', '/reviews', '/models', '/settings'],
  editor: ['/dashboard', '/prompts', '/contents', '/reviews'],
  viewer: ['/dashboard', '/contents'],
}

export function hasPermission(path: string): boolean {
  const userStore = useUserStore()
  if (!userStore.userInfo) return false
  const allowed = roleMenus[userStore.userInfo.role] || []
  return allowed.some((p) => path.startsWith(p))
}

export function canEdit(): boolean {
  const userStore = useUserStore()
  return userStore.userInfo?.role === 'admin' || userStore.userInfo?.role === 'editor'
}
