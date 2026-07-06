import request from './request'
import type { WorkspaceItem, MemberItem } from './types'

export function listWorkspaces(): Promise<WorkspaceItem[]> {
  return request.get('/workspaces')
}

export function createWorkspace(data: { name: string; description?: string }): Promise<WorkspaceItem> {
  return request.post('/workspaces', data)
}

export function getWorkspace(id: string): Promise<WorkspaceItem> {
  return request.get(`/workspaces/${id}`)
}

export function updateWorkspace(id: string, data: { name?: string; description?: string }): Promise<WorkspaceItem> {
  return request.put(`/workspaces/${id}`, data)
}

export function deleteWorkspace(id: string): Promise<void> {
  return request.delete(`/workspaces/${id}`)
}

export function listMembers(workspaceId: string): Promise<MemberItem[]> {
  return request.get(`/workspaces/${workspaceId}/members`)
}

export function addMember(workspaceId: string, data: { user_id: string; role: string }): Promise<MemberItem> {
  return request.post(`/workspaces/${workspaceId}/members`, data)
}

export function removeMember(workspaceId: string, userId: string): Promise<void> {
  return request.delete(`/workspaces/${workspaceId}/members/${userId}`)
}
