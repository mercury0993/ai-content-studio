import axios from 'axios'
import { ElMessage } from 'element-plus'
import router from '@/router'

const request = axios.create({
  baseURL: '/api/v1',
  timeout: 10000,
})

request.interceptors.request.use((config) => {
  const token = localStorage.getItem('access_token')
  if (token) {
    config.headers.Authorization = `Bearer ${token}`
  }
  return config
})

request.interceptors.response.use(
  (response) => response.data,
  (error) => {
    if (error.response?.status === 401) {
      const isPublicPage = router.currentRoute.value.meta?.public
      localStorage.removeItem('access_token')
      localStorage.removeItem('refresh_token')
      if (isPublicPage) {
        ElMessage.error(error.response?.data?.detail || '请求失败')
      } else {
        router.push('/login')
        ElMessage.error('登录已过期，请重新登录')
      }
    } else {
      ElMessage.error(error.response?.data?.detail || '请求失败')
    }
    return Promise.reject(error)
  }
)

export default request
