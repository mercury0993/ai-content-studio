import request from './request'
import type { ApiResponse, DashboardStats, TrendItem, ModelUsageItem, UserRankingItem, ContentItem } from './types'

export function getStats(workspaceId: string) {
  return request.get<ApiResponse<DashboardStats>>('/dashboard/stats', { params: { workspace_id: workspaceId } })
}

export function getTrend(workspaceId: string, days: number = 30) {
  return request.get<ApiResponse<TrendItem[]>>('/dashboard/trend', { params: { workspace_id: workspaceId, days } })
}

export function getModelUsage(workspaceId: string) {
  return request.get<ApiResponse<ModelUsageItem[]>>('/dashboard/model-usage', { params: { workspace_id: workspaceId } })
}

export function getUserRanking(workspaceId: string) {
  return request.get<ApiResponse<UserRankingItem[]>>('/dashboard/user-ranking', { params: { workspace_id: workspaceId } })
}

export function getRecent(workspaceId: string, limit: number = 10) {
  return request.get<ApiResponse<ContentItem[]>>('/dashboard/recent', { params: { workspace_id: workspaceId, limit } })
}
