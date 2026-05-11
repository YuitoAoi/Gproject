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
  page?: number
  page_size?: number
  error?: string
}

export interface TaskDetailResponse {
  task?: TaskItem
  error?: string
}

export interface TaskCreateRequest {
  task_name: string
  task_type?: 'upload' | 'cleaning' | 'training' | 'inference' | 'export'
  config?: string
}

export interface TaskUpdateRequest {
  status?: 'pending' | 'running' | 'done' | 'failed' | 'cancelled'
  progress?: number
  phase?: string
}

export async function getTasks(params?: {
  status?: string
  page?: number
  page_size?: number
}): Promise<TaskListResponse> {
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

export async function createTask(data: TaskCreateRequest): Promise<TaskDetailResponse> {
  try {
    return await request.post<TaskDetailResponse>({
      url: '/tasks',
      data
    })
  } catch {
    return { error: '请求失败' }
  }
}

export async function updateTask(id: number, data: TaskUpdateRequest): Promise<TaskDetailResponse> {
  try {
    return await request.patch<TaskDetailResponse>({
      url: `/tasks/${id}`,
      data
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
