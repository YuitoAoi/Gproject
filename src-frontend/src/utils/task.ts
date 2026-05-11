export type TaskStatus = 'pending' | 'running' | 'done' | 'failed' | 'cancelled'

export const TASK_STATUS_LABEL: Record<TaskStatus, string> = {
  pending: '排队中',
  running: '运行中',
  done: '已完成',
  failed: '失败',
  cancelled: '已取消'
}

export const TASK_STATUS_TAG_TYPE: Record<TaskStatus, string> = {
  pending: 'info',
  running: 'primary',
  done: 'success',
  failed: 'danger',
  cancelled: 'info'
}

export function mapTaskStatusForDisplay(raw: string): TaskStatus {
  switch (raw) {
    case 'running':
      return 'running'
    case 'done':
      return 'done'
    case 'failed':
      return 'failed'
    case 'cancelled':
      return 'cancelled'
    default:
      return 'pending'
  }
}

export type TaskType = 'upload' | 'cleaning' | 'training' | 'inference' | 'export'

export const TASK_TYPE_LABEL: Record<TaskType, string> = {
  upload: '文件上传',
  cleaning: '数据清洗',
  training: '模型训练',
  inference: '模型推理',
  export: '格式导出'
}
