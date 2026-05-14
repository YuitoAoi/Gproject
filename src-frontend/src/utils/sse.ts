/**
 * SSE 流式对话工具
 * 基于 fetch + ReadableStream 消费 SSE 格式的流式响应
 */
import { useUserStore } from '@/store/modules/user'

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant'
  content: string
}

export interface ChatStreamOptions {
  temperature?: number
  maxTokens?: number
}

/**
 * SSE 流式对话 async generator
 * @param model   模型 ID
 * @param messages  对话消息历史
 * @param options   可选参数
 */
export async function* streamChat(
  model: string,
  messages: ChatMessage[],
  options?: ChatStreamOptions,
): AsyncGenerator<string, void, unknown> {
  const { VITE_API_URL } = import.meta.env
  const { accessToken } = useUserStore()

  const payload: Record<string, unknown> = {
    model,
    messages,
  }
  if (options?.temperature !== undefined) payload.temperature = options.temperature
  if (options?.maxTokens !== undefined) payload.max_tokens = options.maxTokens

  const resp = await fetch(`${VITE_API_URL}/llamafactory/chat/stream`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      Authorization: `Bearer ${accessToken}`,
    },
    body: JSON.stringify(payload),
  })

  if (!resp.ok) {
    throw new Error(`请求失败: ${resp.status} ${resp.statusText}`)
  }

  const reader = resp.body!.getReader()
  const decoder = new TextDecoder()

  let buffer = ''
  try {
    while (true) {
      const { done, value } = await reader.read()
      if (done) break

      buffer += decoder.decode(value, { stream: true })
      const lines = buffer.split('\n')
      buffer = lines.pop() ?? ''

      for (const rawLine of lines) {
        const line = rawLine.trim()
        if (!line.startsWith('data: ')) continue
        const data = line.slice(6).trim()
        if (data === '[DONE]') return
        try {
          const parsed = JSON.parse(data)
          const content = parsed?.choices?.[0]?.delta?.content
          if (content) yield content
        } catch {
          // ignore malformed JSON lines
        }
      }
    }
  } finally {
    reader.releaseLock()
  }
}