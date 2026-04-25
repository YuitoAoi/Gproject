type MessageHandler = (data: unknown) => void

class WebSocketClient {
  private ws: WebSocket | null = null
  private url: string = ''
  private reconnectInterval: number = 5000
  private heartbeatInterval: number = 30000
  private reconnectTimer: ReturnType<typeof setTimeout> | null = null
  private heartbeatTimer: ReturnType<typeof setInterval> | null = null
  private listeners: Map<string, Set<MessageHandler>> = new Map()
  private reconnectAttempts: number = 0
  private maxReconnectAttempts: number = 10

  connect(url: string): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      console.log('[WebSocket] Already connected')
      return
    }

    this.url = url
    console.log('[WebSocket] Connecting to', url)

    try {
      this.ws = new WebSocket(url)

      this.ws.onopen = () => {
        console.log('[WebSocket] Connected to', url)
        this.reconnectAttempts = 0
        this.startHeartbeat()
        this.dispatch('open', null)
      }

      this.ws.onmessage = (event) => {
        try {
          const data = JSON.parse(event.data)
          this.dispatch('message', data)
        } catch {
          this.dispatch('message', event.data)
        }
      }

      this.ws.onerror = (error) => {
        console.error('[WebSocket] Error:', error)
        this.dispatch('error', error)
      }

      this.ws.onclose = () => {
        console.log('[WebSocket] Disconnected')
        this.stopHeartbeat()
        this.scheduleReconnect()
        this.dispatch('close', null)
      }
    } catch (error) {
      console.error('[WebSocket] Connection error:', error)
      this.scheduleReconnect()
    }
  }

  disconnect(): void {
    if (this.reconnectTimer) {
      clearTimeout(this.reconnectTimer)
      this.reconnectTimer = null
    }
    this.stopHeartbeat()
    if (this.ws) {
      this.ws.close()
      this.ws = null
    }
  }

  send(data: unknown): void {
    if (this.ws?.readyState === WebSocket.OPEN) {
      this.ws.send(JSON.stringify(data))
    } else {
      console.warn('[WebSocket] Cannot send, not connected')
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

  private dispatch(event: string, data: unknown): void {
    this.listeners.get(event)?.forEach((handler) => handler(data))
    this.listeners.get('*')?.forEach((handler) => handler({ event, data }))
  }

  private scheduleReconnect(): void {
    if (this.reconnectAttempts >= this.maxReconnectAttempts) {
      console.log('[WebSocket] Max reconnect attempts reached')
      return
    }

    if (this.reconnectTimer) {
      return
    }

    console.log('[WebSocket] Scheduling reconnect in', this.reconnectInterval, 'ms')
    this.reconnectTimer = setTimeout(() => {
      this.reconnectTimer = null
      this.reconnectAttempts++
      console.log('[WebSocket] Reconnecting, attempt', this.reconnectAttempts)
      this.connect(this.url)
    }, this.reconnectInterval)
  }

  private startHeartbeat(): void {
    this.heartbeatTimer = setInterval(() => {
      if (this.ws?.readyState === WebSocket.OPEN) {
        this.send({ type: 'ping' })
      }
    }, this.heartbeatInterval)
  }

  private stopHeartbeat(): void {
    if (this.heartbeatTimer) {
      clearInterval(this.heartbeatTimer)
      this.heartbeatTimer = null
    }
  }
}

export const wsClient = new WebSocketClient()
export default wsClient
