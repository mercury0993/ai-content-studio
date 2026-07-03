<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkspaceStore } from '@/stores/workspace'
import { createWorkspace, deleteWorkspace } from '@/api/workspaces'
import { canEdit } from '@/utils/permission'
import SkeletonTable from '@/components/SkeletonTable.vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const workspaceStore = useWorkspaceStore()
const router = useRouter()
const showCreate = ref(false)
const form = ref({ name: '', description: '' })
const loading = ref(false)
const firstLoad = ref(true)

onMounted(async () => {
  await workspaceStore.fetchWorkspaces()
  firstLoad.value = false
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
    <div class="page-header">
      <h3 class="page-heading">工作空间</h3>
      <el-button v-if="canEdit()" type="primary" @click="showCreate = true">新建空间</el-button>
    </div>

    <SkeletonTable v-if="firstLoad" />

    <template v-else-if="workspaceStore.workspaces.length === 0">
      <el-empty description="暂无工作空间" />
    </template>

    <template v-else>
      <el-row :gutter="16">
        <el-col :span="8" v-for="ws in workspaceStore.workspaces" :key="ws.id">
          <el-card class="ws-card" @click="goDetail(ws.id)">
            <template #header>
              <div class="ws-header">
                <span class="ws-name">{{ ws.name }}</span>
                <el-button v-if="canEdit()" size="small" type="danger" @click.stop="handleDelete(ws.id, ws.name)">删除</el-button>
              </div>
            </template>
            <p>{{ ws.description || '暂无描述' }}</p>
            <p class="ws-date">创建于 {{ new Date(ws.created_at).toLocaleDateString() }}</p>
          </el-card>
        </el-col>
      </el-row>
    </template>

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

<style scoped>
.page-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.page-heading {
  margin-bottom: 0;
}
.ws-card {
  margin-bottom: 16px;
  cursor: pointer;
}
.ws-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
}
.ws-name {
  font-weight: bold;
}
.ws-date {
  color: #999;
  font-size: 12px;
}
</style>
