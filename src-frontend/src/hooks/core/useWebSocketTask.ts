/**
 * WebSocket 任务进度连接 Hook
 *
 * 连接到后端 WebSocket 端点，实时接收任务进度推送
 * 自动更新 Pinia 中对应的任务状态
 *
 * 使用方式:
 *   const { connect, disconnect, connected } = useWebSocketTask(jobId)
 */
import { ref, onMounted, onUnmounted } from 'vue'
import { ElNotification } from 'element-plus'
import { useTaskStore } from '@/store/modules/task'
import { store } from '@/store'

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

export function useWebSocketTask(jobId: string) {
  const taskStore = useTaskStore(store)
  const ws = ref<WebSocket | null>(null)
  const connected = ref(false)
  const retryCount = ref(0)
  const maxRetries = 5
  const retryDelay = 3000
  let reconnectTimer: ReturnType<typeof setTimeout> | null = null

  const handleMessage = (event: MessageEvent) => {
    try {
      const data = JSON.parse(event.data)

      if (data.type === 'heartbeat') return
      if (data.type === 'pong') return
      if (data.type === 'connected') {
        console.log('[WS] 已连接:', data.message)
        return
      }

      const status = data.status
      const progress = (data.progress ?? 0) * 100
      const stage = data.stage || status
      const message = data.message || ''

      taskStore.updateTask(jobId, {
        current: Math.round(progress),
        total: 100,
        percentage: progress,
        phase: stage,
        status: status === 'done' ? 'success'
          : status === 'failed' || status === 'cancelled' ? 'failure'
          : 'running',
        message,
      })

      if (status === 'done') {
        ElNotification.success({
          title: '任务完成',
          message: message || `任务 ${jobId} 已完成`,
        })
      } else if (status === 'failed') {
        ElNotification.error({
          title: '任务失败',
          message: message || `任务 ${jobId} 执行失败`,
        })
      }
    } catch (e) {
      console.error('[WS] 消息解析失败:', e, event.data)
    }
  }

  const handleOpen = () => {
    connected.value = true
    retryCount.value = 0
    console.log('[WS] WebSocket连接已建立:', jobId)
  }

  const handleClose = (event: CloseEvent) => {
    connected.value = false
    console.log('[WS] WebSocket连接已关闭:', jobId, event.code, event.reason)

    if (retryCount.value < maxRetries && event.code !== 1000) {
      retryCount.value++
      console.log(`[WS] ${retryCount.value}/${maxRetries} 重连中...`)
      reconnectTimer = setTimeout(connect, retryDelay * retryCount.value)
    }
  }

  const handleError = (error: Event) => {
    console.error('[WS] WebSocket错误:', jobId, error)
  }

  const connect = () => {
    if (ws.value) {
      ws.value.close()
      ws.value = null
    }

    const url = `${WS_BASE}${WS_PATH}?job_id=${jobId}`
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
  }

  const send = (data: any) => {
    if (ws.value && ws.value.readyState === WebSocket.OPEN) {
      ws.value.send(typeof data === 'string' ? data : JSON.stringify(data))
    }
  }

  onMounted(() => {
    connect()
  })

  onUnmounted(() => {
    disconnect()
  })

  return {
    ws,
    connected,
    connect,
    disconnect,
    send,
  }
}
