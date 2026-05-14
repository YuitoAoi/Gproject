import request from '@/utils/http'

/** 服务健康状态项 */
export interface ServiceHealthItem {
  title: string
  status: string
  time: string
  class_: string
  icon: string
}

/** 存储水位信息 */
export interface StorageInfo {
  total_gb: number
  used_gb: number
  free_gb: number
  percentage: number
}

/** 任务简报项 */
export interface TaskBriefingItem {
  taskName: string
  phase: string
  progress: number
}

/** 审计追踪项 */
export interface AuditTrailItem {
  time: string
  status: string
  content: string
}

/** 每日完成任务统计 */
export interface DailyCountItem {
  date: string
  count: number
}

/** 仪表盘聚合响应 */
export interface DashboardResponse {
  active_task_count: number
  dataset_count: number
  finetuned_model_count: number
  compute_task_count: number
  service_health: ServiceHealthItem[]
  storage: StorageInfo | null
  daily_done: DailyCountItem[]
  task_briefing: TaskBriefingItem[]
  audit_trail: AuditTrailItem[]
  error?: string
}

/** 获取仪表盘聚合数据 */
export async function getDashboard(): Promise<DashboardResponse> {
  try {
    return await request.get<DashboardResponse>({ url: '/dashboard' })
  } catch {
    return {
      active_task_count: 0,
      dataset_count: 0,
      finetuned_model_count: 0,
      compute_task_count: 0,
      service_health: [],
      storage: null,
      daily_done: [],
      task_briefing: [],
      audit_trail: [],
      error: '请求失败',
    }
  }
}
