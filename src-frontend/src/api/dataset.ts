import axios from 'axios'
import request from '@/utils/http'

export interface DatasetMeta {
  format: 'csv' | 'xlsx' | 'json'
  file_path: string
  file_size: number
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
  items: Dataset[]
  total: number
  error: string | null
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
}

export interface UploadChunkResponse {
  upload_id: string
  chunk_number: number
  received: boolean
  message: string
}

export interface UploadCompleteResponse {
  upload_id: string
  task_id: string
  dataset_id: number
  status: string
  message: string
}

export interface ProcessRequest {
  process_type: 'clean' | 'convert'
  convert_format?: 'alpaca' | 'sharegpt'
  remove_duplicates?: boolean
  fill_missing?: boolean
  missing_strategy?: 'mean' | 'median' | 'drop'
}

export interface ProcessResponse {
  task_id: string
  status: string
  message: string
}

export interface TaskStatusResponse {
  task_id: string
  status: string
  result?: Record<string, any>
  error?: string
}

export interface SampleResponse {
  headers: string[]
  samples: Record<string, any>[]
  total: number
}

const CHUNK_SIZE = 5 * 1024 * 1024

export async function initiateUpload(filename: string, fileSize: number, fileFormat: string): Promise<UploadInitiateResponse> {
  const response = await axios.post('/api/v1/dataset/upload/initiate', {
    filename,
    file_size: fileSize,
    file_hash: '',
    chunk_size: CHUNK_SIZE
  })
  return response.data
}

export async function uploadChunk(
  uploadId: string,
  chunkNumber: number,
  chunk: Blob
): Promise<UploadChunkResponse> {
  const formData = new FormData()
  formData.append('file', chunk)

  const response = await axios.post<UploadChunkResponse>(
    `/api/v1/dataset/upload/chunk?upload_id=${uploadId}&chunk_index=${chunkNumber}`,
    formData,
    {
      headers: { 'Content-Type': 'multipart/form-data' }
    }
  )
  return response.data
}

export async function completeUpload(
  uploadId: string,
  filename: string,
  fileFormat: string,
  fileSize: number
): Promise<UploadCompleteResponse> {
  const response = await axios.post('/api/v1/dataset/upload/complete', {
    upload_id: uploadId,
    name: filename.replace(/\.[^.]+$/, ''),
    file_format: fileFormat,
    file_size: fileSize
  })
  return response.data
}

export async function uploadDataset(
  file: File,
  onProgress?: (percent: number, phase: string) => void
): Promise<UploadCompleteResponse> {
  const format = file.name.split('.').pop() || 'csv'

  onProgress?.(0, 'initiating')
  const initResponse = await initiateUpload(file.name, file.size, format)
  const { upload_id, chunk_size, total_chunks } = initResponse

  const chunks: Blob[] = []
  let start = 0
  let chunkNum = 0
  while (start < file.size) {
    const end = Math.min(start + chunk_size, file.size)
    chunks.push(file.slice(start, end))
    start = end
    chunkNum++
  }

  const chunkProgress: number[] = new Array(total_chunks).fill(0)
  let completedChunks = 0

  const uploadChunkWithProgress = async (chunk: Blob, num: number): Promise<void> => {
    await uploadChunk(upload_id, num, chunk)
    completedChunks++
    chunkProgress[num] = 100
    const avgProgress = chunkProgress.reduce((a, b) => a + b, 0) / total_chunks
    onProgress?.(Math.round(avgProgress), 'uploading')
  }

  const batchSize = 3
  for (let i = 0; i < chunks.length; i += batchSize) {
    const batch = chunks.slice(i, i + batchSize)
    await Promise.all(batch.map((chunk, idx) => uploadChunkWithProgress(chunk, i + idx)))
  }

  onProgress?.(100, 'completing')
  const completeResponse = await completeUpload(upload_id, file.name, format, file.size)

  onProgress?.(100, 'complete')
  return completeResponse
}

export interface GetDatasetsParams {
  skip?: number
  limit?: number
}

export async function getDatasets(params: GetDatasetsParams = {}): Promise<{
  records: Dataset[]
  current: number
  size: number
  total: number
}> {
  const { skip = 0, limit = 100 } = params
  const response = await axios.get<DatasetListResponse>('/api/v1/dataset', {
    params: { skip, limit }
  })
  const items = response.data.items || []
  return {
    records: items,
    current: 1,
    size: limit,
    total: response.data.total || items.length
  }
}

export async function getDatasetDetail(id: number): Promise<Dataset | null> {
  try {
    const response = await axios.get(`/api/v1/dataset/${id}`)
    return response.data.dataset || null
  } catch {
    return null
  }
}

export async function deleteDataset(id: number): Promise<void> {
  return request.del({
    url: `/dataset/${id}`
  })
}

export async function processDataset(datasetId: number, requestParams: ProcessRequest): Promise<ProcessResponse> {
  return request.post<ProcessResponse>({
    url: `/dataset/${datasetId}/process`,
    data: requestParams
  })
}

export async function getTaskStatus(taskId: string): Promise<TaskStatusResponse> {
  return Promise.reject(new Error('Task status is provided via WebSocket, not HTTP polling'))
}

export async function getTags(): Promise<TagsGetResponse> {
  try {
    const response = await axios.get<TagsGetResponse>('/api/v1/tags')
    return response.data
  } catch {
    return { success: false, error: 'Failed to fetch tags', tags: [] }
  }
}

export async function createTag(name: string, color: string, desc: string = ''): Promise<{ success: boolean; error?: string }> {
  try {
    const response = await axios.post('/api/v1/tag/', { name, color, desc })
    return response.data
  } catch (err: any) {
    return { success: false, error: err.response?.data?.error || 'Failed to create tag' }
  }
}

export async function getDatasetSample(datasetId: number, limit: number = 20): Promise<SampleResponse> {
  try {
    const response = await axios.get<SampleResponse>(`/api/v1/dataset/${datasetId}/sample`, {
      params: { limit }
    })
    return response.data
  } catch {
    return { headers: [], samples: [], total: 0 }
  }
}

export async function requestDownloadToken(datasetId: number): Promise<{
  download_token: string
  filename: string
  file_size: number
  format: string
} | null> {
  try {
    const response = await axios.post(`/api/v1/dataset/${datasetId}/download`)
    return response.data
  } catch {
    return null
  }
}