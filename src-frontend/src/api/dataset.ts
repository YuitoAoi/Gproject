import request from '@/utils/http'

export interface DatasetMeta {
  format: 'csv' | 'xlsx' | 'json'
  file_path: string
  file_size: number
  output_path?: string
}

export interface Dataset {
  id: number
  owner_id: number
  name: string
  desc: string | null
  meta: DatasetMeta
  status: number
  tag_ids: number[]
  created_at: string
  updated_at: string
}

export interface DatasetListResponse {
  items: DatasetItemDTO[]
  total: number
  error: string | null
}

export interface DatasetItemDTO {
  id: number
  name: string
  desc: string | null
  format: string
  file_size: number
  status: number
  tag_ids: number[]
  created_at: string
  updated_at: string
}

export interface TagInfo {
  tag_id: number
  tag_name: string
  tag_color: string
  tag_desc: string
  tag_created_at: string
}

export interface TagsGetResponse {
  success: boolean
  error: string | null
  tags: TagInfo[]
}

export interface UploadInitiateResponse {
  upload_id: string
  chunk_size: number
  total_chunks: number
  uploaded_chunks: number[]
  is_instant_complete: boolean
}

export interface UploadChunkResponse {
  upload_id: string
  chunk_index: number
  received: boolean
  error?: string
}

export interface UploadCompleteResponse {
  upload_id: string
  task_id: string
  dataset_id: number
  status: string
  message: string
}

export interface ProcessRequest {
  api_key: string
  synthesizer_url: string
  synthesizer_model: string
  mode:
    | 'atomic'
    | 'multi_hop'
    | 'aggregated'
    | 'CoT'
    | 'multi_choice'
    | 'multi_answer'
    | 'fill_in_blank'
    | 'true_false'
  data_format: 'Alpaca' | 'Sharegpt' | 'ChatML'
  content_field?: string
  tokenizer?: string
  chunk_size?: number
  chunk_overlap?: number
  quiz_samples?: number
  partition_method?: 'dfs' | 'bfs' | 'leiden' | 'ece'
  rpm?: number
  tpm?: number
}

export interface ProcessResponse {
  job_id: string
  status: 'pending' | 'running' | 'done' | 'failed' | 'cancelled'
  created_at?: string
  started_at?: string
  finished_at?: string
  progress?: number
  error?: string
  output_path?: string
}

export interface TaskStatusResponse {
  task_id: string
  status: string
  result?: Record<string, any>
  error?: string
}

export interface SampleResponse {
  columns: string[]
  rows: Record<string, any>[]
  total_rows: number
  error: string | null
}

export interface DownloadTokenResponse {
  download_token: string
  filename: string
  file_size: number
  format: string
  sha256?: string
}

const CHUNK_SIZE = 5 * 1024 * 1024

async function computeFileHash(file: File): Promise<string> {
  const buffer = await file.arrayBuffer()
  const hashBuffer = await crypto.subtle.digest('SHA-256', buffer)
  const hashArray = Array.from(new Uint8Array(hashBuffer))
  return hashArray.map((b) => b.toString(16).padStart(2, '0')).join('')
}

export async function initiateUpload(
  filename: string,
  fileSize: number,
  fileHash: string
): Promise<UploadInitiateResponse> {
  const response = await request.post<UploadInitiateResponse>({
    url: '/dataset/upload/initiate',
    data: {
      filename,
      file_size: fileSize,
      file_hash: fileHash,
      chunk_size: CHUNK_SIZE
    }
  })
  return response
}

export async function uploadChunk(
  uploadId: string,
  chunkNumber: number,
  chunk: Blob
): Promise<UploadChunkResponse> {
  const formData = new FormData()
  formData.append('upload_id', uploadId)
  formData.append('chunk_index', String(chunkNumber))
  formData.append('file', chunk)

  const response = await request.post<UploadChunkResponse>({
    url: '/dataset/upload/chunk',
    data: formData
  })
  return response
}

export async function completeUpload(
  uploadId: string,
  filename: string,
  fileFormat: string,
  fileSize: number,
  ownerId?: number
): Promise<UploadCompleteResponse> {
  const response = await request.post<UploadCompleteResponse>({
    url: '/dataset/upload/complete',
    data: {
      upload_id: uploadId,
      owner_id: ownerId ?? 0,
      name: filename.replace(/\.[^.]+$/, ''),
      file_format: fileFormat,
      file_size: fileSize
    }
  })
  return response
}

export async function uploadDataset(
  file: File,
  onProgress?: (percent: number, phase: string, detail?: Record<string, any>) => void,
  ownerId?: number
): Promise<UploadCompleteResponse> {
  const format = file.name.split('.').pop() || 'csv'

  onProgress?.(0, 'hashing')
  const fileHash = await computeFileHash(file)
  onProgress?.(5, 'hash_complete', { hash: fileHash })

  onProgress?.(10, 'initiating')
  const initResponse = await initiateUpload(file.name, file.size, fileHash)
  const { upload_id, chunk_size, total_chunks } = initResponse

  const chunks: Blob[] = []
  let start = 0
  while (start < file.size) {
    const end = Math.min(start + chunk_size, file.size)
    chunks.push(file.slice(start, end))
    start = end
  }

  const chunkProgress: number[] = new Array(total_chunks).fill(0)

  const uploadChunkWithProgress = async (chunk: Blob, num: number): Promise<void> => {
    await uploadChunk(upload_id, num, chunk)
    chunkProgress[num] = 100
    const avgProgress = chunkProgress.reduce((a, b) => a + b, 0) / total_chunks
    const percent = 15 + Math.round(avgProgress * 80)
    onProgress?.(percent, 'uploading', { current: num + 1, total: total_chunks })
  }

  const batchSize = 3
  for (let i = 0; i < chunks.length; i += batchSize) {
    const batch = chunks.slice(i, i + batchSize)
    await Promise.all(batch.map((chunk, idx) => uploadChunkWithProgress(chunk, i + idx)))
  }

  onProgress?.(95, 'completing')
  const completeResponse = await completeUpload(upload_id, file.name, format, file.size, ownerId)

  onProgress?.(100, 'complete', { datasetId: completeResponse.dataset_id })
  return completeResponse
}

export async function getDatasets(): Promise<{
  records: DatasetItemDTO[]
  current: number
  size: number
  total: number
}> {
  const response = await request.get<DatasetListResponse>({
    url: '/datasets'
  })
  return {
    records: response.items || [],
    current: 1,
    size: response.items?.length || 0,
    total: response.total || 0
  }
}

export async function getDatasetTimes(): Promise<{
  total: number
  today_new: number
  today_modified: number
}> {
  const response = await request.get<{
    total: number
    today_new: number
    today_modified: number
    error: string | null
  }>({
    url: '/datasets/times'
  })
  return {
    total: response.total ?? 0,
    today_new: response.today_new ?? 0,
    today_modified: response.today_modified ?? 0
  }
}

export async function getDatasetDetail(id: number): Promise<Dataset | null> {
  try {
    const response = await request.post<{ dataset: Dataset | null; error?: string }>({
      url: '/dataset/get',
      data: { dataset_id: id }
    })
    return response.dataset || null
  } catch {
    return null
  }
}

export async function deleteDataset(id: number): Promise<void> {
  return request.del({
    url: '/datasets',
    data: { dataset_ids: [id] }
  })
}

export async function deleteDatasets(ids: number[]): Promise<void> {
  return request.del({
    url: '/datasets',
    data: { dataset_ids: ids }
  })
}

export async function processDataset(
  datasetId: number,
  requestParams: ProcessRequest
): Promise<ProcessResponse> {
  return request.post<ProcessResponse>({
    url: '/dataset/process',
    data: { dataset_id: datasetId, ...requestParams }
  })
}

export async function getTaskStatus(_taskId: string): Promise<TaskStatusResponse> {
  throw new Error('[已废弃] 任务状态请通过 WebSocket 获取，不可使用 HTTP 轮询')
}

export async function getTags(): Promise<TagsGetResponse> {
  try {
    const response = await request.get<TagsGetResponse>({
      url: '/tags'
    })
    return response
  } catch {
    return { success: false, error: 'Failed to fetch tags', tags: [] }
  }
}

export async function updateDataset(data: {
  dataset_id: number
  name?: string
  desc?: string
  tag_ids?: number[]
}): Promise<{ success: boolean; error?: string }> {
  try {
    const response = await request.patch<{ success: boolean; error?: string }>({
      url: '/dataset',
      data
    })
    return response
  } catch (err: any) {
    return { success: false, error: err.message || 'Failed to update dataset' }
  }
}

export async function createTag(
  name: string,
  color: string,
  desc: string = ''
): Promise<{ success: boolean; error?: string }> {
  try {
    const response = await request.post<{ success: boolean; error?: string }>({
      url: '/tag',
      data: { name, color, desc }
    })
    return response
  } catch (err: any) {
    return { success: false, error: err.message || 'Failed to create tag' }
  }
}

export async function deleteTag(tagId: number): Promise<{ success: boolean; error?: string }> {
  try {
    const response = await request.request<{ success: boolean; error?: string }>({
      url: '/tag',
      method: 'DELETE',
      data: { tag_id: tagId, force: false }
    })
    return response
  } catch (err: any) {
    return { success: false, error: err.message || 'Failed to delete tag' }
  }
}

export async function getDatasetSample(
  datasetId: number,
  limit: number = 20
): Promise<SampleResponse> {
  try {
    const response = await request.post<SampleResponse>({
      url: '/dataset/sample',
      data: { dataset_id: datasetId, limit }
    })
    return response
  } catch {
    return { columns: [], rows: [], total_rows: 0, error: 'Failed to fetch sample' }
  }
}

export async function requestDownloadToken(
  datasetId: number
): Promise<DownloadTokenResponse | null> {
  try {
    const response = await request.post<DownloadTokenResponse>({
      url: '/dataset/download',
      data: { dataset_id: datasetId }
    })
    return response
  } catch {
    return null
  }
}

export interface DatasetLogsResponse {
  lines: string[]
  error?: string
}

export async function getDatasetLogs(jobId: string): Promise<DatasetLogsResponse> {
  try {
    return await request.get<DatasetLogsResponse>({
      url: '/dataset/logs',
      params: { job_id: jobId }
    })
  } catch {
    return { lines: [], error: '请求失败' }
  }
}
