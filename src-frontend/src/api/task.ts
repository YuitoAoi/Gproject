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

export interface CleaningSummaryResponse {
  raw_count: number
  final_count: number
  status: string
  current_stage: string
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

export async function getCleaningSummary(id: number): Promise<CleaningSummaryResponse> {
  try {
    return await request.get<CleaningSummaryResponse>({
      url: `/tasks/${id}/cleaning-summary`
    })
  } catch {
    return { error: '请求失败', raw_count: 0, final_count: 0, status: 'pending', current_stage: '' }
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

export interface TerminateResponse {
  success: boolean
  message?: string
}

export async function terminateTask(id: number): Promise<TerminateResponse> {
  try {
    return await request.post<TerminateResponse>({
      url: `/tasks/${id}/terminate`
    })
  } catch {
    return { success: false, message: '请求失败' }
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

export interface TrainingLogResponse {
  lines: string[]
  error?: string
}

export async function getTrainingExportLog(taskId: number): Promise<TrainingLogResponse> {
  try {
    return await request.get<TrainingLogResponse>({
      url: `/tasks/${taskId}/export-log`
    })
  } catch {
    return { lines: [], error: '请求失败' }
  }
}
