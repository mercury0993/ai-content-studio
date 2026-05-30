import request from './request'

export function listPrompts(params: {
  workspace_id: string
  category?: string
  search?: string
  page?: number
  page_size?: number
}) {
  return request.get('/prompts', { params })
}

export function createPrompt(data: {
  workspace_id: string
  title: string
  content: string
  category?: string
  tags?: string[]
}) {
  return request.post('/prompts', data)
}

export function getPrompt(id: string) {
  return request.get(`/prompts/${id}`)
}

export function updatePrompt(id: string, data: {
  title?: string
  content?: string
  category?: string
  tags?: string[]
  is_favorite?: boolean
}) {
  return request.put(`/prompts/${id}`, data)
}

export function deletePrompt(id: string) {
  return request.delete(`/prompts/${id}`)
}

export function listVersions(promptId: string) {
  return request.get(`/prompts/${promptId}/versions`)
}

export function rollbackVersion(promptId: string, version: number) {
  return request.post(`/prompts/${promptId}/rollback/${version}`)
}
