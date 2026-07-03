<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkspaceStore } from '@/stores/workspace'
import { listContents, deleteContent } from '@/api/contents'
import { submitForReview } from '@/api/reviews'
import { exportZip } from '@/api/export'
import { canEdit } from '@/utils/permission'
import { statusMap, truncate, formatDate } from '@/utils/common'
import { useDebouncedWatch } from '@/composables/useDebouncedWatch'
import SkeletonTable from '@/components/SkeletonTable.vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const workspaceStore = useWorkspaceStore()
const router = useRouter()
const contents = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const status = ref('')
const loading = ref(false)
const firstLoad = ref(true)
const selectedIds = ref<string[]>([])

async function fetchContents() {
  if (!workspaceStore.currentWorkspace) return
  loading.value = true
  try {
    const data: any = await listContents({
      workspace_id: workspaceStore.currentWorkspace.id,
      status: status.value || undefined,
      page: page.value,
    })
    contents.value = data.data.items
    total.value = data.data.total
    firstLoad.value = false
  } finally {
    loading.value = false
  }
}

onMounted(fetchContents)
useDebouncedWatch([page, status], fetchContents, 300)

async function handleDelete(id: string) {
  await ElMessageBox.confirm('确定删除？', '提示', { type: 'warning' })
  await deleteContent(id)
  ElMessage.success('已删除')
  await fetchContents()
}

async function handleSubmitReview(id: string) {
  try {
    await submitForReview(id)
    ElMessage.success('已提交审核')
    await fetchContents()
  } catch {
    // handled by interceptor
  }
}

function handleSelectionChange(selection: any[]) {
  selectedIds.value = selection.map((item: any) => item.id)
}

function handleBatchExport() {
  if (selectedIds.value.length === 0) {
    ElMessage.warning('请先选择要导出的内容')
    return
  }
  exportZip(selectedIds.value)
}
</script>

<template>
  <div>
    <div class="page-header">
      <h3 class="page-heading">内容管理</h3>
      <div class="header-actions">
        <el-button v-if="canEdit()" @click="handleBatchExport" :disabled="selectedIds.length === 0">
          批量导出 ZIP ({{ selectedIds.length }})
        </el-button>
        <el-button v-if="canEdit()" type="primary" @click="router.push('/contents/create')">生成内容</el-button>
      </div>
    </div>

    <div class="filter-bar">
      <el-select v-model="status" placeholder="状态筛选" clearable>
        <el-option label="草稿" value="draft" />
        <el-option label="待审核" value="pending_review" />
        <el-option label="已通过" value="approved" />
        <el-option label="已驳回" value="rejected" />
      </el-select>
    </div>

    <SkeletonTable v-if="firstLoad && loading" />

    <template v-else-if="contents.length === 0">
      <el-empty description="暂无内容" />
    </template>

    <template v-else>
      <el-table :data="contents" v-loading="loading" @selection-change="handleSelectionChange">
        <el-table-column type="selection" width="50" />
        <el-table-column label="内容预览" min-width="300">
          <template #default="{ row }">
            <span>{{ truncate(row.edited_text || row.generated_text, 80) }}</span>
          </template>
        </el-table-column>
        <el-table-column label="状态" width="100">
          <template #default="{ row }">
            <el-tag :type="statusMap[row.status]?.type as any">{{ statusMap[row.status]?.label }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="Token" width="100">
          <template #default="{ row }">
            {{ row.token_usage || '暂不支持' }}
          </template>
        </el-table-column>
        <el-table-column label="生成时间" width="120">
          <template #default="{ row }">
            {{ row.generation_time_ms }}ms
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240">
          <template #default="{ row }">
            <el-button size="small" @click="router.push(`/contents/${row.id}`)">查看</el-button>
            <el-button v-if="canEdit() && row.status === 'draft'" size="small" type="success" @click="handleSubmitReview(row.id)">提交审核</el-button>
            <el-button v-if="canEdit()" size="small" type="danger" @click="handleDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </template>

    <div class="pagination-wrap" v-if="total > 0">
      <el-pagination v-model:current-page="page" :page-size="20" :total="total" layout="prev, pager, next" />
    </div>
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
.header-actions {
  display: flex;
  gap: 8px;
}
.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}
.pagination-wrap {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
