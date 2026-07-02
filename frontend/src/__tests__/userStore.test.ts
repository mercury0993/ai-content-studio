import { describe, it, expect, beforeEach, vi } from 'vitest'
import { setActivePinia, createPinia } from 'pinia'
import { useUserStore } from '@/stores/user'

const mockLoginApi = vi.fn()
const mockGetMe = vi.fn()
const mockPush = vi.fn()

vi.mock('@/api/auth', () => ({
  login: (...args: any[]) => mockLoginApi(...args),
  getMe: (...args: any[]) => mockGetMe(...args),
}))

vi.mock('@/router', () => ({
  default: { push: (...args: any[]) => mockPush(...args), currentRoute: { value: { meta: {} } } },
}))

describe('userStore', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
    localStorage.clear()
  })

  it('has no token initially', () => {
    const store = useUserStore()
    expect(store.token).toBe('')
    expect(store.userInfo).toBeNull()
  })

  it('reads token from localStorage', () => {
    localStorage.setItem('access_token', 'test-token')
    setActivePinia(createPinia())
    const store = useUserStore()
    expect(store.token).toBe('test-token')
  })

  it('login sets tokens and redirects to dashboard', async () => {
    const store = useUserStore()
    mockLoginApi.mockResolvedValue({ access_token: 'at', refresh_token: 'rt' })
    mockGetMe.mockResolvedValue({ id: '1', username: 'u', email: 'e@b.com', role: 'editor' })

    await store.login('e@b.com', 'password')

    expect(mockLoginApi).toHaveBeenCalledWith('e@b.com', 'password')
    expect(store.token).toBe('at')
    expect(localStorage.getItem('access_token')).toBe('at')
    expect(localStorage.getItem('refresh_token')).toBe('rt')
    expect(store.userInfo).toEqual({ id: '1', username: 'u', email: 'e@b.com', role: 'editor' })
    expect(mockPush).toHaveBeenCalledWith('/dashboard')
  })

  it('logout clears state and redirects to login', () => {
    localStorage.setItem('access_token', 'old')
    setActivePinia(createPinia())
    const store = useUserStore()

    store.logout()

    expect(store.token).toBe('')
    expect(store.userInfo).toBeNull()
    expect(localStorage.getItem('access_token')).toBeNull()
    expect(mockPush).toHaveBeenCalledWith('/login')
  })
})
