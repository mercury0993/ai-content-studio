<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
import { useWorkspaceStore } from '@/stores/workspace'
import { listReviews, approveContent, rejectContent, batchReview, submitForReview } from '@/api/reviews'
import { listMembers } from '@/api/workspaces'
import { ElMessage, ElMessageBox } from 'element-plus'

const workspaceStore = useWorkspaceStore()
const reviews = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const statusFilter = ref('')
const loading = ref(false)
const selectedIds = ref<string[]>([])
const showSubmitDialog = ref(false)
const showRejectDialog = ref(false)
const members = ref<any[]>([])
const submitForm = ref({ content_id: '', reviewer_id: '' })
const rejectForm = ref({ content_id: '', comment: '' })

const statusMap: Record<string, { label: string; type: string }> = {
  draft: { label: '草稿', type: 'info' },
  pending_review: { label: '待审核', type: 'warning' },
  approved: { label: '已通过', type: 'success' },
  rejected: { label: '已驳回', type: 'danger' },
}

async function fetchReviews() {
  if (!workspaceStore.currentWorkspace) return
  loading.value = true
  try {
    const data: any = await listReviews({
      workspace_id: workspaceStore.currentWorkspace.id,
      status: statusFilter.value || undefined,
      page: page.value,
    })
    reviews.value = data.data.items
    total.value = data.data.total
  } finally {
    loading.value = false
  }
}

async function fetchMembers() {
  if (!workspaceStore.currentWorkspace) return
  members.value = await listMembers(workspaceStore.currentWorkspace.id) as any
}

onMounted(() => {
  fetchReviews()
  fetchMembers()
})
watch([page, statusFilter], fetchReviews)

async function handleApprove(id: string) {
  await approveContent(id)
  ElMessage.success('已通过')
  await fetchReviews()
}

function openReject(id: string) {
  rejectForm.value = { content_id: id, comment: '' }
  showRejectDialog.value = true
}

async function handleReject() {
  if (!rejectForm.value.comment) {
    ElMessage.warning('请填写驳回理由')
    return
  }
  await rejectContent(rejectForm.value.content_id, rejectForm.value.comment)
  ElMessage.success('已驳回')
  showRejectDialog.value = false
  await fetchReviews()
}

function openSubmit(id: string) {
  submitForm.value = { content_id: id, reviewer_id: '' }
  showSubmitDialog.value = true
}

async function handleSubmitForReview() {
  if (!submitForm.value.reviewer_id) {
    ElMessage.warning('请选择审核人')
    return
  }
  await submitForReview(submitForm.value.content_id, submitForm.value.reviewer_id)
  ElMessage.success('已提交审核')
  showSubmitDialog.value = false
  await fetchReviews()
}

async function handleBatch(action: string) {
  if (selectedIds.value.length === 0) {
    ElMessage.warning('请选择要审核的内容')
    return
  }
  if (action === 'reject') {
    const { value } = await ElMessageBox.prompt('请输入驳回理由', '批量驳回', { inputType: 'textarea' })
    await batchReview(selectedIds.value, 'reject', value)
  } else {
    await batchReview(selectedIds.value, 'approve')
  }
  ElMessage.success('批量操作成功')
  selectedIds.value = []
  await fetchReviews()
}

function handleSelectionChange(rows: any[]) {
  selectedIds.value = rows.map((r: any) => r.id)
}

function truncate(text: string, len: number) {
  return text?.length > len ? text.slice(0, len) + '...' : text
}
</script>

<template>
  <div>
    <div style="display: flex; justify-content: space-between; align-items: center; margin-bottom: 16px;">
      <h3>审核中心</h3>
      <div>
        <el-button @click="handleBatch('approve')" :disabled="selectedIds.length === 0">批量通过</el-button>
        <el-button type="danger" @click="handleBatch('reject')" :disabled="selectedIds.length === 0">批量驳回</el-button>
      </div>
    </div>

    <el-select v-model="statusFilter" placeholder="状态筛选" clearable style="margin-bottom: 16px;">
      <el-option label="待审核" value="pending_review" />
      <el-option label="已通过" value="approved" />
      <el-option label="已驳回" value="rejected" />
      <el-option label="草稿" value="draft" />
    </el-select>

    <el-table :data="reviews" v-loading="loading" @selection-change="handleSelectionChange" style="width: 100%">
      <el-table-column type="selection" width="55" />
      <el-table-column label="内容预览" min-width="250">
        <template #default="{ row }">
          <span>{{ truncate(row.edited_text || row.generated_text, 60) }}</span>
        </template>
      </el-table-column>
      <el-table-column label="状态" width="100">
        <template #default="{ row }">
          <el-tag :type="statusMap[row.status]?.type as any">{{ statusMap[row.status]?.label }}</el-tag>
        </template>
      </el-table-column>
      <el-table-column label="审核意见" width="200">
        <template #default="{ row }">
          <span v-if="row.review_comment">{{ row.review_comment }}</span>
          <span v-else style="color: #999;">—</span>
        </template>
      </el-table-column>
      <el-table-column label="创建时间" width="180">
        <template #default="{ row }">
          {{ new Date(row.created_at).toLocaleString() }}
        </template>
      </el-table-column>
      <el-table-column label="操作" width="240">
        <template #default="{ row }">
          <template v-if="row.status === 'draft'">
            <el-button size="small" type="primary" @click="openSubmit(row.id)">提交审核</el-button>
          </template>
          <template v-if="row.status === 'pending_review'">
            <el-button size="small" type="success" @click="handleApprove(row.id)">通过</el-button>
            <el-button size="small" type="danger" @click="openReject(row.id)">驳回</el-button>
          </template>
        </template>
      </el-table-column>
    </el-table>

    <div style="margin-top: 16px; display: flex; justify-content: flex-end;">
      <el-pagination v-model:current-page="page" :page-size="20" :total="total" layout="prev, pager, next" />
    </div>

    <el-dialog v-model="showSubmitDialog" title="提交审核">
      <el-form>
        <el-form-item label="选择审核人">
          <el-select v-model="submitForm.reviewer_id" placeholder="选择审核人" style="width: 100%;">
            <el-option v-for="m in members" :key="m.user_id" :label="`${m.username} (${m.email})`" :value="m.user_id" />
          </el-select>
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showSubmitDialog = false">取消</el-button>
        <el-button type="primary" @click="handleSubmitForReview">提交</el-button>
      </template>
    </el-dialog>

    <el-dialog v-model="showRejectDialog" title="驳回">
      <el-form>
        <el-form-item label="驳回理由">
          <el-input v-model="rejectForm.comment" type="textarea" :rows="3" placeholder="请输入驳回理由" />
        </el-form-item>
      </el-form>
      <template #footer>
        <el-button @click="showRejectDialog = false">取消</el-button>
        <el-button type="danger" @click="handleReject">驳回</el-button>
      </template>
    </el-dialog>
  </div>
</template>
