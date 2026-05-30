<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getContent, updateContent } from '@/api/contents'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const content = ref<any>(null)
const editText = ref('')
const editing = ref(false)

onMounted(async () => {
  content.value = await getContent(route.params.id as string)
  editText.value = content.value.edited_text || content.value.generated_text
})

async function handleSave() {
  await updateContent(content.value.id, { edited_text: editText.value })
  ElMessage.success('保存成功')
  editing.value = false
  content.value = await getContent(route.params.id as string)
}

function handleCopy() {
  navigator.clipboard.writeText(editText.value)
  ElMessage.success('已复制到剪贴板')
}

async function handleExportMarkdown() {
  const token = localStorage.getItem('access_token')
  const resp = await fetch(`/api/v1/export/markdown/${content.value.id}`, {
    headers: { Authorization: `Bearer ${token}` },
  })
  if (!resp.ok) {
    ElMessage.error('导出失败')
    return
  }
  const blob = await resp.blob()
  const url = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = url
  a.download = `content_${content.value.id.slice(0, 8)}.md`
  a.click()
  URL.revokeObjectURL(url)
}
</script>

<template>
  <div v-if="content">
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
      <h3>内容详情</h3>
      <div>
        <el-button @click="handleCopy">复制</el-button>
        <el-button v-if="!editing" @click="editing = true">编辑</el-button>
        <el-button v-if="editing" type="primary" @click="handleSave">保存</el-button>
        <el-button @click="handleExportMarkdown">导出 Markdown</el-button>
        <el-button @click="router.push('/contents')">返回列表</el-button>
      </div>
    </div>

    <el-descriptions :column="2" border style="margin-bottom: 16px;">
      <el-descriptions-item label="状态">{{ content.status }}</el-descriptions-item>
      <el-descriptions-item label="Token 消耗">{{ content.token_usage }}</el-descriptions-item>
      <el-descriptions-item label="生成耗时">{{ content.generation_time_ms }}ms</el-descriptions-item>
      <el-descriptions-item label="创建时间">{{ new Date(content.created_at).toLocaleString() }}</el-descriptions-item>
    </el-descriptions>

    <el-input v-model="editText" type="textarea" :rows="15" :readonly="!editing" />
  </div>
</template>
