import request from './request'

export function listReviews(params: {
  workspace_id: string
  status?: string
  page?: number
  page_size?: number
}) {
  return request.get('/reviews', { params })
}

export function submitForReview(contentId: string, reviewerId?: string) {
  return request.post(`/reviews/${contentId}/submit`, reviewerId ? { reviewer_id: reviewerId } : {})
}

export function approveContent(contentId: string, comment?: string) {
  return request.post(`/reviews/${contentId}/approve`, { comment })
}

export function rejectContent(contentId: string, comment: string) {
  return request.post(`/reviews/${contentId}/reject`, { comment })
}

export function batchReview(contentIds: string[], action: string, comment?: string) {
  return request.post('/reviews/batch', { content_ids: contentIds, action, comment })
}
