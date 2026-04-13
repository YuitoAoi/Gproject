import { ElNotification } from 'element-plus'

type MessageHandler = (data: any) => void

class WebSocketManager {
  private ws: WebSocket | null = null
  private url: string = ''
  private reconnectInterval: number = 5000
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private listeners: Map<string, Set<MessageHandler>> = new Map()
  private isConnecting: boolean = false

  connect(url?: string): void {
    if (this.ws?.readyState === WebSocket.OPEN || this.isConnecting) {
      return
    }

    this.url = url || this.getWebSocketUrl()
    this.isConnecting = true

    try {
      this.ws = new WebSocket(this.url)

      this.ws.onopen = () => {
        this.isConnecting = false
        console.log('[WebSocket] Connected to', this.url)
        this.startHeartbeat()
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          this.dispatch(data.type || 'message', data)
        } catch {
          this.dispatch('message', event.data)
        }
      }

      this.ws.onerror = (error) => {
        console.error('[WebSocket] Error:', error)
      }

      this.ws.onclose = () => {
        this.isConnecting = false
        console.log('[WebSocket] Connection closed')
        this.scheduleReconnect()
      }
    } catch (error) {
      this.isConnecting = false
      console.error('[WebSocket] Connection failed:', error)
      this.scheduleReconnect()
    }
  }

  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  on(event: string, handler: MessageHandler): void {
    if (!this.listeners.has(event)) {
      this.listeners.set(event, new Set())
    }
    this.listeners.get(event)!.add(handler)
  }

  off(event: string, handler: MessageHandler): void {
    this.listeners.get(event)?.delete(handler)
  }

  send(data: any): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    }
  }

  private dispatch(event: string, data: any): void {
    this.listeners.get(event)?.forEach(handler => handler(data))
    this.listeners.get('*')?.forEach(handler => handler({ event, ...data }))
  }

  private scheduleReconnect(): void {
    if (this.reconnectTimer) return
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null
      this.connect()
    }, this.reconnectInterval)
  }

  private startHeartbeat(): void {
    setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.send({ type: 'ping' })
      }
    }, 30000)
  }

  private getWebSocketUrl(): string {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const host = import.meta.env.VITE_WS_URL || window.location.host
    return `${protocol}//${host}/ws`
  }

  get isConnected(): boolean {
    return this.ws?.readyState === WebSocket.OPEN
  }
}

const websocketManager = new WebSocketManager()

export const connectWebSocket = () => websocketManager.connect()
export const disconnectWebSocket = () => websocketManager.disconnect()
export const onWebSocketMessage = (event: string, handler: MessageHandler) => websocketManager.on(event, handler)
export const offWebSocketMessage = (event: string, handler: MessageHandler) => websocketManager.off(event, handler)
export const sendWebSocketMessage = (data: any) => websocketManager.send(data)

websocketManager.on('system-notification', (data) => {
  ElNotification({
    title: data.title || '系统通知',
    message: data.message || '',
    type: data.type || 'info',
    duration: 5000
  })
})

websocketManager.on('model-activated', (data) => {
  ElNotification({
    title: '模型已激活',
    message: `模型 "${data.model_name}" 已准备就绪`,
    type: 'success',
    duration: 5000
  })
})

websocketManager.on('model-deactivated', (data) => {
  ElNotification({
    title: '模型已停用',
    message: `模型 "${data.model_name}" 已从GPU卸载`,
    type: 'info',
    duration: 3000
  })
})

export default websocketManager
