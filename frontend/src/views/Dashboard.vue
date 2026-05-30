<script setup lang="ts">
import { ref, onMounted, watch, nextTick } from 'vue'
import { useWorkspaceStore } from '@/stores/workspace'
import { getStats, getTrend, getModelUsage, getUserRanking, getRecent } from '@/api/dashboard'
import * as echarts from 'echarts'

const workspaceStore = useWorkspaceStore()

const stats = ref({ prompt_count: 0, content_count: 0, monthly_generated: 0, pending_review: 0 })
const recentItems = ref<any[]>([])

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

  await nextTick()
  renderTrendChart(trendData.data)
  renderModelChart(modelData.data)
  renderRankingChart(rankingData.data)
}

function renderTrendChart(data: { date: string; count: number }[]) {
  const el = document.getElementById('trend-chart')
  if (!el) return
  if (!trendChart) trendChart = echarts.init(el)
  trendChart.setOption({
    title: { text: '近 30 天生成趋势', left: 'center' },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: data.map((d) => d.date.slice(5)) },
    yAxis: { type: 'value', minInterval: 1 },
    series: [{ data: data.map((d) => d.count), type: 'line', smooth: true, areaStyle: { opacity: 0.3 } }],
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  })
}

function renderModelChart(data: { name: string; count: number }[]) {
  const el = document.getElementById('model-chart')
  if (!el) return
  if (!modelChart) modelChart = echarts.init(el)
  modelChart.setOption({
    title: { text: '模型使用占比', left: 'center' },
    tooltip: { trigger: 'item' },
    series: [{
      type: 'pie',
      radius: '60%',
      data: data.map((d) => ({ name: d.name, value: d.count })),
      emphasis: { itemStyle: { shadowBlur: 10, shadowOffsetX: 0, shadowColor: 'rgba(0, 0, 0, 0.5)' } },
    }],
  })
}

function renderRankingChart(data: { username: string; count: number }[]) {
  const el = document.getElementById('ranking-chart')
  if (!el) return
  if (!rankingChart) rankingChart = echarts.init(el)
  rankingChart.setOption({
    title: { text: '用户生成量排名', left: 'center' },
    tooltip: { trigger: 'axis' },
    xAxis: { type: 'category', data: data.map((d) => d.username) },
    yAxis: { type: 'value', minInterval: 1 },
    series: [{ data: data.map((d) => d.count), type: 'bar' }],
    grid: { left: '3%', right: '4%', bottom: '3%', containLabel: true },
  })
}

onMounted(fetchDashboard)
watch(() => workspaceStore.currentWorkspace, fetchDashboard)

const statusMap: Record<string, { label: string; type: string }> = {
  draft: { label: '草稿', type: 'info' },
  pending_review: { label: '待审核', type: 'warning' },
  approved: { label: '已通过', type: 'success' },
  rejected: { label: '已驳回', type: 'danger' },
}
</script>

<template>
  <div>
    <h3>数据看板</h3>

    <el-row :gutter="16" style="margin-bottom: 24px;">
      <el-col :span="6">
        <el-card shadow="hover">
          <div style="text-align: center;">
            <div style="font-size: 32px; font-weight: bold; color: #409EFF;">{{ stats.prompt_count }}</div>
            <div style="color: #999;">Prompt 总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div style="text-align: center;">
            <div style="font-size: 32px; font-weight: bold; color: #67C23A;">{{ stats.content_count }}</div>
            <div style="color: #999;">内容总数</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div style="text-align: center;">
            <div style="font-size: 32px; font-weight: bold; color: #E6A23C;">{{ stats.monthly_generated }}</div>
            <div style="color: #999;">本月生成</div>
          </div>
        </el-card>
      </el-col>
      <el-col :span="6">
        <el-card shadow="hover">
          <div style="text-align: center;">
            <div style="font-size: 32px; font-weight: bold; color: #F56C6C;">{{ stats.pending_review }}</div>
            <div style="color: #999;">待审核</div>
          </div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-bottom: 24px;">
      <el-col :span="16">
        <el-card>
          <div id="trend-chart" style="height: 300px;"></div>
        </el-card>
      </el-col>
      <el-col :span="8">
        <el-card>
          <div id="model-chart" style="height: 300px;"></div>
        </el-card>
      </el-col>
    </el-row>

    <el-row :gutter="16" style="margin-bottom: 24px;">
      <el-col :span="12">
        <el-card>
          <div id="ranking-chart" style="height: 300px;"></div>
        </el-card>
      </el-col>
      <el-col :span="12">
        <el-card>
          <template #header><span>最近生成记录</span></template>
          <el-table :data="recentItems" style="width: 100%;" max-height="260">
            <el-table-column label="内容" min-width="200">
              <template #default="{ row }">
                {{ (row.edited_text || row.generated_text || '').slice(0, 40) }}...
              </template>
            </el-table-column>
            <el-table-column label="状态" width="100">
              <template #default="{ row }">
                <el-tag :type="statusMap[row.status]?.type as any" size="small">{{ statusMap[row.status]?.label }}</el-tag>
              </template>
            </el-table-column>
            <el-table-column label="时间" width="140">
              <template #default="{ row }">
                {{ new Date(row.created_at).toLocaleString() }}
              </template>
            </el-table-column>
          </el-table>
        </el-card>
      </el-col>
    </el-row>
  </div>
</template>
