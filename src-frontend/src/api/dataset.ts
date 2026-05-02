import axios from 'axios'
import request from '@/utils/http'

export interface Dataset {
  id: number
  name: string
  description: string | null
  file_path: string
  file_size: number
  format: string
  total_records: number
  status: 'pending' | 'processing' | 'converting' | 'ready' | 'error'
  created_at: string
  updated_at: string
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

const CHUNK_SIZE = 5 * 1024 * 1024

export async function initiateUpload(filename: string, fileSize: number, fileFormat: string): Promise<UploadInitiateResponse> {
  const params = new URLSearchParams({
    filename,
    file_size: fileSize.toString(),
    file_format: fileFormat
  })
  const response = await axios.get(`/api/v1/datasets/initiate-upload?${params.toString()}`)
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
    `/api/v1/datasets/upload-chunk?upload_id=${uploadId}&chunk_number=${chunkNumber}`,
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
  const params = new URLSearchParams({
    upload_id: uploadId,
    filename,
    file_format: fileFormat,
    file_size: fileSize.toString()
  })
  const response = await axios.post(`/api/v1/datasets/complete-upload?${params.toString()}`)
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

export interface DatasetListResponse {
  records: Dataset[]
  current: number
  size: number
  total: number
}

export interface GetDatasetsParams {
  skip?: number
  limit?: number
}

export async function getDatasets(params: GetDatasetsParams = {}): Promise<DatasetListResponse> {
  const { skip = 0, limit = 100 } = params
  const response = await axios.get('/api/v1/datasets', {
    params: { skip, limit }
  })
  const records: Dataset[] = response.data
  return {
    records,
    current: 1,
    size: limit,
    total: records.length
  }
}

export async function getDataset(id: number): Promise<Dataset> {
  return request.get<Dataset>({
    url: `/datasets/${id}`
  })
}

export async function deleteDataset(id: number): Promise<void> {
  return request.del({
    url: `/datasets/${id}`
  })
}

export async function processDataset(datasetId: number, requestParams: ProcessRequest): Promise<ProcessResponse> {
  return request.post<ProcessResponse>({
    url: `/datasets/${datasetId}/process`,
    data: requestParams
  })
}

export async function getTaskStatus(taskId: string): Promise<TaskStatusResponse> {
  return request.get<TaskStatusResponse>({
    url: `/datasets/tasks/${taskId}`
  })
}