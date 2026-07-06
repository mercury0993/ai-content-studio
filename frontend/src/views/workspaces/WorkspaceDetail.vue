<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute } from 'vue-router'
import { getWorkspace, listMembers, addMember, removeMember } from '@/api/workspaces'
import { ElMessage, ElMessageBox } from 'element-plus'
import type { WorkspaceItem, MemberItem } from '@/api/types'

const route = useRoute()
const workspace = ref<WorkspaceItem | null>(null)
const members = ref<MemberItem[]>([])
const showAddMember = ref(false)
const newMember = ref({ user_id: '', role: 'viewer' })

onMounted(async () => {
  const id = route.params.id as string
  workspace.value = (await getWorkspace(id))
  members.value = (await listMembers(id))
})

async function handleAddMember() {
  if (!newMember.value.user_id) {
    ElMessage.warning('请输入用户 ID')
    return
  }
  try {
    await addMember(route.params.id as string, newMember.value)
    ElMessage.success('添加成功')
    showAddMember.value = false
    members.value = (await listMembers(route.params.id as string))
  } catch {
    ElMessage.error('操作失败，请重试')
  }
}

async function handleRemoveMember(userId: string) {
  await ElMessageBox.confirm('确定移除该成员？', '提示', { type: 'warning' })
  await removeMember(route.params.id as string, userId)
  ElMessage.success('已移除')
  members.value = (await listMembers(route.params.id as string))
}
</script>

<template>
  <div v-if="workspace">
    <h3>{{ workspace.name }}</h3>
    <p>{{ workspace.description || '暂无描述' }}</p>

    <div style="display: flex; justify-content: space-between; align-items: center; margin: 24px 0 16px;">
      <h4>成员管理</h4>
      <el-button type="primary" size="small" @click="showAddMember = true">添加成员</el-button>
    </div>

    <el-table :data="members" style="width: 100%">
      <el-table-column prop="username" label="用户名" />
      <el-table-column prop="email" label="邮箱" />
      <el-table-column prop="role" label="角色" />
      <el-table-column label="操作" width="100">
        <template #default="{ row }">
          <el-button size="small" type="danger" @click="handleRemoveMember(row.user_id)">移除</el-button>
        </template>
      </el-table-column>
    </el-table>

    <el-dialog v-model="showAddMember" title="添加成员">
      <el-form>
        <el-form-item label="用户 ID">
          <el-input v-model="newMember.user_id" placeholder="输入用户 UUID" />
        </el-form-item>
        <el-form-item label="角色">
          <el-select v-model="newMember.role">
            <el-option label="管理员" value="admin" />
            <el-option label="编辑" value="editor" />
            <el-option label="只读" value="viewer" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showAddMember = false">取消</el-button>
        <el-button type="primary" @click="handleAddMember">添加</el-button>
      </template>
    </el-dialog>
  </div>
</template>
