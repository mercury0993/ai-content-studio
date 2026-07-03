<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getPrompt, updatePrompt } from '@/api/prompts'
import { promptCategories } from '@/utils/common'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const loading = ref(false)
const form = ref({
  title: '',
  content: '',
  category: '',
  tags: [] as string[],
  tagInput: '',
})

onMounted(async () => {
  const data: any = await getPrompt(route.params.id as string)
  form.value.title = data.title
  form.value.content = data.content
  form.value.category = data.category || ''
  form.value.tags = data.tags || []
})

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
  loading.value = true
  try {
    await updatePrompt(route.params.id as string, {
      title: form.value.title,
      content: form.value.content,
      category: form.value.category || undefined,
      tags: form.value.tags.length > 0 ? form.value.tags : undefined,
    })
    ElMessage.success('保存成功')
    router.push('/prompts')
  } finally {
    loading.value = false
  }
}
</script>

<template>
  <div>
    <h3>编辑 Prompt</h3>
    <el-form label-width="80px" style="max-width: 800px; margin-top: 16px;">
      <el-form-item label="标题">
        <el-input v-model="form.title" />
      </el-form-item>
      <el-form-item label="分类">
        <el-select v-model="form.category" clearable>
          <el-option v-for="c in promptCategories" :key="c.value" :label="c.label" :value="c.value" />
        </el-select>
      </el-form-item>
      <el-form-item label="标签">
        <div>
          <el-tag v-for="tag in form.tags" :key="tag" closable @close="removeTag(tag)" style="margin-right: 4px; margin-bottom: 4px;">{{ tag }}</el-tag>
          <el-input v-model="form.tagInput" size="small" style="width: 120px;" placeholder="添加标签" @keyup.enter="addTag" />
        </div>
      </el-form-item>
      <el-form-item label="内容">
        <el-input v-model="form.content" type="textarea" :rows="10" />
      </el-form-item>
      <el-form-item>
        <el-button type="primary" :loading="loading" @click="handleSubmit">保存</el-button>
        <el-button @click="router.push('/prompts')">取消</el-button>
      </el-form-item>
    </el-form>
  </div>
</template>
