import request from '@/utils/http'
import { DATASET_TABLE_DATA, CLEANING_SAMPLES, MOCK_PROCESSING_LOGS, DEFAULT_CLEANING_CONFIG } from '@/mock/temp/formData'

/** 获取数据集列表 */
export function fetchGetDatasetList(params: Api.DataManage.DatasetSearchParams) {
  return request.get<Api.DataManage.DatasetList>({
    url: '/api/dataset/list',
    params
  })
}

/** 获取数据集详情 */
export function fetchGetDatasetDetail(id: number) {
  return request.get<Api.DataManage.DatasetListItem>({
    url: `/api/dataset/detail/${id}`
  })
}

/** 删除数据集 */
export function fetchDeleteDataset(id: number) {
  return request.del({
    url: `/api/dataset/delete/${id}`
  })
}

/** Mock: 获取数据集列表（静态开发用，后端就绪后替换为 fetchGetDatasetList） */
export function fetchGetDatasetListMock(params: Api.DataManage.DatasetSearchParams): Promise<Api.DataManage.DatasetList> {
  return new Promise((resolve) => {
    setTimeout(() => {
      let filtered = [...DATASET_TABLE_DATA]

      if (params.name) {
        const keyword = params.name.toLowerCase()
        filtered = filtered.filter(
          (d) => d.name.toLowerCase().includes(keyword) || d.description.toLowerCase().includes(keyword)
        )
      }
      if (params.format) {
        filtered = filtered.filter((d) => d.format === params.format)
      }
      if (params.status) {
        filtered = filtered.filter((d) => d.status === params.status)
      }
      if (params.tag) {
        filtered = filtered.filter((d) => d.tags.some((t) => t.label === params.tag))
      }
      if (params.creator) {
        filtered = filtered.filter((d) => d.creator === params.creator)
      }

      const current = params.current || 1
      const size = params.size || 10
      const start = (current - 1) * size
      const records = filtered.slice(start, start + size)

      resolve({
        records,
        current,
        size,
        total: filtered.length
      })
    }, 300)
  })
}

/** Mock: 获取清洗预览样本 */
export function fetchGetCleaningSamplesMock(): Promise<Api.DataManage.DataProcessing.CleaningSample[]> {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(CLEANING_SAMPLES as Api.DataManage.DataProcessing.CleaningSample[])
    }, 200)
  })
}

/** Mock: 刷新样本（随机重排） */
export function fetchRefreshCleaningSamplesMock(): Promise<Api.DataManage.DataProcessing.CleaningSample[]> {
  return new Promise((resolve) => {
    setTimeout(() => {
      const shuffled = [...CLEANING_SAMPLES].sort(() => Math.random() - 0.5)
      resolve(shuffled as Api.DataManage.DataProcessing.CleaningSample[])
    }, 150)
  })
}

/** Mock: 提交清洗任务 */
export function fetchSubmitCleaningTaskMock(config: Api.DataManage.DataProcessing.CleaningConfig): Promise<{ taskId: string }> {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve({ taskId: `cln_${Date.now().toString(36)}` })
    }, 500)
  })
}

/** Mock: 获取处理任务状态 */
export function fetchGetProcessingTaskMock(taskId: string): Promise<Api.DataManage.DataProcessing.ProcessingTask> {
  return new Promise((resolve) => {
    const mockProgress = Math.min(Math.floor(Math.random() * 30) + 50, 95)
    setTimeout(() => {
      resolve({
        taskId,
        datasetName: '客户对话_原始.csv',
        status: 'processing',
        progress: mockProgress,
        eta: '00:12:45',
        rawCount: 52000,
        filteredCount: 4548,
        dedupedCount: 8521,
        finalCount: 38931
      })
    }, 200)
  })
}

/** Mock: 获取处理任务日志 */
export function fetchGetProcessingLogsMock(_taskId: string): Promise<Api.DataManage.DataProcessing.ProcessingLog[]> {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(MOCK_PROCESSING_LOGS as Api.DataManage.DataProcessing.ProcessingLog[])
    }, 300)
  })
}

/** Mock: 获取默认清洗配置 */
export function fetchGetDefaultCleaningConfigMock(): Promise<Api.DataManage.DataProcessing.CleaningConfig> {
  return new Promise((resolve) => {
    setTimeout(() => {
      resolve(DEFAULT_CLEANING_CONFIG as Api.DataManage.DataProcessing.CleaningConfig)
    }, 100)
  })
}
