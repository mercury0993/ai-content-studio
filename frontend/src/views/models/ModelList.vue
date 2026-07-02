<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useWorkspaceStore } from '@/stores/workspace'
import { listModels, createModel, updateModel, deleteModel, toggleModel } from '@/api/aiModels'
import { canEdit } from '@/utils/permission'
import { ElMessage, ElMessageBox } from 'element-plus'

const workspaceStore = useWorkspaceStore()
const models = ref<any[]>([])
const showCreate = ref(false)
const editingModel = ref<any>(null)
const loading = ref(false)

const providerDefaults: Record<string, { base_url: string; model_name: string }> = {
  openai: { base_url: 'https://api.openai.com/v1', model_name: 'gpt-4o' },
  deepseek: { base_url: 'https://api.deepseek.com', model_name: 'deepseek-chat' },
  claude: { base_url: '', model_name: 'claude-3-opus-20240229' },
  wenxin: { base_url: '', model_name: '' },
}

const form = ref({
  name: '',
  provider: 'deepseek',
  api_key: '',
  base_url: 'https://api.deepseek.com',
  model_name: 'deepseek-chat',
  temperature: 0.7,
  max_tokens: 2000,
})

const providers = [
  { label: 'OpenAI', value: 'openai' },
  { label: 'DeepSeek', value: 'deepseek' },
  { label: 'Claude', value: 'claude' },
  { label: '文心一言', value: 'wenxin' },
]

watch(() => form.value.provider, (newProvider) => {
  const defaults = providerDefaults[newProvider]
  if (defaults) {
    form.value.base_url = defaults.base_url
    form.value.model_name = defaults.model_name
  }
})

async function fetchModels() {
  if (!workspaceStore.currentWorkspace) {
    ElMessage.warning('未加入任何工作空间，请先在"工作空间"页面加入或创建空间')
    return
  }
  loading.value = true
  try {
    models.value = await listModels(workspaceStore.currentWorkspace.id) as any
  } finally {
    loading.value = false
  }
}

onMounted(fetchModels)

async function handleSubmit() {
  if (!form.value.name || !form.value.model_name) {
    ElMessage.warning('请填写模型名称和模型标识')
    return
  }
  if (!workspaceStore.currentWorkspace) {
    ElMessage.warning('未加入任何工作空间，请先在"工作空间"页面加入或创建空间')
    return
  }

  try {
    if (editingModel.value) {
      await updateModel(editingModel.value.id, {
        name: form.value.name,
        provider: form.value.provider,
        api_key: form.value.api_key || undefined,
        base_url: form.value.base_url || undefined,
        model_name: form.value.model_name,
        default_params: { temperature: form.value.temperature, max_tokens: form.value.max_tokens },
      })
      ElMessage.success('更新成功')
    } else {
      await createModel({
        workspace_id: workspaceStore.currentWorkspace.id,
        name: form.value.name,
        provider: form.value.provider,
        api_key: form.value.api_key || undefined,
        base_url: form.value.base_url || undefined,
        model_name: form.value.model_name,
        default_params: { temperature: form.value.temperature, max_tokens: form.value.max_tokens },
      })
      ElMessage.success('创建成功')
    }
    showCreate.value = false
    editingModel.value = null
    resetForm()
    await fetchModels()
  } catch {
    // handled by interceptor
  }
}

function resetForm() {
  form.value = { name: '', provider: 'deepseek', api_key: '', base_url: 'https://api.deepseek.com', model_name: 'deepseek-chat', temperature: 0.7, max_tokens: 2000 }
}

function openEdit(model: any) {
  editingModel.value = model
  form.value = {
    name: model.name,
    provider: model.provider,
    api_key: '',
    base_url: model.base_url || '',
    model_name: model.model_name,
    temperature: model.default_params?.temperature || 0.7,
    max_tokens: model.default_params?.max_tokens || 2000,
  }
  showCreate.value = true
}

async function handleToggle(model: any) {
  await toggleModel(model.id)
  await fetchModels()
}

async function handleDelete(id: string) {
  await ElMessageBox.confirm('确定删除此模型配置？', '提示', { type: 'warning' })
  await deleteModel(id)
  ElMessage.success('已删除')
  await fetchModels()
}
</script>

<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
      <h3>AI 模型配置</h3>
      <el-button v-if="canEdit()" type="primary" @click="resetForm(); editingModel = null; showCreate = true">添加模型</el-button>
    </div>

    <el-table :data="models" v-loading="loading" style="width: 100%">
      <el-table-column prop="name" label="模型名称" />
      <el-table-column prop="provider" label="提供商" width="120" />
      <el-table-column prop="model_name" label="模型标识" width="180" />
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-switch :model-value="row.is_active" @change="handleToggle(row)" />
        </template>
      </el-table-column>
      <el-table-column label="默认参数" width="200">
        <template #default="{ row }">
          <span v-if="row.default_params">
            T={{ row.default_params.temperature }}, Tokens={{ row.default_params.max_tokens }}
          </span>
        </template>
      </el-table-column>
      <el-table-column label="操作" width="160">
        <template #default="{ row }">
          <el-button v-if="canEdit()" size="small" @click="openEdit(row)">编辑</el-button>
          <el-button v-if="canEdit()" size="small" type="danger" @click="handleDelete(row.id)">删除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showCreate" :title="editingModel ? '编辑模型' : '添加模型'" width="500px">
      <el-form label-width="100px">
        <el-form-item label="模型名称">
          <el-input v-model="form.name" placeholder="如：GPT-4o" />
        </el-form-item>
        <el-form-item label="提供商">
          <el-select v-model="form.provider">
            <el-option v-for="p in providers" :key="p.value" :label="p.label" :value="p.value" />
          </el-select>
        </el-form-item>
        <el-form-item label="模型标识">
          <el-input v-model="form.model_name" placeholder="如：gpt-4o" />
        </el-form-item>
        <el-form-item label="API Key">
          <el-input v-model="form.api_key" type="password" placeholder="留空则使用环境变量中的全局 Key" show-password />
        </el-form-item>
        <el-form-item label="Base URL">
          <el-input v-model="form.base_url" placeholder="可选，自定义 API 地址" />
        </el-form-item>
        <el-form-item label="Temperature">
          <el-input-number v-model="form.temperature" :min="0" :max="2" :step="0.1" />
        </el-form-item>
        <el-form-item label="Max Tokens">
          <el-input-number v-model="form.max_tokens" :min="100" :max="8000" :step="100" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" @click="handleSubmit">{{ editingModel ? '保存' : '创建' }}</el-button>
      </template>
    </el-dialog>
  </div>
</template>
