import { defineStore } from 'pinia'
import { ref } from 'vue'
import { listWorkspaces, getWorkspace } from '@/api/workspaces'

export interface Workspace {
  id: string
  name: string
  description: string | null
  owner_id: string
  created_at: string
}

export const useWorkspaceStore = defineStore('workspace', () => {
  const workspaces = ref<Workspace[]>([])
  const currentWorkspace = ref<Workspace | null>(null)

  async function fetchWorkspaces() {
    const data: any = await listWorkspaces()
    workspaces.value = data
    if (!currentWorkspace.value && data.length > 0) {
      currentWorkspace.value = data[0]
    }
  }

  async function switchWorkspace(id: string) {
    const data: any = await getWorkspace(id)
    currentWorkspace.value = data
  }

  return { workspaces, currentWorkspace, fetchWorkspaces, switchWorkspace }
})
