import request from './request'
import type { ModelItem } from './types'

export function listModels(workspaceId: string) {
  return request.get<ModelItem[]>('/models', { params: { workspace_id: workspaceId } })
}

export function createModel(data: {
  workspace_id: string
  name: string
  provider: string
  api_key?: string
  base_url?: string
  model_name: string
  default_params?: Record<string, number>
}) {
  return request.post<ModelItem>('/models', data)
}

export function updateModel(id: string, data: {
  name?: string
  provider?: string
  api_key?: string
  base_url?: string
  model_name?: string
  default_params?: Record<string, number>
}) {
  return request.put<ModelItem>(`/models/${id}`, data)
}

export function deleteModel(id: string) {
  return request.delete(`/models/${id}`)
}

export function toggleModel(id: string) {
  return request.patch<ModelItem>(`/models/${id}/toggle`)
}
