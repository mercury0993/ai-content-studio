import { createApp } from 'vue'
import { createPinia } from 'pinia'
import ElementPlus from 'element-plus'
import { ElMessage } from 'element-plus'
import 'element-plus/dist/index.css'
import './styles/theme.css'
import App from './App.vue'
import router from './router'

const app = createApp(App)
app.use(createPinia())
app.use(router)
app.use(ElementPlus)

app.config.errorHandler = (err: unknown) => {
  console.error('Global error:', err)
  const msg = err instanceof Error ? err.message : '未知错误'
  ElMessage.error(`应用错误: ${msg}`)
}

app.mount('#app')
