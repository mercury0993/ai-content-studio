import request from './request'

export function listWorkspaces() {
  return request.get('/workspaces')
}

export function createWorkspace(data: { name: string; description?: string }) {
  return request.post('/workspaces', data)
}

export function getWorkspace(id: string) {
  return request.get(`/workspaces/${id}`)
}

export function updateWorkspace(id: string, data: { name?: string; description?: string }) {
  return request.put(`/workspaces/${id}`, data)
}

export function deleteWorkspace(id: string) {
  return request.delete(`/workspaces/${id}`)
}

export function listMembers(workspaceId: string) {
  return request.get(`/workspaces/${workspaceId}/members`)
}

export function addMember(workspaceId: string, data: { user_id: string; role: string }) {
  return request.post(`/workspaces/${workspaceId}/members`, data)
}

export function removeMember(workspaceId: string, userId: string) {
  return request.delete(`/workspaces/${workspaceId}/members/${userId}`)
}
