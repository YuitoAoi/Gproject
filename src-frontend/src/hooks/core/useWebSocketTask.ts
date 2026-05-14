/**
 * WebSocket 任务进度连接 Hook
 *
 * 连接到后端 WebSocket 端点，实时接收任务进度推送
 * 自动更新 Pinia 中对应的任务状态
 *
 * 使用方式:
 *   const { connect, disconnect, connected } = useWebSocketTask(jobId)
 */
import { ref, watch } from 'vue'
import { ElMessage, ElNotification } from 'element-plus'
import { useTaskStore } from '@/store/modules/task'
import { mapTaskStatusForDisplay } from '@/utils/task'
import { store } from '@/store'

export interface TrainingProgress {
  status: 'running' | 'done' | 'failed' | 'pending'
  progress: number
  stage: string
  message: string
  current_step?: number
  total_steps?: number
  loss?: number | null
  eval_loss?: number | null
  learning_rate?: number | null
  epoch?: number | null
  gpu?: Array<{
    used_memory_mb?: number
    total_memory_mb?: number
    temperature?: number
  }>
  type?: string
}

function resolveWsBase(): string {
  const env = import.meta.env.VITE_WS_URL
  if (env) return env
  const api = import.meta.env.VITE_API_URL
  if (typeof api === 'string' && api.startsWith('http')) {
    return api.replace(/^http/, 'ws')
  }
  return 'ws://localhost:8088'
}

const WS_BASE = resolveWsBase()
const WS_PATH = '/ws/progress'

export function useWebSocketTask(initialJobId: string = '') {
  const taskStore = useTaskStore(store)
  const ws = ref<WebSocket | null>(null)
  const connected = ref(false)
  const retryCount = ref(0)
  const maxRetries = 5
  const retryDelay = 3000
  const jobId = ref(initialJobId)
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null
  let currentJobId = initialJobId

  // 训练进度实时数据，供监控页直接消费
  const trainingProgress = ref<TrainingProgress | null>(null)
  const lossHistory = ref<Array<{ step: number; trainLoss: number; evalLoss: number }>>([])

  watch(jobId, (newVal) => {
    currentJobId = newVal
  })

  const handleMessage = (event: MessageEvent) => {
    try {
      const data: TrainingProgress = JSON.parse(event.data)

      if (data.type === 'heartbeat') return
      if (data.type === 'pong') return
      if (data.type === 'connected') {
        console.log('[WS] 已连接:', data.message)
        return
      }

      const status = data.status
      const progress = data.progress ?? 0
      const stage = data.stage || status
      const message = data.message || ''

      // 更新 Pinia store
      taskStore.updateTask(currentJobId, {
        current: Math.round(progress * 100),
        total: 100,
        percentage: progress * 100,
        phase: stage,
        status: mapTaskStatusForDisplay(status),
        message
      })

      // 累积训练进度数据
      trainingProgress.value = data

      // 累积 loss 历史
      if (status === 'running' && data.current_step !== undefined) {
        const entry = {
          step: data.current_step,
          trainLoss: data.loss ?? 0,
          evalLoss: data.eval_loss ?? 0
        }
        // 避免重复 step
        if (!lossHistory.value.find(l => l.step === entry.step)) {
          lossHistory.value = [...lossHistory.value, entry].sort((a, b) => a.step - b.step)
        }
      }

      if (status === 'done') {
        ElNotification.success({
          title: '训练完成',
          message: message || `训练任务已完成`
        })
      } else if (status === 'failed') {
        ElNotification.error({
          title: '训练失败',
          message: message || `训练任务执行失败`
        })
      }
    } catch (e) {
      console.error('[WS] 消息解析失败:', e, event.data)
    }
  }

  const handleOpen = () => {
    connected.value = true
    retryCount.value = 0
    console.log('[WS] WebSocket连接已建立:', currentJobId)
  }

  const handleClose = (event: CloseEvent) => {
    connected.value = false
    console.log('[WS] WebSocket连接已关闭:', currentJobId, event.code, event.reason)

    if (retryCount.value < maxRetries && event.code !== 1000) {
      retryCount.value++
      console.log(`[WS] ${retryCount.value}/${maxRetries} 重连中...`)
      reconnectTimer = setTimeout(connect, retryDelay * retryCount.value)
    } else if (retryCount.value >= maxRetries) {
      ElMessage.warning('实时连接已断开，请刷新页面重试')
    }
  }

  const handleError = (error: Event) => {
    console.error('[WS] WebSocket错误:', currentJobId, error)
  }

  const connect = () => {
    if (!currentJobId) return
    if (ws.value) {
      ws.value.close()
      ws.value = null
    }

    const url = `${WS_BASE}${WS_PATH}?job_id=${currentJobId}`
    ws.value = new WebSocket(url)

    ws.value.onopen = handleOpen
    ws.value.onmessage = handleMessage
    ws.value.onclose = handleClose
    ws.value.onerror = handleError
  }

  const disconnect = () => {
    if (reconnectTimer) {
      clearTimeout(reconnectTimer)
      reconnectTimer = null
    }
    if (ws.value) {
      ws.value.close(1000, '主动断开')
      ws.value = null
    }
    connected.value = false
    trainingProgress.value = null
  }

  const send = (data: unknown) => {
    if (ws.value && ws.value.readyState === WebSocket.OPEN) {
      ws.value.send(typeof data === 'string' ? data : JSON.stringify(data))
    }
  }

  return {
    ws,
    connected,
    connect,
    disconnect,
    send,
    jobId,
    trainingProgress,
    lossHistory,
  }
}
