/**
 * 简单的事件总线
 * 用于跨组件通信（如打开全局搜索对话框）
 */
type Handler = (...args: any[]) => void

class EventBus {
  private events = new Map<string, Set<Handler>>()

  on(event: string, handler: Handler): void {
    if (!this.events.has(event)) {
      this.events.set(event, new Set())
    }
    this.events.get(event)!.add(handler)
  }

  off(event: string, handler: Handler): void {
    this.events.get(event)?.delete(handler)
  }

  emit(event: string, ...args: any[]): void {
    this.events.get(event)?.forEach((handler) => handler(...args))
  }
}

export const mittBus = new EventBus()
