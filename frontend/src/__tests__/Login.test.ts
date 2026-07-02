import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import { ElMessage } from 'element-plus'
import Login from '@/views/Login.vue'

const mockLogin = vi.fn()
const mockPush = vi.fn()

vi.mock('@/stores/user', () => ({
  useUserStore: () => ({
    login: mockLogin,
    token: '',
    userInfo: null,
  }),
}))

vi.mock('@/router', () => ({
  default: { push: mockPush, currentRoute: { value: { meta: {} } } },
}))

vi.mock('element-plus', async () => {
  const actual = await vi.importActual('element-plus')
  return { ...actual }
})

describe('Login.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  function mountLogin() {
    return mount(Login, {
      global: { stubs: { 'router-link': true } },
    })
  }

  it('renders login form', () => {
    const wrapper = mountLogin()
    expect(wrapper.find('h1').text()).toBe('AI Content Studio')
    expect(wrapper.find('input[placeholder="邮箱"]').exists()).toBe(true)
    expect(wrapper.find('input[placeholder="密码"]').exists()).toBe(true)
  })

  it('shows warning when fields are empty', async () => {
    const spy = vi.spyOn(ElMessage, 'warning')
    const wrapper = mountLogin()
    await wrapper.find('form').trigger('submit.prevent')
    expect(spy).toHaveBeenCalledWith('请输入邮箱和密码')
  })

  it('calls login when form is submitted', async () => {
    const wrapper = mountLogin()
    await wrapper.find('input[placeholder="邮箱"]').setValue('a@b.com')
    await wrapper.find('input[placeholder="密码"]').setValue('password123')
    mockLogin.mockResolvedValue(undefined)
    await wrapper.find('form').trigger('submit.prevent')
    expect(mockLogin).toHaveBeenCalledWith('a@b.com', 'password123')
  })
})
