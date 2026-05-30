import request from './request'

export function listModels(workspaceId: string) {
  return request.get('/models', { params: { workspace_id: workspaceId } })
}

export function createModel(data: {
  workspace_id: string
  name: string
  provider: string
  api_key?: string
  base_url?: string
  model_name: string
  default_params?: Record<string, any>
}) {
  return request.post('/models', data)
}

export function updateModel(id: string, data: Record<string, any>) {
  return request.put(`/models/${id}`, data)
}

export function deleteModel(id: string) {
  return request.delete(`/models/${id}`)
}

export function toggleModel(id: string) {
  return request.patch(`/models/${id}/toggle`)
}
