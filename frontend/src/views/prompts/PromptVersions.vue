<script setup lang="ts">
import { ref, onMounted } from 'vue'
import { useRoute, useRouter } from 'vue-router'
import { listVersions, rollbackVersion } from '@/api/prompts'
import { ElMessage, ElMessageBox } from 'element-plus'

const route = useRoute()
const router = useRouter()
const versions = ref<any[]>([])

onMounted(async () => {
  versions.value = await listVersions(route.params.id as string) as any
})

async function handleRollback(version: number) {
  await ElMessageBox.confirm(`确定回滚到版本 ${version}？`, '提示', { type: 'warning' })
  await rollbackVersion(route.params.id as string, version)
  ElMessage.success('回滚成功')
  router.push('/prompts')
}
</script>

<template>
  <div>
    <div style="display: flex; align-items: center; gap: 12px; margin-bottom: 16px;">
      <h3>版本历史</h3>
      <el-button @click="router.push('/prompts')">返回列表</el-button>
    </div>

    <el-timeline>
      <el-timeline-item v-for="v in versions" :key="v.id" :timestamp="new Date(v.created_at).toLocaleString()">
        <el-card>
          <h4>版本 {{ v.version }}</h4>
          <el-input type="textarea" :model-value="v.content" :rows="4" readonly />
          <el-button size="small" style="margin-top: 8px;" @click="handleRollback(v.version)">回滚到此版本</el-button>
        </el-card>
      </el-timeline-item>
    </el-timeline>
  </div>
</template>
