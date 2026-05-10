import request from '@/utils/http'

export interface TaskItem {
  id: number
  task_name: string
  task_type: string
  status: string
  progress: number
  phase: string
  config: string
  created_at: string
  updated_at: string
}

export interface TaskListResponse {
  items: TaskItem[]
  total: number
  error?: string
}

export interface TaskDetailResponse {
  task?: TaskItem
  error?: string
}

export async function getTasks(params?: { status?: string }): Promise<TaskListResponse> {
  try {
    return await request.get<TaskListResponse>({
      url: '/tasks',
      params: params || {}
    })
  } catch {
    return { items: [], total: 0, error: '请求失败' }
  }
}

export async function getTask(id: number): Promise<TaskDetailResponse> {
  try {
    return await request.get<TaskDetailResponse>({
      url: `/tasks/${id}`
    })
  } catch {
    return { error: '请求失败' }
  }
}

export async function deleteTask(id: number): Promise<{ success: boolean }> {
  try {
    return await request.del<{ success: boolean }>({
      url: `/tasks/${id}`
    })
  } catch {
    return { success: false }
  }
}
