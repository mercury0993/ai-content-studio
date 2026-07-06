import request from './request'
import type { WorkspaceItem, MemberItem } from './types'

export function listWorkspaces() {
  return request.get<WorkspaceItem[]>('/workspaces')
}

export function createWorkspace(data: { name: string; description?: string }) {
  return request.post<WorkspaceItem>('/workspaces', data)
}

export function getWorkspace(id: string) {
  return request.get<WorkspaceItem>(`/workspaces/${id}`)
}

export function updateWorkspace(id: string, data: { name?: string; description?: string }) {
  return request.put<WorkspaceItem>(`/workspaces/${id}`, data)
}

export function deleteWorkspace(id: string) {
  return request.delete(`/workspaces/${id}`)
}

export function listMembers(workspaceId: string) {
  return request.get<MemberItem[]>(`/workspaces/${workspaceId}/members`)
}

export function addMember(workspaceId: string, data: { user_id: string; role: string }) {
  return request.post(`/workspaces/${workspaceId}/members`, data)
}

export function removeMember(workspaceId: string, userId: string) {
  return request.delete(`/workspaces/${workspaceId}/members/${userId}`)
}
