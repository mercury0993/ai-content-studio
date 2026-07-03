<script setup lang="ts">
import { ref, onMounted, onUnmounted, watch, nextTick } from 'vue'
import { useWorkspaceStore } from '@/stores/workspace'
import { getStats, getTrend, getModelUsage, getUserRanking, getRecent } from '@/api/dashboard'
import { statusMap } from '@/utils/common'
import SkeletonCard from '@/components/SkeletonCard.vue'
import SkeletonChart from '@/components/SkeletonChart.vue'
import SkeletonTable from '@/components/SkeletonTable.vue'
import * as echarts from 'echarts'
import { ElMessage } from 'element-plus'

const workspaceStore = useWorkspaceStore()

const stats = ref({ prompt_count: 0, content_count: 0, monthly_generated: 0, pending_review: 0 })
const recentItems = ref<any[]>([])
const firstLoad = ref(true)

const trendChartRef = ref<HTMLElement>()
const modelChartRef = ref<HTMLElement>()
const rankingChartRef = ref<HTMLElement>()
let trendChart: echarts.ECharts | null = null
let modelChart: echarts.ECharts | null = null
let rankingChart: echarts.ECharts | null = null

async function fetchDashboard() {
  if (!workspaceStore.currentWorkspace) return
  const wsId = workspaceStore.currentWorkspace.id

  try {
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
  } catch (e) {
    console.error('Dashboard load failed:', e)
    ElMessage.error('数据加载失败，请刷新重试')
    firstLoad.value = false
  }
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
  const el = trendChartRef.value
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
  const el = modelChartRef.value
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
  const el = rankingChartRef.value
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
          <div ref="trendChartRef" class="chart-body"></div>
        </div>
      </el-col>
      <el-col :xs="24" :sm="24" :md="8">
        <div class="chart-card">
          <div class="chart-title">模型占比</div>
          <div ref="modelChartRef" class="chart-body"></div>
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
          <div ref="rankingChartRef" class="chart-body"></div>
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
