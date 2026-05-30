<script setup lang="ts">
import { ref } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkspaceStore } from '@/stores/workspace'
import { createPrompt } from '@/api/prompts'
import { ElMessage } from 'element-plus'

const router = useRouter()
const workspaceStore = useWorkspaceStore()
const loading = ref(false)

const form = ref({
  title: '',
  content: '',
  category: '',
  tags: [] as string[],
  tagInput: '',
})

const categories = [
  { label: '营销文案', value: 'marketing' },
  { label: '技术文档', value: 'tech_doc' },
  { label: '社交媒体', value: 'social_media' },
]

function addTag() {
  const tag = form.value.tagInput.trim()
  if (tag && !form.value.tags.includes(tag)) {
    form.value.tags.push(tag)
  }
  form.value.tagInput = ''
}

function removeTag(tag: string) {
  form.value.tags = form.value.tags.filter((t) => t !== tag)
}

async function handleSubmit() {
  if (!form.value.title || !form.value.content) {
    ElMessage.warning('请填写标题和内容')
    return
  }
  if (!workspaceStore.currentWorkspace) {
    ElMessage.warning('请先选择工作空间')
    return
  }
  loading.value = true
  try {
    await createPrompt({
      workspace_id: workspaceStore.currentWorkspace.id,
      title: form.value.title,
      content: form.value.content,
      category: form.value.category || undefined,
      tags: form.value.tags.length > 0 ? form.value.tags : undefined,
    })
    ElMessage.success('创建成功')
    router.push('/prompts')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div>
    <h3>新建 Prompt</h3>
    <el-form label-width="80px" style="max-width: 800px; margin-top: 16px;">
      <el-form-item label="标题">
        <el-input v-model="form.title" placeholder="Prompt 标题" />
      </el-form-item>
      <el-form-item label="分类">
        <el-select v-model="form.category" placeholder="选择分类" clearable>
          <el-option v-for="c in categories" :key="c.value" :label="c.label" :value="c.value" />
        </el-select>
      </el-form-item>
      <el-form-item label="标签">
        <div>
          <el-tag v-for="tag in form.tags" :key="tag" closable @close="removeTag(tag)" style="margin-right: 4px; margin-bottom: 4px;">{{ tag }}</el-tag>
          <el-input v-model="form.tagInput" size="small" style="width: 120px;" placeholder="添加标签" @keyup.enter="addTag" />
        </div>
      </el-form-item>
      <el-form-item label="内容">
        <el-input v-model="form.content" type="textarea" :rows="10" placeholder="Prompt 内容，使用 {{变量名}} 定义变量" />
      </el-form-item>
      <el-form-item>
        <p style="color: #999; font-size: 12px;">提示：在内容中使用 {{变量名}} 来定义变量，例如 {{product_name}}、{{target_audience}}</p>
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="loading" @click="handleSubmit">创建</el-button>
        <el-button @click="router.push('/prompts')">取消</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>
