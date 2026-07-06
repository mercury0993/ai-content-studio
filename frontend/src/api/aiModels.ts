import request from './request'
import type { ModelItem } from './types'

export function listModels(workspaceId: string): Promise<ModelItem[]> {
  return request.get('/models', { params: { workspace_id: workspaceId } })
}

export function createModel(data: {
  workspace_id: string
  name: string
  provider: string
  api_key?: string
  base_url?: string
  model_name: string
  default_params?: Record<string, number>
}): Promise<ModelItem> {
  return request.post('/models', data)
}

export function updateModel(id: string, data: {
  name?: string
  provider?: string
  api_key?: string
  base_url?: string
  model_name?: string
  default_params?: Record<string, number>
}): Promise<ModelItem> {
  return request.put(`/models/${id}`, data)
}

export function deleteModel(id: string): Promise<void> {
  return request.delete(`/models/${id}`)
}

export function toggleModel(id: string): Promise<ModelItem> {
  return request.patch(`/models/${id}/toggle`)
}
