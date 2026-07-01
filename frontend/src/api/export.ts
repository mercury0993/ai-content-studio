import { ElMessage } from 'element-plus'

function getToken(): string {
  return localStorage.getItem('access_token') || ''
}

async function downloadBlob(url: string, filename: string, method: 'GET' | 'POST' = 'GET', body?: any) {
  const options: RequestInit = {
    method,
    headers: { Authorization: `Bearer ${getToken()}` },
  }
  if (body) {
    options.headers = { ...options.headers, 'Content-Type': 'application/json' }
    options.body = JSON.stringify(body)
  }
  const resp = await fetch(url, options)
  if (!resp.ok) {
    ElMessage.error('导出失败')
    return
  }
  const blob = await resp.blob()
  const objectUrl = URL.createObjectURL(blob)
  const a = document.createElement('a')
  a.href = objectUrl
  a.download = filename
  a.click()
  URL.revokeObjectURL(objectUrl)
}

export function exportMarkdown(contentId: string) {
  return downloadBlob(`/api/v1/export/markdown/${contentId}`, `content_${contentId.slice(0, 8)}.md`)
}

export function exportZip(contentIds: string[]) {
  return downloadBlob('/api/v1/export/zip', 'contents.zip', 'POST', contentIds)
}
