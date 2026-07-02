import { describe, it, expect, beforeEach } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { hasPermission, canEdit } from '@/utils/permission'
import { useUserStore } from '@/stores/user'

describe('permission', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
  })

  it('returns false when user is not logged in', () => {
    expect(hasPermission('/dashboard')).toBe(false)
    expect(canEdit()).toBe(false)
  })

  it('admin has full access', () => {
    const store = useUserStore()
    store.$patch({ userInfo: { id: '1', username: 'a', email: 'a@b.com', role: 'admin' } })

    expect(hasPermission('/dashboard')).toBe(true)
    expect(hasPermission('/workspaces')).toBe(true)
    expect(hasPermission('/prompts')).toBe(true)
    expect(hasPermission('/reviews')).toBe(true)
    expect(hasPermission('/models')).toBe(true)
    expect(hasPermission('/settings')).toBe(true)
    expect(canEdit()).toBe(true)
  })

  it('editor has limited access', () => {
    const store = useUserStore()
    store.$patch({ userInfo: { id: '2', username: 'e', email: 'e@b.com', role: 'editor' } })

    expect(hasPermission('/dashboard')).toBe(true)
    expect(hasPermission('/prompts')).toBe(true)
    expect(hasPermission('/reviews')).toBe(true)
    expect(hasPermission('/workspaces')).toBe(false)
    expect(hasPermission('/models')).toBe(false)
    expect(canEdit()).toBe(true)
  })

  it('viewer has read-only access', () => {
    const store = useUserStore()
    store.$patch({ userInfo: { id: '3', username: 'v', email: 'v@b.com', role: 'viewer' } })

    expect(hasPermission('/dashboard')).toBe(true)
    expect(hasPermission('/contents')).toBe(true)
    expect(hasPermission('/prompts')).toBe(false)
    expect(hasPermission('/reviews')).toBe(false)
    expect(canEdit()).toBe(false)
  })
})
