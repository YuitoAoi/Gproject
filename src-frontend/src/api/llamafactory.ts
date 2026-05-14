import request from '@/utils/http'

/** ═══ 模型列表 ═══ */

export interface LlamaFactoryModelsResponse {
  success: boolean
  models: string[]
  error?: string
}

export async function getLlamaFactoryModels(): Promise<LlamaFactoryModelsResponse> {
  try {
    return await request.get<LlamaFactoryModelsResponse>({
      url: '/llamafactory/models'
    })
  } catch {
    return { success: false, models: [], error: '请求失败' }
  }
}

/** ═══ 对话 ═══ */

export interface ChatMessage {
  role: 'system' | 'user' | 'assistant'
  content: string
}

export interface LlamaFactoryChatRequest {
  model: string
  messages: ChatMessage[]
  temperature?: number
  max_tokens?: number
}

export interface LlamaFactoryChatResponse {
  success: boolean
  content?: string
  error?: string
}

export async function llamaFactoryChat(data: LlamaFactoryChatRequest): Promise<LlamaFactoryChatResponse> {
  try {
    return await request.post<LlamaFactoryChatResponse>({
      url: '/llamafactory/chat',
      data
    })
  } catch {
    return { success: false, error: '请求失败' }
  }
}

/** ═══ 微调产物列表 ═══ */

export interface FinetunedModelsResponse {
  success: boolean
  fine_tuned: string[]
  online: string[]
  error?: string
}

export async function getFinetunedModels(): Promise<FinetunedModelsResponse> {
  try {
    return await request.get<FinetunedModelsResponse>({
      url: '/llamafactory/finetuned-models'
    })
  } catch {
    return { success: false, fine_tuned: [], online: [], error: '请求失败' }
  }
}

/** ═══ 启动在线推理 ═══ */

export interface InferenceStartResponse {
  success: boolean
  error?: string
}

export async function startInference(modelId: string): Promise<InferenceStartResponse> {
  try {
    return await request.post<InferenceStartResponse>({
      url: '/llamafactory/inference/start',
      params: { model_id: modelId }
    })
  } catch {
    return { success: false, error: '请求失败' }
  }
}

/** ═══ 训练任务提交 ═══ */

export interface TrainingSubmitRequest {
  task_name: string
  base_model: string
  finetune_method: 'lora' | 'qlora' | 'full'
  dataset_id: number
  params: {
    epochs: number
    batch_size: number
    learning_rate: number
    max_seq_length: number
    lora_rank?: number
    lora_alpha?: number
    lora_dropout?: number
    lora_target?: string
    gradient_accumulation_steps?: number
    weight_decay?: number
    warmup_ratio?: number
    optimizer?: string
    scheduler?: string
    fp16?: boolean
    bf16?: boolean
    gradient_checkpointing?: boolean
  }
}

export interface TrainingSubmitResponse {
  success: boolean
  task_id?: number
  job_id?: string
  error?: string
}

export async function submitTraining(data: TrainingSubmitRequest): Promise<TrainingSubmitResponse> {
  try {
    return await request.post<TrainingSubmitResponse>({
      url: '/llamafactory/train',
      data
    })
  } catch {
    return { success: false, error: '请求失败' }
  }
}
