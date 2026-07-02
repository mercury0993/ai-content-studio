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

export async function generateContentStream(
  data: {
    workspace_id: string
    prompt_id: string
    model_id: string
    variables?: Record<string, string>
  },
  onChunk: (text: string) => void,
  onDone: () => void,
  onError: (error: string) => void,
) {
  const token = localStorage.getItem('access_token')
  try {
    const response = await fetch('/api/v1/contents/generate-stream', {
      method: 'POST',
      headers: {
        'Content-Type': 'application/json',
        Authorization: `Bearer ${token}`,
      },
      body: JSON.stringify(data),
    })

    if (!response.ok) {
      const err = await response.json().catch(() => ({ detail: '生成失败' }))
      onError(err.detail || '生成失败')
      return
    }

    const reader = response.body!.getReader()
    const decoder = new TextDecoder()

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      onChunk(decoder.decode(value, { stream: true }))
    }
    onDone()
  } catch {
    onError('网络请求失败')
  }
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
