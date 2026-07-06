import request from './request'
import type { ApiResponse, PaginatedResponse, PromptItem, PromptVersionItem } from './types'

export function listPrompts(params: {
  workspace_id: string
  category?: string
  search?: string
  page?: number
  page_size?: number
}): Promise<ApiResponse<PaginatedResponse<PromptItem>>> {
  return request.get('/prompts', { params })
}

export function createPrompt(data: {
  workspace_id: string
  title: string
  content: string
  category?: string
  tags?: string[]
}): Promise<PromptItem> {
  return request.post('/prompts', data)
}

export function getPrompt(id: string): Promise<PromptItem> {
  return request.get(`/prompts/${id}`)
}

export function updatePrompt(id: string, data: {
  title?: string
  content?: string
  category?: string
  tags?: string[]
  is_favorite?: boolean
}): Promise<PromptItem> {
  return request.put(`/prompts/${id}`, data)
}

export function deletePrompt(id: string): Promise<void> {
  return request.delete(`/prompts/${id}`)
}

export function listVersions(promptId: string): Promise<PromptVersionItem[]> {
  return request.get(`/prompts/${promptId}/versions`)
}

export function rollbackVersion(promptId: string, version: number): Promise<void> {
  return request.post(`/prompts/${promptId}/rollback/${version}`)
}
