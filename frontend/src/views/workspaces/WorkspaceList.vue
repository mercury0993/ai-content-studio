<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkspaceStore } from '@/stores/workspace'
import { createWorkspace, deleteWorkspace } from '@/api/workspaces'
import { ElMessage, ElMessageBox } from 'element-plus'

const workspaceStore = useWorkspaceStore()
const router = useRouter()
const showCreate = ref(false)
const form = ref({ name: '', description: '' })
const loading = ref(false)

onMounted(() => {
  workspaceStore.fetchWorkspaces()
})

async function handleCreate() {
  if (!form.value.name) {
    ElMessage.warning('请输入空间名称')
    return
  }
  loading.value = true
  try {
    await createWorkspace(form.value)
    ElMessage.success('创建成功')
    showCreate.value = false
    form.value = { name: '', description: '' }
    await workspaceStore.fetchWorkspaces()
  } finally {
    loading.value = false
  }
}

async function handleDelete(id: string, name: string) {
  await ElMessageBox.confirm(`确定删除空间「${name}」？`, '提示', { type: 'warning' })
  await deleteWorkspace(id)
  ElMessage.success('已删除')
  await workspaceStore.fetchWorkspaces()
}

function goDetail(id: string) {
  router.push(`/workspaces/${id}`)
}
</script>

<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
      <h3>工作空间</h3>
      <el-button type="primary" @click="showCreate = true">新建空间</el-button>
    </div>

    <el-row :gutter="16">
      <el-col :span="8" v-for="ws in workspaceStore.workspaces" :key="ws.id">
        <el-card style="margin-bottom: 16px; cursor: pointer;" @click="goDetail(ws.id)">
          <template #header>
            <div style="display: flex; justify-content: space-between; align-items: center;">
              <span style="font-weight: bold;">{{ ws.name }}</span>
              <el-button size="small" type="danger" @click.stop="handleDelete(ws.id, ws.name)">删除</el-button>
            </div>
          </template>
          <p>{{ ws.description || '暂无描述' }}</p>
          <p style="color: #999; font-size: 12px;">创建于 {{ new Date(ws.created_at).toLocaleDateString() }}</p>
        </el-card>
      </el-col>
    </el-row>

    <el-dialog v-model="showCreate" title="新建工作空间">
      <el-form>
        <el-form-item label="名称">
          <el-input v-model="form.name" placeholder="空间名称" />
        </el-form-item>
        <el-form-item label="描述">
          <el-input v-model="form.description" type="textarea" placeholder="空间描述（可选）" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showCreate = false">取消</el-button>
        <el-button type="primary" :loading="loading" @click="handleCreate">创建</el-button>
      </template>
    </el-dialog>
  </div>
</template>
