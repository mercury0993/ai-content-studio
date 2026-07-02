import { describe, it, expect, beforeEach, vi } from 'vitest'
import { mount } from '@vue/test-utils'
import { setActivePinia, createPinia } from 'pinia'
import { ElMessage } from 'element-plus'
import Register from '@/views/Register.vue'

const mockRegister = vi.fn()
const mockPush = vi.fn()

vi.mock('@/api/auth', () => ({
  register: (...args: any[]) => mockRegister(...args),
}))

vi.mock('vue-router', () => ({
  useRouter: () => ({ push: mockPush }),
}))

describe('Register.vue', () => {
  beforeEach(() => {
    setActivePinia(createPinia())
    vi.clearAllMocks()
  })

  function mountRegister() {
    return mount(Register, {
      global: { stubs: { 'router-link': true } },
    })
  }

  it('renders register form', () => {
    const wrapper = mountRegister()
    expect(wrapper.find('h2').text()).toBe('注册账号')
    expect(wrapper.find('input[placeholder="用户名"]').exists()).toBe(true)
    expect(wrapper.find('input[placeholder="邮箱"]').exists()).toBe(true)
    expect(wrapper.find('input[placeholder="密码"]').exists()).toBe(true)
  })

  it('shows warning when fields are empty', async () => {
    const spy = vi.spyOn(ElMessage, 'warning')
    const wrapper = mountRegister()
    await wrapper.find('form').trigger('submit.prevent')
    expect(spy).toHaveBeenCalledWith('请填写所有字段')
  })

  it('calls register API and redirects on success', async () => {
    const wrapper = mountRegister()
    await wrapper.find('input[placeholder="用户名"]').setValue('newuser')
    await wrapper.find('input[placeholder="邮箱"]').setValue('new@test.com')
    await wrapper.find('input[placeholder="密码"]').setValue('password123')
    mockRegister.mockResolvedValue({ id: '1' })
    await wrapper.find('form').trigger('submit.prevent')
    expect(mockRegister).toHaveBeenCalledWith('newuser', 'new@test.com', 'password123')
    expect(mockPush).toHaveBeenCalledWith('/login')
  })

  it('does not call API when loading', async () => {
    const wrapper = mountRegister()
    await wrapper.find('input[placeholder="用户名"]').setValue('newuser')
    await wrapper.find('input[placeholder="邮箱"]').setValue('new@test.com')
    await wrapper.find('input[placeholder="密码"]').setValue('password123')
    // simulate slow API: don't resolve between triggers
    mockRegister.mockReturnValue(new Promise(() => {}))
    await wrapper.find('form').trigger('submit.prevent')
    await wrapper.find('form').trigger('submit.prevent')
    expect(mockRegister).toHaveBeenCalledTimes(1)
  })
})
