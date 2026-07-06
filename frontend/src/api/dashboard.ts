import request from './request'
import type { ApiResponse, DashboardStats, TrendItem, ModelUsageItem, UserRankingItem, ContentItem } from './types'

export function getStats(workspaceId: string): Promise<ApiResponse<DashboardStats>> {
  return request.get('/dashboard/stats', { params: { workspace_id: workspaceId } })
}

export function getTrend(workspaceId: string, days: number = 30): Promise<ApiResponse<TrendItem[]>> {
  return request.get('/dashboard/trend', { params: { workspace_id: workspaceId, days } })
}

export function getModelUsage(workspaceId: string): Promise<ApiResponse<ModelUsageItem[]>> {
  return request.get('/dashboard/model-usage', { params: { workspace_id: workspaceId } })
}

export function getUserRanking(workspaceId: string): Promise<ApiResponse<UserRankingItem[]>> {
  return request.get('/dashboard/user-ranking', { params: { workspace_id: workspaceId } })
}

export function getRecent(workspaceId: string, limit: number = 10): Promise<ApiResponse<ContentItem[]>> {
  return request.get('/dashboard/recent', { params: { workspace_id: workspaceId, limit } })
}
