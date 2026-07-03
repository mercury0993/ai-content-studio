<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkspaceStore } from '@/stores/workspace'
import { listPrompts, deletePrompt, updatePrompt } from '@/api/prompts'
import { canEdit } from '@/utils/permission'
import { useDebouncedWatch } from '@/composables/useDebouncedWatch'
import SkeletonTable from '@/components/SkeletonTable.vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const workspaceStore = useWorkspaceStore()
const router = useRouter()
const prompts = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const pageSize = ref(20)
const search = ref('')
const category = ref('')
const loading = ref(false)
const firstLoad = ref(true)

const categories = [
  { label: '全部', value: '' },
  { label: '营销文案', value: 'marketing' },
  { label: '技术文档', value: 'tech_doc' },
  { label: '社交媒体', value: 'social_media' },
]

async function fetchPrompts() {
  if (!workspaceStore.currentWorkspace) return
  loading.value = true
  try {
    const data: any = await listPrompts({
      workspace_id: workspaceStore.currentWorkspace.id,
      category: category.value || undefined,
      search: search.value || undefined,
      page: page.value,
      page_size: pageSize.value,
    })
    prompts.value = data.data.items
    total.value = data.data.total
    firstLoad.value = false
  } finally {
    loading.value = false
  }
}

onMounted(fetchPrompts)
useDebouncedWatch([page, category], fetchPrompts, 300)

async function handleSearch() {
  page.value = 1
  await fetchPrompts()
}

async function handleDelete(id: string) {
  await ElMessageBox.confirm('确定删除此 Prompt？', '提示', { type: 'warning' })
  await deletePrompt(id)
  ElMessage.success('已删除')
  await fetchPrompts()
}

async function handleToggleFavorite(prompt: any) {
  await updatePrompt(prompt.id, { is_favorite: !prompt.is_favorite })
  await fetchPrompts()
}

function goEdit(id: string) {
  router.push(`/prompts/${id}/edit`)
}

function goVersions(id: string) {
  router.push(`/prompts/${id}/versions`)
}
</script>

<template>
  <div>
    <div class="page-header">
      <h3 class="page-heading">Prompt 模板</h3>
      <el-button v-if="canEdit()" type="primary" @click="router.push('/prompts/create')">新建 Prompt</el-button>
    </div>

    <div class="filter-bar">
      <el-input v-model="search" placeholder="搜索 Prompt..." style="width: 300px;" @keyup.enter="handleSearch" clearable />
      <el-select v-model="category" placeholder="分类" clearable>
        <el-option v-for="c in categories" :key="c.value" :label="c.label" :value="c.value" />
      </el-select>
    </div>

    <SkeletonTable v-if="firstLoad && loading" />

    <template v-else-if="prompts.length === 0">
      <el-empty description="暂无 Prompt 模板" />
    </template>

    <template v-else>
      <el-table :data="prompts" v-loading="loading">
        <el-table-column width="40">
          <template #default="{ row }">
            <el-icon class="favorite-icon" @click="handleToggleFavorite(row)">
              <StarFilled v-if="row.is_favorite" style="color: #f7ba2a;" />
              <Star v-else />
            </el-icon>
          </template>
        </el-table-column>
        <el-table-column prop="title" label="标题" />
        <el-table-column prop="category" label="分类" width="120" />
        <el-table-column prop="version" label="版本" width="80" />
        <el-table-column label="标签" width="200">
          <template #default="{ row }">
            <el-tag v-for="tag in (row.tags || [])" :key="tag" size="small" class="tag-item">{{ tag }}</el-tag>
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240">
          <template #default="{ row }">
            <el-button v-if="canEdit()" size="small" @click="goEdit(row.id)">编辑</el-button>
            <el-button size="small" @click="goVersions(row.id)">历史</el-button>
            <el-button v-if="canEdit()" size="small" type="danger" @click="handleDelete(row.id)">删除</el-button>
          </template>
        </el-table-column>
      </el-table>
    </template>

    <div class="pagination-wrap" v-if="total > 0">
      <el-pagination v-model:current-page="page" :page-size="pageSize" :total="total" layout="prev, pager, next" />
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
.filter-bar {
  display: flex;
  gap: 12px;
  margin-bottom: 16px;
}
.favorite-icon {
  cursor: pointer;
}
.tag-item {
  margin-right: 4px;
}
.pagination-wrap {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
