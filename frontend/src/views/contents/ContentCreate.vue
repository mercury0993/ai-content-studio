<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkspaceStore } from '@/stores/workspace'
import { listPrompts } from '@/api/prompts'
import { listModels } from '@/api/aiModels'
import { generateContentStream } from '@/api/contents'
import { ElMessage } from 'element-plus'

const router = useRouter()
const workspaceStore = useWorkspaceStore()

const prompts = ref<any[]>([])
const models = ref<any[]>([])
const selectedPrompt = ref<any>(null)
const selectedModelId = ref('')
const variables = ref<Record<string, string>>({})
const generating = ref(false)
const resultText = ref('')
const showResult = ref(false)

onMounted(async () => {
  if (!workspaceStore.currentWorkspace) return
  const promptData: any = await listPrompts({ workspace_id: workspaceStore.currentWorkspace.id, page_size: 100 })
  prompts.value = promptData.data.items
  models.value = await listModels(workspaceStore.currentWorkspace.id) as any
})

function onPromptChange() {
  const prompt = prompts.value.find((p) => p.id === selectedPrompt.value)
  if (prompt) {
    variables.value = {}
    for (const v of prompt.variables || []) {
      variables.value[v.name] = ''
    }
  }
}

async function handleGenerate() {
  if (!selectedPrompt.value || !selectedModelId.value) {
    ElMessage.warning('请选择 Prompt 和模型')
    return
  }
  if (!workspaceStore.currentWorkspace) return

  const prompt = prompts.value.find((p) => p.id === selectedPrompt.value)
  for (const v of prompt?.variables || []) {
    if (v.required && !variables.value[v.name]) {
      ElMessage.warning(`请填写变量 ${v.name}`)
      return
    }
  }

  generating.value = true
  showResult.value = true
  resultText.value = ''

  await generateContentStream(
    {
      workspace_id: workspaceStore.currentWorkspace.id,
      prompt_id: selectedPrompt.value,
      model_id: selectedModelId.value,
      variables: variables.value,
    },
    (chunk: string) => {
      resultText.value += chunk
    },
    () => {
      generating.value = false
    },
    (error: string) => {
      ElMessage.error(error)
      generating.value = false
      showResult.value = false
    },
  )
}

function handleCopy() {
  navigator.clipboard.writeText(resultText.value)
  ElMessage.success('已复制到剪贴板')
}
</script>

<template>
  <div>
    <h3>生成内容</h3>
    <el-form label-width="100px" style="max-width: 800px; margin-top: 16px;">
      <el-form-item label="Prompt 模板">
        <el-select v-model="selectedPrompt" placeholder="选择 Prompt" @change="onPromptChange" style="width: 100%;">
          <el-option v-for="p in prompts" :key="p.id" :label="p.title" :value="p.id" />
        </el-select>
      </el-form-item>

      <el-form-item label="AI 模型">
        <el-select v-model="selectedModelId" placeholder="选择模型" style="width: 100%;">
          <el-option v-for="m in models" :key="m.id" :label="`${m.name} (${m.model_name})`" :value="m.id" :disabled="!m.is_active" />
        </el-select>
      </el-form-item>

      <el-form-item v-for="(val, key) in variables" :key="key" :label="key as string">
        <el-input v-model="variables[key]" :placeholder="`请输入 ${key}`" />
      </el-form-item>

      <el-form-item>
        <el-button type="primary" :loading="generating" @click="handleGenerate">生成</el-button>
        <el-button @click="router.push('/contents')">返回列表</el-button>
      </el-form-item>
    </el-form>

    <div v-if="showResult" style="margin-top: 24px; max-width: 800px;">
      <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 8px;">
        <h4>生成结果</h4>
        <el-button size="small" @click="handleCopy" :disabled="generating">复制</el-button>
      </div>
      <el-input type="textarea" :model-value="resultText" :rows="15" readonly />
    </div>
  </div>
</template>
