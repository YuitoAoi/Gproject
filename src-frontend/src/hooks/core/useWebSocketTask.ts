/**
 * WebSocket 任务进度连接 Hook
 *
 * 连接到后端WebSocket端点，实时接收Celery任务进度推送
 * 自动更新Pinia中对应的任务状态
 *
 * 使用方式:
 *   const { connect, disconnect, connected } = useWebSocketTask(taskId)
 */
import { ref, onMounted, onUnmounted, watch } from 'vue'
import { ElNotification } from 'element-plus'
import { useTaskStore } from '@/store/modules/task'
import { store } from '@/store'

const WS_BASE = import.meta.env.VITE_WS_URL || 'ws://localhost:8000'
const WS_URL = `${WS_BASE}/ws/progress`

export function useWebSocketTask(taskId: string) {
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

      // 任务进度更新
      if (data.task_id) {
        taskStore.updateTask(taskId, {
          current: data.current,
          total: data.total,
          percentage: data.percentage,
          phase: data.phase,
          status: data.status,
          message: data.message || ''
        })

        // 任务完成/失败通知
        if (data.status === 'success') {
          ElNotification.success({
            title: '任务完成',
            message: data.message || `任务 ${taskId} 已完成`
          })
        } else if (data.status === 'failure') {
          ElNotification.error({
            title: '任务失败',
            message: data.message || `任务 ${taskId} 执行失败`
          })
        }
      }
    } catch (e) {
      console.error('[WS] 消息解析失败:', e, event.data)
    }
  }

  const handleOpen = () => {
    connected.value = true
    retryCount.value = 0
    console.log('[WS] WebSocket连接已建立:', taskId)
  }

  const handleClose = (event: CloseEvent) => {
    connected.value = false
    console.log('[WS] WebSocket连接已关闭:', taskId, event.code, event.reason)

    // 自动重连
    if (retryCount.value < maxRetries && event.code !== 1000) {
      retryCount.value++
      console.log(`[WS] ${retryCount.value}/${maxRetries} 重连中...`)
      reconnectTimer = setTimeout(connect, retryDelay * retryCount.value)
    }
  }

  const handleError = (error: Event) => {
    console.error('[WS] WebSocket错误:', taskId, error)
  }

  const connect = () => {
    if (ws.value) {
      ws.value.close()
      ws.value = null
    }

    const url = `${WS_URL}?task_id=${taskId}`
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

  // 发送消息到服务端
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
    send
  }
}
