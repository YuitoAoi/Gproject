export interface TaskItem {
  id: string
  name: string
  type: 'training' | 'cleaning' | 'export' | 'inference' | 'upload'
  typeLabel: string
  status: 'running' | 'pending' | 'done' | 'failed'
  statusLabel: string
  elapsedTime: string
  progress: number
  gpuCount: number
  createdAt: string
}

export interface TaskDetail {
  id: string
  name: string
  status: 'running' | 'pending' | 'done' | 'failed'
  progress: number
  currentStep: number
  totalSteps: number
  elapsedTime: string
  baseModel: string
  trainStage: string
  finetuneAlgorithm: string
  batchSize: number
  gradAccumulation: number
  learningRate: string
  lrScheduler: string
  gpuCount: number
  memoryUsage: string
  loss: number
  evalLoss: number
  learningRateValue: string
  throughput: string
}

export interface CheckpointItem {
  name: string
  step: number
  evalLoss: number
  isBest: boolean
}

export const TASK_STATUS_CONFIG = {
  running: { color: '#409EFF', label: '运行中', dot: '#409EFF', icon: 'ri:play-circle-line' },
  pending: { color: '#E6A23C', label: '排队等待', dot: '#E6A23C', icon: 'ri:time-line' },
  done: { color: '#67C23A', label: '已完成', dot: '#67C23A', icon: 'ri:check-line' },
  failed: { color: '#909399', label: '失败', dot: '#909399', icon: 'ri:close-line' }
} as const

export const TASK_TYPE_CONFIG = {
  upload: { label: '文件上传', icon: 'ri:upload-2-line', color: '#909399' },
  training: { label: '指令微调', icon: 'ri:brain-line', color: '#409EFF' },
  cleaning: { label: '数据清洗', icon: 'ri:brush-3-line', color: '#67C23A' },
  export: { label: '格式导出', icon: 'ri:download-2-line', color: '#E6A23C' },
  inference: { label: '模型推理', icon: 'ri:message-3-line', color: '#9B59B6' }
} as const

export const taskDashboardMockData = {
  running: 4,
  pending: 12,
  done: 15,
  failed: 2,
  avgWaitTime: '2.5 小时',
  successRate: '92.5%',
  totalGpu: 32,
  allocatedGpu: 24
}

export const taskListMockData: TaskItem[] = [
  {
    id: 'TR-0042',
    name: '医疗_SFT_v3',
    type: 'training',
    typeLabel: '指令微调',
    status: 'running',
    statusLabel: '运行中',
    elapsedTime: '2h30m',
    progress: 37,
    gpuCount: 4,
    createdAt: '2026-05-07 14:30:00'
  },
  {
    id: 'TR-0045',
    name: '法律_SFT_v1',
    type: 'training',
    typeLabel: '指令微调',
    status: 'pending',
    statusLabel: '排队等待',
    elapsedTime: '12h00m',
    progress: 0,
    gpuCount: 8,
    createdAt: '2026-05-07 08:00:00'
  },
  {
    id: 'CL-0891',
    name: '维基去重',
    type: 'cleaning',
    typeLabel: '数据清洗',
    status: 'done',
    statusLabel: '已完成',
    elapsedTime: '00h45m',
    progress: 100,
    gpuCount: 2,
    createdAt: '2026-05-06 16:00:00'
  },
  {
    id: 'EX-0012',
    name: '模型导出v2',
    type: 'export',
    typeLabel: '格式导出',
    status: 'failed',
    statusLabel: '失败',
    elapsedTime: '异常终止',
    progress: 0,
    gpuCount: 1,
    createdAt: '2026-05-06 10:00:00'
  },
  {
    id: 'TR-0041',
    name: '金融_SFT_v2',
    type: 'training',
    typeLabel: '指令微调',
    status: 'running',
    statusLabel: '运行中',
    elapsedTime: '5h15m',
    progress: 68,
    gpuCount: 4,
    createdAt: '2026-05-07 10:00:00'
  },
  {
    id: 'CL-0892',
    name: '新闻去重',
    type: 'cleaning',
    typeLabel: '数据清洗',
    status: 'done',
    statusLabel: '已完成',
    elapsedTime: '01h20m',
    progress: 100,
    gpuCount: 2,
    createdAt: '2026-05-06 18:00:00'
  },
  {
    id: 'TR-0046',
    name: '教育_SFT_v1',
    type: 'training',
    typeLabel: '指令微调',
    status: 'pending',
    statusLabel: '排队等待',
    elapsedTime: '8h30m',
    progress: 0,
    gpuCount: 8,
    createdAt: '2026-05-07 06:00:00'
  },
  {
    id: 'EX-0013',
    name: 'Qwen量化导出',
    type: 'export',
    typeLabel: '格式导出',
    status: 'done',
    statusLabel: '已完成',
    elapsedTime: '00h30m',
    progress: 100,
    gpuCount: 1,
    createdAt: '2026-05-05 14:00:00'
  },
  {
    id: 'TR-0043',
    name: '代码_SFT_v1',
    type: 'training',
    typeLabel: '指令微调',
    status: 'running',
    statusLabel: '运行中',
    elapsedTime: '1h45m',
    progress: 25,
    gpuCount: 4,
    createdAt: '2026-05-07 12:30:00'
  },
  {
    id: 'CL-0893',
    name: '小说清洗',
    type: 'cleaning',
    typeLabel: '数据清洗',
    status: 'running',
    statusLabel: '运行中',
    elapsedTime: '0h35m',
    progress: 45,
    gpuCount: 2,
    createdAt: '2026-05-07 13:00:00'
  }
]

export const taskDetailMockData: TaskDetail = {
  id: 'TR-0042',
  name: '医疗问答_SFT_v3',
  status: 'running',
  progress: 37,
  currentStep: 4500,
  totalSteps: 12000,
  elapsedTime: '05h20m',
  baseModel: 'Qwen-14B-Chat-Int8',
  trainStage: 'Supervised Fine-Tuning (SFT)',
  finetuneAlgorithm: 'LoRA (Rank=16, Alpha=32)',
  batchSize: 4,
  gradAccumulation: 8,
  learningRate: '2e-5',
  lrScheduler: 'Cosine Annealing',
  gpuCount: 4,
  memoryUsage: '34GB',
  loss: 0.82,
  evalLoss: 0.78,
  learningRateValue: '2e-5',
  throughput: '8.5 t/s'
}

export const checkpointListMockData: CheckpointItem[] = [
  { name: 'checkpoint-2000', step: 2000, evalLoss: 0.98, isBest: false },
  { name: 'checkpoint-3000', step: 3000, evalLoss: 0.82, isBest: true },
  { name: 'checkpoint-4000', step: 4000, evalLoss: 0.84, isBest: false }
]

export const terminalLogsMockData = [
  '[14:20:00] [INFO] Task ID: cln_9fa82b started.',
  '[14:20:01] [INFO] Loading dataset from S3...',
  '[14:20:05] [WARN] Chunk 1: Dropped 452 empty rows.',
  '[14:20:12] [INFO] PII Masker: Masked 1,204 phones.',
  '[14:21:03] [WARN] Chunk 2: Dropped 89 short texts.',
  '[14:21:30] [INFO] MinHash Dedup: Scanning...',
  '[14:22:15] [INFO] Chunk 3 processing...'
]

export const lossChartMockData = [
  { step: 0, trainLoss: 1.8, evalLoss: 1.6 },
  { step: 500, trainLoss: 1.5, evalLoss: 1.4 },
  { step: 1000, trainLoss: 1.3, evalLoss: 1.2 },
  { step: 1500, trainLoss: 1.2, evalLoss: 1.1 },
  { step: 2000, trainLoss: 1.1, evalLoss: 0.98 },
  { step: 2500, trainLoss: 1.0, evalLoss: 0.92 },
  { step: 3000, trainLoss: 0.95, evalLoss: 0.82 },
  { step: 3500, trainLoss: 0.9, evalLoss: 0.85 },
  { step: 4000, trainLoss: 0.87, evalLoss: 0.84 },
  { step: 4500, trainLoss: 0.82, evalLoss: 0.78 }
]
