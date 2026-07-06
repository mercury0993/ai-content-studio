# Frontend Optimization Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Optimize frontend performance (memory leaks, debounce), code quality (DRY utilities, inline styles), UX (empty states, skeleton screens, workspace switcher), and responsive layout.

**Architecture:** Extract shared utilities and composables, add 3 reusable skeleton components, fix ECharts lifecycle in Dashboard, add workspace switcher to MainLayout header, and make Dashboard responsive. All changes follow existing Vue 3 + Element Plus patterns with scoped styles.

**Tech Stack:** Vue 3 + TypeScript + Element Plus + ECharts + Pinia + Vue Router

---

### Task 1: Create common utilities

**Files:**
- Create: `frontend/src/utils/common.ts`

- [ ] **Step 1: Write `common.ts` with shared constants and helpers**

```typescript
export const statusMap: Record<string, { label: string; type: string }> = {
  draft: { label: '草稿', type: 'info' },
  pending_review: { label: '待审核', type: 'warning' },
  approved: { label: '已通过', type: 'success' },
  rejected: { label: '已驳回', type: 'danger' },
}

export function truncate(text: string, len: number): string {
  if (!text) return ''
  return text.length > len ? text.slice(0, len) + '...' : text
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleString()
}
```

- [ ] **Step 2: Verify file exists**

Run: `ls -la frontend/src/utils/common.ts`

---

### Task 2: Create debounced watch composable

**Files:**
- Create: `frontend/src/composables/useDebouncedWatch.ts`

- [ ] **Step 1: Write `useDebouncedWatch.ts`**

```typescript
import { watch, onUnmounted, type WatchSource, type WatchCallback, type WatchOptions } from 'vue'

export function useDebouncedWatch<T>(
  sources: WatchSource<T> | WatchSource<T>[],
  callback: WatchCallback<T>,
  delay = 300,
  options?: WatchOptions,
) {
  let timer: ReturnType<typeof setTimeout> | null = null

  const unwatch = watch(
    sources,
    (...args: Parameters<WatchCallback<T>>) => {
      if (timer) clearTimeout(timer)
      timer = setTimeout(() => {
        timer = null
        ;(callback as any)(...args)
      }, delay)
    },
    options,
  )

  onUnmounted(() => {
    if (timer) clearTimeout(timer)
    unwatch()
  })

  return unwatch
}
```

- [ ] **Step 2: Verify file exists**

Run: `ls -la frontend/src/composables/useDebouncedWatch.ts`

---

### Task 3: Create skeleton components

**Files:**
- Create: `frontend/src/components/SkeletonCard.vue`
- Create: `frontend/src/components/SkeletonChart.vue`
- Create: `frontend/src/components/SkeletonTable.vue`

- [ ] **Step 1: Write `SkeletonCard.vue`**

```vue
<template>
  <div class="skeleton-card">
    <div class="skeleton-block skeleton-value"></div>
    <div class="skeleton-block skeleton-label"></div>
  </div>
</template>

<style scoped>
.skeleton-card {
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  border: 1px solid var(--el-border-color);
  text-align: center;
}
.skeleton-block {
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
  margin: 0 auto;
}
.skeleton-value {
  height: 36px;
  width: 60%;
  margin-bottom: 12px;
}
.skeleton-label {
  height: 14px;
  width: 40%;
}
@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>
```

- [ ] **Step 2: Write `SkeletonChart.vue`**

```vue
<template>
  <div class="skeleton-chart">
    <div class="skeleton-block skeleton-title"></div>
    <div class="skeleton-block skeleton-body"></div>
  </div>
</template>

<style scoped>
.skeleton-chart {
  background: #fff;
  border-radius: 8px;
  border: 1px solid var(--el-border-color);
  padding: 20px;
}
.skeleton-block {
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
}
.skeleton-title {
  height: 16px;
  width: 30%;
  margin-bottom: 16px;
}
.skeleton-body {
  height: 280px;
  width: 100%;
}
@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>
```

- [ ] **Step 3: Write `SkeletonTable.vue`**

```vue
<template>
  <div class="skeleton-table">
    <div class="skeleton-row" v-for="i in 5" :key="i">
      <div class="skeleton-block" :style="{ width: widths[i % widths.length] }"></div>
    </div>
  </div>
</template>

<script setup lang="ts">
const widths = ['60%', '40%', '50%', '35%', '55%']
</script>

<style scoped>
.skeleton-table {
  background: #fff;
  border-radius: 8px;
  border: 1px solid var(--el-border-color);
  padding: 16px;
}
.skeleton-row {
  padding: 12px 0;
  border-bottom: 1px solid var(--el-border-color-light);
}
.skeleton-row:last-child {
  border-bottom: none;
}
.skeleton-block {
  height: 16px;
  background: linear-gradient(90deg, #f0f0f0 25%, #e0e0e0 50%, #f0f0f0 75%);
  background-size: 200% 100%;
  animation: shimmer 1.5s infinite;
  border-radius: 4px;
}
@keyframes shimmer {
  0% { background-position: 200% 0; }
  100% { background-position: -200% 0; }
}
</style>
```

- [ ] **Step 4: Verify all 3 files exist**

Run: `ls -la frontend/src/components/Skeleton*.vue`

---

### Task 4: Fix Dashboard.vue — ECharts lifecycle, responsive, skeleton, common utils, inline styles

**Files:**
- Modify: `frontend/src/views/Dashboard.vue`

- [ ] **Step 1: Rewrite Dashboard.vue fully**

```vue
<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useWorkspaceStore } from '@/stores/workspace'
import { getStats, getTrend, getModelUsage, getUserRanking, getRecent } from '@/api/dashboard'
import { statusMap } from '@/utils/common'
import SkeletonCard from '@/components/SkeletonCard.vue'
import SkeletonChart from '@/components/SkeletonChart.vue'
import SkeletonTable from '@/components/SkeletonTable.vue'
import * as echarts from 'echarts'

const workspaceStore = useWorkspaceStore()

const stats = ref({ prompt_count: 0, content_count: 0, monthly_generated: 0, pending_review: 0 })
const recentItems = ref<any[]>([])
const firstLoad = ref(true)

let trendChart: echarts.ECharts | null = null
let modelChart: echarts.ECharts | null = null
let rankingChart: echarts.ECharts | null = null

async function fetchDashboard() {
  if (!workspaceStore.currentWorkspace) return
  const wsId = workspaceStore.currentWorkspace.id

  const [statsData, trendData, modelData, rankingData, recentData]: any[] = await Promise.all([
    getStats(wsId),
    getTrend(wsId),
    getModelUsage(wsId),
    getUserRanking(wsId),
    getRecent(wsId),
  ])

  stats.value = statsData.data
  recentItems.value = recentData.data
  firstLoad.value = false

  await nextTick()
  renderTrendChart(trendData.data)
  renderModelChart(modelData.data)
  renderRankingChart(rankingData.data)
}

const chartColors = {
  primary: '#4f5dd5',
  success: '#16a34a',
  warning: '#d97706',
  danger: '#dc2626',
}

function baseChartOptions(): any {
  return {
    textStyle: { fontFamily: 'inherit' },
    grid: { left: '3%', right: '4%', top: '40px', bottom: '3%', containLabel: true },
  }
}

function renderTrendChart(data: { date: string; count: number }[]) {
  const el = document.getElementById('trend-chart')
  if (!el) return
  if (trendChart) {
    trendChart.dispose()
  }
  trendChart = echarts.init(el)
  trendChart.setOption({
    ...baseChartOptions(),
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: data.map((d) => d.date.slice(5)), axisLine: { lineStyle: { color: '#e5e7eb' } } },
    yAxis: { type: 'value', minInterval: 1, splitLine: { lineStyle: { color: '#f3f4f6' } } },
    series: [{
      data: data.map((d) => d.count),
      type: 'line',
      smooth: true,
      lineStyle: { color: chartColors.primary, width: 2 },
      itemStyle: { color: chartColors.primary },
      areaStyle: { color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
        { offset: 0, color: 'rgba(79, 93, 213, 0.12)' },
        { offset: 1, color: 'rgba(79, 93, 213, 0)' },
      ]) },
      symbol: 'none',
    }],
  })
}

function renderModelChart(data: { name: string; count: number }[]) {
  const el = document.getElementById('model-chart')
  if (!el) return
  if (modelChart) {
    modelChart.dispose()
  }
  modelChart = echarts.init(el)
  modelChart.setOption({
    ...baseChartOptions(),
    tooltip: { trigger: 'item' },
    color: ['#4f5dd5', '#16a34a', '#d97706', '#dc2626', '#6b7280', '#8b5cf6'],
    series: [{
      type: 'pie',
      radius: ['50%', '75%'],
      center: ['50%', '50%'],
      data: data.map((d) => ({ name: d.name, value: d.count })),
      label: { show: false },
      emphasis: { label: { show: true, fontWeight: 600 } },
    }],
  })
}

function renderRankingChart(data: { username: string; count: number }[]) {
  const el = document.getElementById('ranking-chart')
  if (!el) return
  if (rankingChart) {
    rankingChart.dispose()
  }
  rankingChart = echarts.init(el)
  rankingChart.setOption({
    ...baseChartOptions(),
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: data.map((d) => d.username), axisLine: { lineStyle: { color: '#e5e7eb' } } },
    yAxis: { type: 'value', minInterval: 1, splitLine: { lineStyle: { color: '#f3f4f6' } } },
    series: [{
      data: data.map((d) => d.count),
      type: 'bar',
      barWidth: '50%',
      itemStyle: {
        color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
          { offset: 0, color: '#4f5dd5' },
          { offset: 1, color: '#919ae7' },
        ]),
        borderRadius: [4, 4, 0, 0],
      },
    }],
  })
}

function handleResize() {
  trendChart?.resize()
  modelChart?.resize()
  rankingChart?.resize()
}

onMounted(() => {
  fetchDashboard()
  window.addEventListener('resize', handleResize)
})

onUnmounted(() => {
  window.removeEventListener('resize', handleResize)
  trendChart?.dispose()
  modelChart?.dispose()
  rankingChart?.dispose()
})

watch(() => workspaceStore.currentWorkspace, fetchDashboard)

const statCards = [
  { key: 'prompt_count', label: 'Prompt 总数', color: 'var(--el-color-primary)' },
  { key: 'content_count', label: '内容总数', color: 'var(--el-color-success)' },
  { key: 'monthly_generated', label: '本月生成', color: 'var(--el-color-warning)' },
  { key: 'pending_review', label: '待审核', color: 'var(--el-color-danger)' },
]
</script>

<template>
  <div>
    <h3 class="page-heading">数据看板</h3>

    <el-row v-if="firstLoad" :gutter="20" class="stat-row">
      <el-col v-for="i in 4" :key="i" :xs="12" :sm="12" :md="6" :lg="6">
        <SkeletonCard />
      </el-col>
    </el-row>
    <el-row v-else :gutter="20" class="stat-row">
      <el-col v-for="card in statCards" :key="card.key" :xs="12" :sm="12" :md="6" :lg="6">
        <div class="stat-card">
          <div class="stat-value" :style="{ color: card.color }">
            {{ (stats as any)[card.key] }}
          </div>
          <div class="stat-label">{{ card.label }}</div>
        </div>
      </el-col>
    </el-row>

    <el-row v-if="firstLoad" :gutter="20" class="chart-row">
      <el-col :xs="24" :sm="24" :md="16">
        <SkeletonChart />
      </el-col>
      <el-col :xs="24" :sm="24" :md="8">
        <SkeletonChart />
      </el-col>
    </el-row>
    <el-row v-else :gutter="20" class="chart-row">
      <el-col :xs="24" :sm="24" :md="16">
        <div class="chart-card">
          <div class="chart-title">生成趋势</div>
          <div id="trend-chart" class="chart-body"></div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="24" :md="8">
        <div class="chart-card">
          <div class="chart-title">模型占比</div>
          <div id="model-chart" class="chart-body"></div>
        </div>
      </el-col>
    </el-row>

    <el-row :gutter="20">
      <el-col v-if="firstLoad" :xs="24" :md="12">
        <SkeletonChart />
      </el-col>
      <el-col v-else :xs="24" :md="12">
        <div class="chart-card">
          <div class="chart-title">用户排名</div>
          <div id="ranking-chart" class="chart-body"></div>
        </div>
      </el-col>
      <el-col v-if="firstLoad" :xs="24" :md="12">
        <SkeletonTable />
      </el-col>
      <el-col v-else :xs="24" :md="12">
        <div class="chart-card">
          <div class="chart-title">最近记录</div>
          <div class="chart-body" style="padding: 0;">
            <el-table :data="recentItems" max-height="270" stripe>
              <el-table-column label="内容" min-width="200">
                <template #default="{ row }">
                  <span class="recent-text">{{ (row.edited_text || row.generated_text || '').slice(0, 45) }}...</span>
                </template>
              </el-table-column>
              <el-table-column label="状态" width="90">
                <template #default="{ row }">
                  <el-tag :type="statusMap[row.status]?.type as any" size="small">{{ statusMap[row.status]?.label }}</el-tag>
                </template>
              </el-table-column>
              <el-table-column label="时间" width="150">
                <template #default="{ row }">
                  <span class="recent-time">{{ new Date(row.created_at).toLocaleString() }}</span>
                </template>
              </el-table-column>
            </el-table>
          </div>
        </div>
      </el-col>
    </el-row>
  </div>
</template>

<style scoped>
.stat-row {
  margin-bottom: 20px;
}

.stat-card {
  background: #fff;
  border-radius: 8px;
  padding: 24px;
  border: 1px solid var(--el-border-color);
  text-align: center;
  transition: box-shadow 0.2s ease;
}

.stat-card:hover {
  box-shadow: var(--el-box-shadow-light);
}

.stat-value {
  font-size: 36px;
  font-weight: 700;
  line-height: 1.2;
  letter-spacing: -0.02em;
}

.stat-label {
  font-size: 13px;
  color: var(--el-text-color-secondary);
  margin-top: 8px;
  font-weight: 500;
}

.chart-row {
  margin-bottom: 20px;
}

.chart-card {
  background: #fff;
  border-radius: 8px;
  border: 1px solid var(--el-border-color);
  padding: 20px;
  margin-bottom: 20px;
}

.chart-title {
  font-size: 14px;
  font-weight: 600;
  color: var(--el-text-color-primary);
  margin-bottom: 8px;
}

.chart-body {
  height: 300px;
}

.recent-text {
  font-size: 13px;
  color: var(--el-text-color-regular);
}

.recent-time {
  font-size: 12px;
  color: var(--el-text-color-secondary);
}
</style>
```

- [ ] **Step 2: Verify Dashboard builds**

Run: `cd frontend && npx vite build --mode development 2>&1 | tail -5`

---

### Task 5: Fix ContentList.vue — debounce, common utils, empty state, skeleton, inline styles

**Files:**
- Modify: `frontend/src/views/contents/ContentList.vue`

- [ ] **Step 1: Rewrite ContentList.vue**

```vue
<script setup lang="ts">
import { ref, onMounted, watch } from 'vue'
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
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npx vite build --mode development 2>&1 | tail -5`

---

### Task 6: Fix PromptList.vue — debounce, common utils, empty state, skeleton, inline styles

**Files:**
- Modify: `frontend/src/views/prompts/PromptList.vue`

- [ ] **Step 1: Rewrite PromptList.vue**

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkspaceStore } from '@/stores/workspace'
import { listPrompts, deletePrompt, updatePrompt } from '@/api/prompts'
import { canEdit } from '@/utils/permission'
import { formatDate } from '@/utils/common'
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
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npx vite build --mode development 2>&1 | tail -5`

---

### Task 7: Fix ReviewCenter.vue — debounce, common utils, empty state, skeleton, inline styles

**Files:**
- Modify: `frontend/src/views/reviews/ReviewCenter.vue`

- [ ] **Step 1: Rewrite ReviewCenter.vue**

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useWorkspaceStore } from '@/stores/workspace'
import { listReviews, approveContent, rejectContent, batchReview, submitForReview } from '@/api/reviews'
import { listMembers } from '@/api/workspaces'
import { canEdit } from '@/utils/permission'
import { statusMap, truncate, formatDate } from '@/utils/common'
import { useDebouncedWatch } from '@/composables/useDebouncedWatch'
import SkeletonTable from '@/components/SkeletonTable.vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const workspaceStore = useWorkspaceStore()
const reviews = ref<any[]>([])
const total = ref(0)
const page = ref(1)
const statusFilter = ref('')
const loading = ref(false)
const firstLoad = ref(true)
const selectedIds = ref<string[]>([])
const showSubmitDialog = ref(false)
const showRejectDialog = ref(false)
const members = ref<any[]>([])
const submitForm = ref({ content_id: '', reviewer_id: '' })
const rejectForm = ref({ content_id: '', comment: '' })

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
    firstLoad.value = false
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
useDebouncedWatch([page, statusFilter], fetchReviews, 300)

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
</script>

<template>
  <div>
    <div class="page-header">
      <h3 class="page-heading">审核中心</h3>
      <div v-if="canEdit()">
        <el-button @click="handleBatch('approve')" :disabled="selectedIds.length === 0">批量通过</el-button>
        <el-button type="danger" @click="handleBatch('reject')" :disabled="selectedIds.length === 0">批量驳回</el-button>
      </div>
    </div>

    <el-select v-model="statusFilter" placeholder="状态筛选" clearable class="filter-select">
      <el-option label="待审核" value="pending_review" />
      <el-option label="已通过" value="approved" />
      <el-option label="已驳回" value="rejected" />
      <el-option label="草稿" value="draft" />
    </el-select>

    <SkeletonTable v-if="firstLoad && loading" />

    <template v-else-if="reviews.length === 0">
      <el-empty description="暂无审核内容" />
    </template>

    <template v-else>
      <el-table :data="reviews" v-loading="loading" @selection-change="handleSelectionChange">
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
            <span v-else class="text-muted">—</span>
          </template>
        </el-table-column>
        <el-table-column label="创建时间" width="180">
          <template #default="{ row }">
            {{ formatDate(row.created_at) }}
          </template>
        </el-table-column>
        <el-table-column label="操作" width="240">
          <template #default="{ row }">
            <template v-if="row.status === 'draft' && canEdit()">
              <el-button size="small" type="primary" @click="openSubmit(row.id)">提交审核</el-button>
            </template>
            <template v-if="row.status === 'pending_review' && canEdit()">
              <el-button size="small" type="success" @click="handleApprove(row.id)">通过</el-button>
              <el-button size="small" type="danger" @click="openReject(row.id)">驳回</el-button>
            </template>
          </template>
        </el-table-column>
      </el-table>
    </template>

    <div class="pagination-wrap" v-if="total > 0">
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
.filter-select {
  margin-bottom: 16px;
}
.text-muted {
  color: #999;
}
.pagination-wrap {
  margin-top: 16px;
  display: flex;
  justify-content: flex-end;
}
</style>
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npx vite build --mode development 2>&1 | tail -5`

---

### Task 8: Fix WorkspaceList.vue — empty state, skeleton, inline styles

**Files:**
- Modify: `frontend/src/views/workspaces/WorkspaceList.vue`

- [ ] **Step 1: Rewrite WorkspaceList.vue**

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkspaceStore } from '@/stores/workspace'
import { createWorkspace, deleteWorkspace } from '@/api/workspaces'
import { canEdit } from '@/utils/permission'
import { formatDate } from '@/utils/common'
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
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npx vite build --mode development 2>&1 | tail -5`

---

### Task 9: Fix ModelList.vue — empty state, skeleton, inline styles

**Files:**
- Modify: `frontend/src/views/models/ModelList.vue`

- [ ] **Step 1: Rewrite ModelList.vue**

```vue
<script setup lang="ts">
import { ref, watch, onMounted } from 'vue'
import { useWorkspaceStore } from '@/stores/workspace'
import { listModels, createModel, updateModel, deleteModel, toggleModel } from '@/api/aiModels'
import { canEdit } from '@/utils/permission'
import SkeletonTable from '@/components/SkeletonTable.vue'
import { ElMessage, ElMessageBox } from 'element-plus'

const workspaceStore = useWorkspaceStore()
const models = ref<any[]>([])
const showCreate = ref(false)
const editingModel = ref<any>(null)
const loading = ref(false)
const firstLoad = ref(true)

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
    firstLoad.value = false
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
    <div class="page-header">
      <h3 class="page-heading">AI 模型配置</h3>
      <el-button v-if="canEdit()" type="primary" @click="resetForm(); editingModel = null; showCreate = true">添加模型</el-button>
    </div>

    <SkeletonTable v-if="firstLoad && loading" />

    <template v-else-if="models.length === 0">
      <el-empty description="暂无模型配置" />
    </template>

    <template v-else>
      <el-table :data="models" v-loading="loading">
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
    </template>

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
</style>
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npx vite build --mode development 2>&1 | tail -5`

---

### Task 10: Fix Settings.vue and ContentCreate/CreateDetail — inline styles

**Files:**
- Modify: `frontend/src/views/Settings.vue`
- Modify: `frontend/src/views/contents/ContentCreate.vue`
- Modify: `frontend/src/views/contents/ContentDetail.vue`

- [ ] **Step 1: Rewrite Settings.vue — extract inline styles to scoped block**

```vue
<script setup lang="ts">
import { ref, reactive } from 'vue'
import { updateProfile, changePassword } from '@/api/auth'
import { useUserStore } from '@/stores/user'
import { ElMessage } from 'element-plus'

const userStore = useUserStore()

const profileForm = reactive({
  username: userStore.userInfo?.username || '',
  email: userStore.userInfo?.email || '',
})
const profileLoading = ref(false)

const passwordForm = reactive({
  current_password: '',
  new_password: '',
  confirm_password: '',
})
const passwordLoading = ref(false)

async function handleUpdateProfile() {
  if (!profileForm.username || !profileForm.email) {
    ElMessage.warning('请填写完整信息')
    return
  }
  profileLoading.value = true
  try {
    await updateProfile({ username: profileForm.username, email: profileForm.email })
    await userStore.fetchUser()
    ElMessage.success('个人资料已更新')
  } catch {
    // handled by interceptor
  } finally {
    profileLoading.value = false
  }
}

async function handleChangePassword() {
  if (!passwordForm.current_password || !passwordForm.new_password) {
    ElMessage.warning('请填写密码')
    return
  }
  if (passwordForm.new_password !== passwordForm.confirm_password) {
    ElMessage.warning('两次输入的新密码不一致')
    return
  }
  if (passwordForm.new_password.length < 6) {
    ElMessage.warning('新密码长度至少 6 位')
    return
  }
  passwordLoading.value = true
  try {
    await changePassword({
      current_password: passwordForm.current_password,
      new_password: passwordForm.new_password,
    })
    ElMessage.success('密码已修改，下次登录请使用新密码')
    passwordForm.current_password = ''
    passwordForm.new_password = ''
    passwordForm.confirm_password = ''
  } catch {
    // handled by interceptor
  } finally {
    passwordLoading.value = false
  }
}
</script>

<template>
  <div class="settings-page">
    <h3 class="settings-title">个人设置</h3>

    <el-card class="settings-card">
      <template #header><span class="card-header-title">个人资料</span></template>
      <el-form label-width="100px">
        <el-form-item label="用户名">
          <el-input v-model="profileForm.username" placeholder="用户名" />
        </el-form-item>
        <el-form-item label="邮箱">
          <el-input v-model="profileForm.email" placeholder="邮箱" />
        </el-form-item>
        <el-form-item label="角色">
          <el-tag>{{ userStore.userInfo?.role }}</el-tag>
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="profileLoading" @click="handleUpdateProfile">保存修改</el-button>
        </el-form-item>
      </el-form>
    </el-card>

    <el-card>
      <template #header><span class="card-header-title">修改密码</span></template>
      <el-form label-width="100px">
        <el-form-item label="当前密码">
          <el-input v-model="passwordForm.current_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="新密码">
          <el-input v-model="passwordForm.new_password" type="password" show-password />
        </el-form-item>
        <el-form-item label="确认密码">
          <el-input v-model="passwordForm.confirm_password" type="password" show-password />
        </el-form-item>
        <el-form-item>
          <el-button type="primary" :loading="passwordLoading" @click="handleChangePassword">修改密码</el-button>
        </el-form-item>
      </el-form>
    </el-card>
  </div>
</template>

<style scoped>
.settings-page {
  max-width: 600px;
}
.settings-title {
  margin-bottom: 24px;
}
.settings-card {
  margin-bottom: 24px;
}
.card-header-title {
  font-weight: bold;
}
</style>
```

- [ ] **Step 2: Rewrite ContentCreate.vue — extract inline styles**

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRouter } from 'vue-router'
import { useWorkspaceStore } from '@/stores/workspace'
import { listPrompts } from '@/api/prompts'
import { listModels } from '@/api/aiModels'
import { generateContentStream } from '@/api/contents'
import { submitForReview } from '@/api/reviews'
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
const generatedContentId = ref('')
const submitting = ref(false)

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
  generatedContentId.value = ''

  await generateContentStream(
    {
      workspace_id: workspaceStore.currentWorkspace.id,
      prompt_id: selectedPrompt.value,
      model_id: selectedModelId.value,
      variables: variables.value,
    },
    (chunk: string) => {
      const cidMarker = '__CID__:'
      if (chunk.includes(cidMarker)) {
        const [text, cid] = chunk.split(cidMarker)
        resultText.value += text
        generatedContentId.value = cid.replace(/\n/g, '').trim()
      } else {
        resultText.value += chunk
      }
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

async function handleSubmitReview() {
  if (!generatedContentId.value) return
  submitting.value = true
  try {
    await submitForReview(generatedContentId.value)
    ElMessage.success('已提交审核')
    generatedContentId.value = ''
  } catch {
    // handled by interceptor
  } finally {
    submitting.value = false
  }
}

function handleCopy() {
  navigator.clipboard.writeText(resultText.value)
  ElMessage.success('已复制到剪贴板')
}
</script>

<template>
  <div>
    <h3 class="page-heading">生成内容</h3>
    <el-form label-width="100px" class="generate-form">
      <el-form-item label="Prompt 模板">
        <el-select v-model="selectedPrompt" placeholder="选择 Prompt" @change="onPromptChange" class="full-width">
          <el-option v-for="p in prompts" :key="p.id" :label="p.title" :value="p.id" />
        </el-select>
      </el-form-item>

      <el-form-item label="AI 模型">
        <el-select v-model="selectedModelId" placeholder="选择模型" class="full-width">
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

    <div v-if="showResult" class="result-area">
      <div class="result-header">
        <h4>生成结果</h4>
        <div class="result-actions">
          <el-button size="small" type="success" @click="handleSubmitReview" :disabled="generating || !generatedContentId" :loading="submitting">提交审核</el-button>
          <el-button size="small" @click="handleCopy" :disabled="generating">复制</el-button>
        </div>
      </div>
      <el-input type="textarea" :model-value="resultText" :rows="15" readonly />
    </div>
  </div>
</template>

<style scoped>
.generate-form {
  max-width: 800px;
  margin-top: 16px;
}
.full-width {
  width: 100%;
}
.result-area {
  margin-top: 24px;
  max-width: 800px;
}
.result-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 8px;
}
.result-actions {
  display: flex;
  gap: 8px;
}
</style>
```

- [ ] **Step 3: Rewrite ContentDetail.vue — extract inline styles**

```vue
<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { getContent, updateContent } from '@/api/contents'
import { exportMarkdown } from '@/api/export'
import { formatDate } from '@/utils/common'
import { ElMessage } from 'element-plus'

const route = useRoute()
const router = useRouter()
const content = ref<any>(null)
const editText = ref('')
const editing = ref(false)

onMounted(async () => {
  content.value = await getContent(route.params.id as string)
  editText.value = content.value.edited_text || content.value.generated_text
})

async function handleSave() {
  await updateContent(content.value.id, { edited_text: editText.value })
  ElMessage.success('保存成功')
  editing.value = false
  content.value = await getContent(route.params.id as string)
}

function handleCopy() {
  navigator.clipboard.writeText(editText.value)
  ElMessage.success('已复制到剪贴板')
}

function handleExportMarkdown() {
  exportMarkdown(content.value.id)
}
</script>

<template>
  <div v-if="content">
    <div class="detail-header">
      <h3 class="page-heading">内容详情</h3>
      <div class="detail-actions">
        <el-button @click="handleCopy">复制</el-button>
        <el-button v-if="!editing" @click="editing = true">编辑</el-button>
        <el-button v-if="editing" type="primary" @click="handleSave">保存</el-button>
        <el-button @click="handleExportMarkdown">导出 Markdown</el-button>
        <el-button @click="router.push('/contents')">返回列表</el-button>
      </div>
    </div>

    <el-descriptions :column="2" border class="detail-meta">
      <el-descriptions-item label="状态">{{ content.status }}</el-descriptions-item>
      <el-descriptions-item label="Token 消耗">{{ content.token_usage || '暂不支持' }}</el-descriptions-item>
      <el-descriptions-item label="生成耗时">{{ content.generation_time_ms }}ms</el-descriptions-item>
      <el-descriptions-item label="创建时间">{{ formatDate(content.created_at) }}</el-descriptions-item>
    </el-descriptions>

    <el-input v-model="editText" type="textarea" :rows="15" :readonly="!editing" />
  </div>
</template>

<style scoped>
.detail-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  margin-bottom: 16px;
}
.page-heading {
  margin-bottom: 0;
}
.detail-actions {
  display: flex;
  gap: 8px;
}
.detail-meta {
  margin-bottom: 16px;
}
</style>
```

- [ ] **Step 4: Verify build for all three files**

Run: `cd frontend && npx vite build --mode development 2>&1 | tail -5`

---

### Task 11: Fix MainLayout.vue — workspace switcher in header

**Files:**
- Modify: `frontend/src/layouts/MainLayout.vue`

- [ ] **Step 1: Rewrite MainLayout.vue with workspace switcher**

```vue
<script setup lang="ts">
import { ref, watch } from 'vue'
import { useRouter } from 'vue-router'
import { useUserStore } from '@/stores/user'
import { useWorkspaceStore } from '@/stores/workspace'

const userStore = useUserStore()
const workspaceStore = useWorkspaceStore()
const router = useRouter()
const isCollapse = ref(false)

function handleCommand(command: string) {
  if (command === 'logout') {
    userStore.logout()
  } else if (command === 'settings') {
    router.push('/settings')
  }
}

function handleWorkspaceChange(id: string) {
  workspaceStore.switchWorkspace(id)
}
</script>

<template>
  <el-container class="app-shell">
    <el-aside :width="isCollapse ? '64px' : '220px'" class="app-sidebar">
      <div class="sidebar-brand">
        <span v-if="!isCollapse" class="brand-text">AI Studio</span>
        <span v-else class="brand-icon">AI</span>
      </div>

      <el-menu
        :default-active="$route.path"
        :collapse="isCollapse"
        background-color="transparent"
        text-color="var(--sidebar-text)"
        active-text-color="var(--sidebar-active-text)"
        router
        class="sidebar-menu"
      >
        <el-menu-item index="/dashboard">
          <el-icon><DataBoard /></el-icon>
          <template #title>数据看板</template>
        </el-menu-item>
        <el-menu-item index="/workspaces">
          <el-icon><Folder /></el-icon>
          <template #title>工作空间</template>
        </el-menu-item>
        <el-menu-item index="/prompts">
          <el-icon><Document /></el-icon>
          <template #title>Prompt 管理</template>
        </el-menu-item>
        <el-menu-item index="/contents">
          <el-icon><EditPen /></el-icon>
          <template #title>内容管理</template>
        </el-menu-item>
        <el-menu-item index="/reviews">
          <el-icon><Checked /></el-icon>
          <template #title>审核中心</template>
        </el-menu-item>
        <el-menu-item index="/models">
          <el-icon><Cpu /></el-icon>
          <template #title>AI 模型</template>
        </el-menu-item>
        <el-menu-item index="/settings">
          <el-icon><Setting /></el-icon>
          <template #title>个人设置</template>
        </el-menu-item>
      </el-menu>
    </el-aside>

    <el-container class="app-main">
      <el-header class="app-header">
        <div class="header-left">
          <el-icon class="collapse-btn" @click="isCollapse = !isCollapse">
            <Fold v-if="!isCollapse" />
            <Expand v-else />
          </el-icon>

          <el-select
            :model-value="workspaceStore.currentWorkspace?.id"
            @change="handleWorkspaceChange"
            placeholder="选择空间"
            size="default"
            class="workspace-switcher"
          >
            <el-option
              v-for="ws in workspaceStore.workspaces"
              :key="ws.id"
              :label="ws.name"
              :value="ws.id"
            />
          </el-select>
        </div>

        <div class="header-right">
          <el-dropdown @command="handleCommand" trigger="click">
            <span class="user-trigger">
              <span class="user-avatar">{{ userStore.userInfo?.username?.charAt(0)?.toUpperCase() }}</span>
              <span class="user-name">{{ userStore.userInfo?.username }}</span>
              <el-icon><ArrowDown /></el-icon>
            </span>
            <template #dropdown>
              <el-dropdown-menu>
                <el-dropdown-item command="settings">
                  <el-icon><Setting /></el-icon>个人设置
                </el-dropdown-item>
                <el-dropdown-item command="logout" divided>
                  <el-icon><SwitchButton /></el-icon>退出登录
                </el-dropdown-item>
              </el-dropdown-menu>
            </template>
          </el-dropdown>
        </div>
      </el-header>

      <el-main class="app-content">
        <router-view />
      </el-main>
    </el-container>
  </el-container>
</template>

<style scoped>
.app-shell {
  height: 100vh;
}

.app-sidebar {
  background: var(--sidebar-bg);
  display: flex;
  flex-direction: column;
  overflow: hidden;
  transition: width 0.2s ease;
}

.sidebar-brand {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: center;
  color: #e5e7eb;
  font-size: 18px;
  font-weight: 700;
  letter-spacing: -0.02em;
  border-bottom: 1px solid rgba(255, 255, 255, 0.06);
  flex-shrink: 0;
}

.sidebar-menu {
  flex: 1;
  border-right: none;
  padding-top: 8px;
}

.sidebar-menu .el-menu-item {
  margin: 2px 8px;
  border-radius: 6px;
  height: 40px;
  line-height: 40px;
  font-size: 14px;
  transition: all 0.15s ease;
}

.sidebar-menu .el-menu-item:hover {
  background: var(--sidebar-hover-bg);
}

.sidebar-menu .el-menu-item.is-active {
  background: var(--sidebar-active-bg);
  font-weight: 500;
}

.app-main {
  display: flex;
  flex-direction: column;
}

.app-header {
  height: 56px;
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 0 24px;
  background: #fff;
  border-bottom: 1px solid var(--el-border-color);
  flex-shrink: 0;
}

.header-left {
  display: flex;
  align-items: center;
  gap: 16px;
}

.collapse-btn {
  cursor: pointer;
  font-size: 18px;
  color: var(--el-text-color-secondary);
  transition: color 0.15s;
}

.collapse-btn:hover {
  color: var(--el-text-color-primary);
}

.workspace-switcher {
  width: 200px;
}

.header-right {
  display: flex;
  align-items: center;
  gap: 16px;
}

.user-trigger {
  display: flex;
  align-items: center;
  gap: 8px;
  cursor: pointer;
  padding: 4px 8px;
  border-radius: 6px;
  transition: background 0.15s;
}

.user-trigger:hover {
  background: var(--el-bg-color-page);
}

.user-avatar {
  width: 28px;
  height: 28px;
  border-radius: 50%;
  background: var(--el-color-primary);
  color: #fff;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 12px;
  font-weight: 600;
}

.user-name {
  font-size: 14px;
  color: var(--el-text-color-primary);
}

.app-content {
  background: var(--el-bg-color-page);
  padding: 24px;
  overflow-y: auto;
}
</style>
```

- [ ] **Step 2: Verify build**

Run: `cd frontend && npx vite build --mode development 2>&1 | tail -5`

---

### Task 12: Full build and test verification

- [ ] **Step 1: Run full production build**

Run: `cd frontend && npx vite build 2>&1 | tail -10`
Expected: Build completes without errors

- [ ] **Step 2: Run existing tests**

Run: `cd frontend && npx vitest run 2>&1`
Expected: All existing tests pass

- [ ] **Step 3: Commit all changes**

```bash
cd E:/lx/projects/ai-content-studio
git add frontend/src/utils/common.ts
git add frontend/src/composables/useDebouncedWatch.ts
git add frontend/src/components/SkeletonCard.vue
git add frontend/src/components/SkeletonChart.vue
git add frontend/src/components/SkeletonTable.vue
git add frontend/src/views/Dashboard.vue
git add frontend/src/views/contents/ContentList.vue
git add frontend/src/views/prompts/PromptList.vue
git add frontend/src/views/reviews/ReviewCenter.vue
git add frontend/src/views/workspaces/WorkspaceList.vue
git add frontend/src/views/models/ModelList.vue
git add frontend/src/views/Settings.vue
git add frontend/src/views/contents/ContentCreate.vue
git add frontend/src/views/contents/ContentDetail.vue
git add frontend/src/layouts/MainLayout.vue
git commit -m "refactor: optimize frontend — memory leaks, debounce, skeleton, empty states, responsive layout"
```
