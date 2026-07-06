// Shared API response types

export interface ApiResponse<T> {
  code: number
  data: T
}

export interface PaginatedResponse<T> {
  items: T[]
  total: number
  page: number
  page_size: number
}

export interface ContentItem {
  id: string
  workspace_id: string
  prompt_id: string
  model_id: string
  generated_text: string
  edited_text?: string
  status: string
  token_usage?: number
  generation_time_ms?: number
  created_at: string
  updated_at?: string
  variables_used?: Record<string, string>
}

export interface PromptItem {
  id: string
  workspace_id: string
  title: string
  content: string
  category: string
  tags: string[]
  variables?: { name: string; required?: boolean }[]
  version: number
  is_favorite: boolean
  created_at: string
}

export interface PromptVersionItem {
  id: string
  prompt_id: string
  version: number
  content: string
  created_at: string
}

export interface ModelItem {
  id: string
  workspace_id: string
  name: string
  provider: string
  model_name: string
  base_url?: string
  is_active: boolean
  default_params?: Record<string, number>
  created_at: string
}

export interface MemberItem {
  user_id: string
  username: string
  email: string
  role: string
}

export interface WorkspaceItem {
  id: string
  name: string
  description?: string
  created_at: string
}

export interface ReviewItem extends ContentItem {
  review_comment?: string
}

export interface DashboardStats {
  prompt_count: number
  content_count: number
  monthly_generated: number
  pending_review: number
}

export interface TrendItem {
  date: string
  count: number
}

export interface ModelUsageItem {
  name: string
  count: number
}

export interface UserRankingItem {
  username: string
  count: number
}
