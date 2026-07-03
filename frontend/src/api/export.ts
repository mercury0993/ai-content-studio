import { ElMessage } from 'element-plus'
import request from './request'

async function downloadBlob(url: string, filename: string, method: 'GET' | 'POST' = 'GET', body?: any) {
  try {
    const resp = method === 'GET'
      ? await request.get(url, { responseType: 'blob' })
      : await request.post(url, body, { responseType: 'blob' })
    const blob = resp instanceof Blob ? resp : new Blob([JSON.stringify(resp)], { type: 'application/octet-stream' })
    const objectUrl = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = objectUrl
    a.download = filename
    a.click()
    URL.revokeObjectURL(objectUrl)
  } catch {
    ElMessage.error('导出失败')
  }
}

export function exportMarkdown(contentId: string) {
  return downloadBlob(`/contents/${contentId}/export/markdown`, `content_${contentId.slice(0, 8)}.md`)
}

export function exportZip(contentIds: string[]) {
  return downloadBlob('/export/zip', 'contents.zip', 'POST', contentIds)
}
