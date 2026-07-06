type TagType = 'primary' | 'success' | 'warning' | 'danger' | 'info' | ''

export const statusMap: Record<string, { label: string; type: TagType }> = {
  draft: { label: '草稿', type: 'info' },
  pending_review: { label: '待审核', type: 'warning' },
  approved: { label: '已通过', type: 'success' },
  rejected: { label: '已驳回', type: 'danger' },
}

export function truncate(text: string, len: number): string {
  if (!text) return ''
  return text.length > len ? text.slice(0, len) + '...' : text
}

export function formatDate(iso: string): string {
  return new Date(iso).toLocaleString()
}

export const promptCategories = [
  { label: '营销文案', value: 'marketing' },
  { label: '技术文档', value: 'tech_doc' },
  { label: '社交媒体', value: 'social_media' },
]
