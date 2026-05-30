import request from './request'

export function getStats(workspaceId: string) {
  return request.get('/dashboard/stats', { params: { workspace_id: workspaceId } })
}

export function getTrend(workspaceId: string, days: number = 30) {
  return request.get('/dashboard/trend', { params: { workspace_id: workspaceId, days } })
}

export function getModelUsage(workspaceId: string) {
  return request.get('/dashboard/model-usage', { params: { workspace_id: workspaceId } })
}

export function getUserRanking(workspaceId: string) {
  return request.get('/dashboard/user-ranking', { params: { workspace_id: workspaceId } })
}

export function getRecent(workspaceId: string, limit: number = 10) {
  return request.get('/dashboard/recent', { params: { workspace_id: workspaceId, limit } })
}
