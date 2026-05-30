import request from './request'

export function listContents(params: {
  workspace_id: string
  status?: string
  page?: number
  page_size?: number
}) {
  return request.get('/contents', { params })
}

export function generateContent(data: {
  workspace_id: string
  prompt_id: string
  model_id: string
  variables?: Record<string, string>
}) {
  return request.post('/contents/generate', data)
}

export function getContent(id: string) {
  return request.get(`/contents/${id}`)
}

export function updateContent(id: string, data: { edited_text?: string }) {
  return request.put(`/contents/${id}`, data)
}

export function deleteContent(id: string) {
  return request.delete(`/contents/${id}`)
}
