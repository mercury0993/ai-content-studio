import request from './request'
import type { ApiResponse, PaginatedResponse, ContentItem } from './types'

export function listContents(params: {
  workspace_id: string
  status?: string
  page?: number
  page_size?: number
}): Promise<ApiResponse<PaginatedResponse<ContentItem>>> {
  return request.get('/contents', { params })
}

export function generateContent(data: {
  workspace_id: string
  prompt_id: string
  model_id: string
  variables?: Record<string, string>
}): Promise<ContentItem> {
  return request.post('/contents/generate', data)
}

function parseSSE(buffer: string): { events: { event: string; data: string }[]; remainder: string } {
  const events: { event: string; data: string }[] = []
  const lines = buffer.split('\n')
  const remainder = lines.pop() || ''

  let currentEvent = ''
  let currentData = ''

  for (const line of lines) {
    if (line.startsWith('event: ')) {
      currentEvent = line.slice(7)
    } else if (line.startsWith('data: ')) {
      currentData += (currentData ? '\n' : '') + line.slice(6)
    } else if (line === '') {
      if (currentData) {
        events.push({ event: currentEvent || 'message', data: currentData })
        currentEvent = ''
        currentData = ''
      }
    }
  }

  return { events, remainder }
}

export async function generateContentStream(
  data: {
    workspace_id: string
    prompt_id: string
    model_id: string
    variables?: Record<string, string>
  },
  onChunk: (text: string) => void,
  onDone: (contentId: string) => void,
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
    let buffer = ''

    while (true) {
      const { done, value } = await reader.read()
      if (done) break
      buffer += decoder.decode(value, { stream: true })

      const { events, remainder } = parseSSE(buffer)
      buffer = remainder

      for (const ev of events) {
        if (ev.event === 'done') {
          onDone(ev.data)
        } else {
          onChunk(ev.data)
        }
      }
    }
    onDone('')
  } catch {
    onError('网络请求失败')
  }
}

export function getContent(id: string): Promise<ContentItem> {
  return request.get(`/contents/${id}`)
}

export function updateContent(id: string, data: { edited_text?: string }): Promise<ContentItem> {
  return request.put(`/contents/${id}`, data)
}

export function deleteContent(id: string): Promise<void> {
  return request.delete(`/contents/${id}`)
}
