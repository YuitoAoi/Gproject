<template>
  <div class="dataset-hub-page">
    <!-- ========== 模块一：页头区域 ========== -->
    <div class="page-header mb-5">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="page-header__title">数据集管理</h1>
          <p class="page-header__subtitle"
            >这里是您的预训练数据资产池，支持多格式解析与分块上传。</p
          >
        </div>
        <ElButton class="page-header__button" size="large" @click="uploadVisible = true" v-ripple>
          <span class="ri:add-line mr-1"></span>导入数据集
        </ElButton>
      </div>
    </div>

    <!-- ========== 模块二：顶部融合面板 ========== -->
    <div class="fusion-panel grid grid-cols-1 lg:grid-cols-5 gap-5 mb-5">
      <!-- 左侧 40%：动态指标卡片 -->
      <div class="lg:col-span-2 grid grid-cols-2 gap-4">
        <!-- 总数据集卡片 -->
        <div class="art-card p-5 relative">
          <div class="flex flex-col justify-between h-full">
            <div>
              <p class="text-sm text-g-500">数据集总量</p>
              <div class="text-2xl font-medium mt-2">{{ stats.total }}</div>
              <p class="text-base text-g-600 mt-2">今日新增</p>
              <span class="font-medium text-success">+{{ stats.today_new }}</span>
              <p class="text-base text-g-600 mt-2">今日修改</p>
              <span class="font-medium text-primary">+{{ stats.today_modified }}</span>
            </div>
          </div>
          <div class="size-12 rounded-lg flex-cc bg-theme/10 absolute bottom-4 right-4">
            <ArtSvgIcon icon="ri:archive-line" class="text-xl text-theme" />
          </div>
        </div>
        <!-- 存储水位卡片 -->
        <div class="art-card p-5 relative">
          <div class="flex flex-col justify-between h-full">
            <div>
              <p class="text-sm text-g-500">存储水位</p>
              <div class="text-2xl font-medium mt-2">35%</div>
              <p class="text-base text-g-600 mt-2">已用存储空间</p>
              <div class="mt-2">
                <ElProgress :percentage="35" :stroke-width="6" :show-text="false" color="#E6A23C" />
              </div>
              <small class="text-g-500 mt-1">4.2 GB / 12 GB</small>
            </div>
          </div>
          <div class="size-12 rounded-lg flex-cc bg-warning/10 absolute bottom-4 right-4">
            <ArtSvgIcon icon="ri:hard-drive-3-line" class="text-xl text-warning" />
          </div>
        </div>
      </div>

      <!-- 右侧 60%：任务队列 -->
      <div class="lg:col-span-3">
        <div class="art-card p-0" style="height: 240px">
          <!-- 任务队列头部 -->
          <div class="task-queue-header">
            <div class="flex items-center gap-2">
              <ArtSvgIcon icon="ri:file-list-3-line" class="text-lg text-g-600" />
              <span class="text-sm font-medium text-g-700">
                任务队列
                <template v-if="uploadTasks.length > 0">
                  <span class="task-count-badge">{{ uploadTasks.length }}</span>
                </template>
              </span>
              <template v-if="uploadTasks.length > 0">
                <span class="text-xs text-g-500">
                  ({{ runningCount }}个执行中<template v-if="errorCount > 0"
                    >, {{ errorCount }}个异常</template
                  >)
                </span>
              </template>
              <template v-else>
                <span class="text-xs text-g-500 font-normal">(当前空闲)</span>
              </template>
            </div>
            <ElButton
              v-if="uploadTasks.length > 0"
              text
              size="small"
              type="info"
              @click="clearCompletedTasks"
            >
              清除已完成
            </ElButton>
          </div>

          <!-- 场景A：无上传任务 -->
          <div v-if="uploadTasks.length === 0" class="task-empty">
            <ArtSvgIcon icon="ri:file-list-3-line" class="text-4xl text-g-400 mb-2" />
            <p class="text-sm text-g-600">暂无上传任务</p>
            <p class="text-xs text-g-500 mt-1"
              >点击上方「导入新数据集」开始扩充您的预训练资产池。</p
            >
          </div>

          <!-- 场景B：有上传任务 -->
          <div v-else class="task-list">
            <ElScrollbar>
              <div
                v-for="task in uploadTasks"
                :key="task.id"
                class="task-item"
                :class="{
                  'task-item-error': task.status === 'error',
                  'task-item-success': task.status === 'completed',
                  'task-item-paused': task.status === 'paused'
                }"
              >
                <!-- 文件图标 -->
                <div class="task-icon" :class="getTaskIconClass(task)">
                  <ArtSvgIcon :icon="getTaskIcon(task)" class="text-lg" />
                </div>

                <!-- 任务信息 -->
                <div class="task-info">
                  <div class="flex items-center justify-between mb-1">
                    <span class="task-name truncate">{{ task.name }}</span>
                    <span v-if="task.status !== 'error'" class="task-percent"
                      >{{ task.progress }}%</span
                    >
                    <ElTag v-else size="small" type="danger" effect="plain" class="!py-0">
                      网络异常
                    </ElTag>
                  </div>

                  <!-- 进度条 -->
                  <template v-if="task.status !== 'error'">
                    <div class="task-progress">
                      <ElProgress
                        :percentage="task.progress"
                        :stroke-width="4"
                        :show-text="false"
                        :color="
                          task.status === 'completed'
                            ? '#67C23A'
                            : task.status === 'paused'
                              ? '#E6A23C'
                              : '#409EFF'
                        "
                      />
                    </div>
                    <div class="task-meta">
                      <span v-if="task.status === 'uploading'" class="flex items-center gap-1">
                        <ArtSvgIcon icon="ri:arrow-up-line" class="text-xs" />
                        {{ task.speed }}
                      </span>
                      <span v-if="task.status === 'completed'">
                        <ArtSvgIcon icon="ri:check-line" class="text-success text-xs mr-0.5" />
                        已完成
                      </span>
                      <span v-if="task.status === 'paused'">
                        <ArtSvgIcon icon="ri:pause-line" class="text-warning text-xs mr-0.5" />
                        已暂停
                      </span>
                      <span class="text-g-400">|</span>
                      <span v-if="task.status === 'uploading'" class="text-g-600"
                        >剩余 {{ task.remaining }}</span
                      >
                      <span v-else-if="task.status === 'paused'" class="text-g-600"
                        >点击恢复继续上传</span
                      >
                    </div>
                  </template>
                  <template v-else>
                    <div class="task-error-msg">
                      <ArtSvgIcon icon="ri:error-warning-line" class="text-danger text-xs mr-0.5" />
                      上传失败 — {{ task.remaining || '网络连接中断，请检查网络后重试' }}
                    </div>
                  </template>
                </div>

                <!-- 操作按钮 -->
                <div class="task-actions">
                  <template v-if="task.status === 'uploading'">
                    <ElButton
                      text
                      size="small"
                      class="!p-2 hover:!bg-blue-50"
                      @click="pauseTask(task)"
                      title="暂停"
                    >
                      <ArtSvgIcon
                        icon="ri:pause-line"
                        class="text-lg text-g-500 hover:!text-blue-500"
                      />
                    </ElButton>
                  </template>
                  <template v-if="task.status === 'paused'">
                    <ElButton
                      text
                      size="small"
                      class="!p-2 hover:!bg-blue-50"
                      @click="resumeTask(task)"
                      title="恢复"
                    >
                      <ArtSvgIcon
                        icon="ri:play-line"
                        class="text-lg text-success hover:!text-blue-500"
                      />
                    </ElButton>
                  </template>
                  <template v-if="task.status === 'error'">
                    <ElButton
                      text
                      size="small"
                      class="!p-2 hover:!bg-blue-50"
                      @click="resumeTask(task)"
                      title="重试"
                    >
                      <ArtSvgIcon icon="ri:refresh-line" class="text-lg text-blue-500" />
                    </ElButton>
                  </template>
                  <ElButton
                    text
                    size="small"
                    class="!p-2 hover:!bg-red-50"
                    @click="removeTask(task)"
                    title="移除"
                  >
                    <ArtSvgIcon
                      icon="ri:close-line"
                      class="text-lg text-g-500 hover:!text-danger"
                    />
                  </ElButton>
                </div>
              </div>
            </ElScrollbar>
          </div>
        </div>
      </div>
    </div>

    <!-- ========== 模块三：数据集列表看板 ========== -->
    <ElCard class="art-card !p-0" shadow="never">
      <!-- 工具栏：搜索筛选（左） + 批量操作（右） -->
      <div
        class="toolbar flex items-center justify-between flex-wrap gap-3 px-5 py-3 border-b border-g-100"
      >
        <!-- 左侧：搜索筛选 -->
        <div class="flex items-center gap-2 flex-wrap">
          <ElInput
            v-model="searchKeyword"
            placeholder="搜索数据集名称或 ID..."
            class="!w-52"
            clearable
            @keyup.enter="handleToolbarSearch"
          >
            <template #prefix>
              <span class="ri:search-line text-g-400"></span>
            </template>
          </ElInput>
          <ElSelect
            v-model="filterTag"
            placeholder="标签: 全部"
            class="!w-28"
            clearable
            :popper-attrs="{ style: { maxHeight: '256px', overflowY: 'auto' } }"
          >
            <ElOption
              v-for="tag in tagStore.tags"
              :key="tag.tag_id"
              :label="tag.tag_name"
              :value="tag.tag_name"
            />
          </ElSelect>
          <ElSelect v-model="filterFormat" placeholder="格式: 全部" class="!w-28" clearable>
            <ElOption label="JSON" value="JSON" />
            <ElOption label="CSV" value="CSV" />
            <ElOption label="TXT" value="TXT" />
          </ElSelect>
          <ElSelect v-model="filterStatus" placeholder="状态: 全部" class="!w-28" clearable>
            <ElOption label="已就绪" value="ready" />
            <ElOption label="清洗中" value="processing" />
            <ElOption label="待清洗" value="pending" />
            <ElOption label="异常" value="error" />
          </ElSelect>
          <ElButton type="primary" @click="handleToolbarSearch">
            <span class="ri:search-line mr-1"></span>查询
          </ElButton>
          <ElButton @click="handleSearchReset">
            <span class="ri:refresh-line mr-1"></span>重置
          </ElButton>
        </div>

        <!-- 右侧：批量操作 -->
        <div class="flex items-center gap-2 flex-wrap">
          <ElButton :disabled="selectedRows.length === 0" @click="handleBatchDelete">
            <span class="ri:delete-bin-line mr-1"></span>批量删除
            <template v-if="selectedRows.length > 0">({{ selectedRows.length }})</template>
          </ElButton>
          <ElButton :disabled="selectedRows.length === 0">
            <span class="ri:price-tag-3-line mr-1"></span>批量打标签
          </ElButton>
        </div>
      </div>

      <!-- 数据表格 -->
      <ArtTable
        :loading="loading"
        :data="data"
        :columns="columns"
        :pagination="pagination"
        empty-height="400px"
        @selection-change="handleSelectionChange"
        @pagination:size-change="handleSizeChange"
        @pagination:current-change="handleCurrentChange"
      >
      </ArtTable>
    </ElCard>

    <!-- 上传弹窗 -->
    <DatasetUpload v-model:visible="uploadVisible" @upload-start="handleUploadStart" />

    <!-- 数据集抽屉 -->
    <DatasetDrawer
      v-model:visible="drawerVisible"
      :dataset="currentDataset"
      ref="drawerRef"
      @refresh="refreshData"
    />
  </div>
</template>

<script setup lang="ts">
  import ArtButtonTable from '@/components/core/forms/art-button-table/index.vue'
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import { useTable } from '@/hooks/core/useTable'
  import { useTagStore, type TagInfo } from '@/store/modules/tag'
  import {
    getDatasets,
    getDatasetTimes,
    deleteDatasets,
    uploadDataset,
    type DatasetItemDTO
  } from '@/api/dataset'
  import DatasetUpload from './modules/dataset-upload.vue'
  import DatasetDrawer from './modules/dataset-drawer.vue'
  import { useWebSocketTask } from '@/hooks/core/useWebSocketTask'
  import { nextTick, ref as vueRef, shallowRef, onMounted } from 'vue'
  import { ElTag, ElMessageBox, ElMessage, ElTooltip } from 'element-plus'
  import axios from 'axios'

  defineOptions({ name: 'DatasetHubPage' })

  const drawerRef = vueRef<{ setActiveTab: (tab: string) => void } | null>(null)
  const tagStore = useTagStore()

  // 上传弹窗
  const uploadVisible = ref(false)

  // 抽屉
  const drawerVisible = ref(false)
  const currentDataset = ref<DatasetItemDTO | null>(null)

  // 选中行
  const selectedRows = ref<DatasetItemDTO[]>([])

  // 搜索与筛选
  const searchKeyword = ref('')
  const filterTag = ref('')
  const filterFormat = ref('')
  const filterStatus = ref('')

  // 上传任务队列
  interface UploadTaskItem {
    id: number
    name: string
    progress: number
    status: 'preparing' | 'uploading' | 'paused' | 'completed' | 'error'
    speed: string
    remaining: string
    file?: File
  }

  const uploadTasks = ref<UploadTaskItem[]>([])

  // 数据集统计
  const stats = ref({
    total: 0,
    today_new: 0,
    today_modified: 0
  })

  const fetchTimes = async () => {
    try {
      stats.value = await getDatasetTimes()
    } catch {
      // ignore
    }
  }

  const runningCount = computed(
    () => uploadTasks.value.filter((t) => t.status === 'uploading').length
  )
  const errorCount = computed(() => uploadTasks.value.filter((t) => t.status === 'error').length)

  // 任务图标
  const getTaskIcon = (task: UploadTaskItem) => {
    if (task.status === 'error') return 'ri:file-warning-line'
    if (task.status === 'completed') return 'ri:file-check-line'
    if (task.status === 'paused') return 'ri:file-pause-line'
    return 'ri:file-text-line'
  }

  const getTaskIconClass = (task: UploadTaskItem) => {
    if (task.status === 'error') return 'icon-error'
    if (task.status === 'completed') return 'icon-success'
    if (task.status === 'paused') return 'icon-paused'
    return 'icon-uploading'
  }

  const getProgressColor = (status: string) => {
    if (status === 'completed') return '#67C23A'
    if (status === 'paused') return '#E6A23C'
    return '#409EFF'
  }

  const getStatusConfig = (status: number) => {
    if (status === 2) return { type: 'success' as const, text: '已就绪', dot: '#67C23A' }
    if (status === 1) return { type: 'warning' as const, text: '清洗中', dot: '#409EFF' }
    if (status === -1) return { type: 'danger' as const, text: '异常', dot: '#F56C6C' }
    return { type: 'info' as const, text: '待清洗', dot: '#E6A23C' }
  }

  const resolveTags = (tagIds: number[]) => {
    return tagStore.tags.filter((t) => tagIds.includes(t.tag_id))
  }

  const applyLocalFilters = (records: DatasetItemDTO[]): DatasetItemDTO[] => {
    let result = records
    const params = searchParams as Record<string, any>

    if (params.name) {
      const keyword = params.name.toLowerCase()
      result = result.filter((d) => d.name.toLowerCase().includes(keyword))
    }

    if (params.format) {
      result = result.filter((d) => d.format.toUpperCase() === params.format)
    }

    if (params.status) {
      const statusMap: Record<string, number> = {
        ready: 2,
        processing: 1,
        pending: 0,
        error: -1
      }
      const targetStatus = statusMap[params.status]
      if (targetStatus !== undefined) {
        result = result.filter((d) => d.status === targetStatus)
      }
    }

    if (params.tag) {
      const tag = tagStore.tags.find((t: TagInfo) => t.tag_name === params.tag)
      if (tag) {
        result = result.filter((d) => d.tag_ids.includes(tag.tag_id))
      }
    }

    return result
  }

  const formatSize = (size: number): string => {
    if (size >= 1024 * 1024 * 1024) return `${(size / (1024 * 1024 * 1024)).toFixed(2)} GB`
    if (size >= 1024 * 1024) return `${(size / (1024 * 1024)).toFixed(1)} MB`
    if (size >= 1024) return `${(size / 1024).toFixed(1)} KB`
    return `${size} B`
  }

  const {
    columns,
    columnChecks,
    data,
    loading,
    pagination,
    getData,
    searchParams,
    handleSizeChange,
    handleCurrentChange,
    refreshData,
    refreshSoft
  } = useTable({
    core: {
      apiFn: getDatasets,
      columnsFactory: () => [
        { type: 'selection' },
        { type: 'index', width: 50, label: '#' },
        {
          prop: 'name',
          label: '数据集名称',
          width: 210,
          formatter: (row: DatasetItemDTO) => {
            return h(
              'span',
              {
                class: 'text-sm font-medium truncate cursor-pointer hover:text-primary',
                onClick: () => openDatasetDrawer(row)
              },
              row.name
            )
          }
        },
        {
          prop: 'format',
          label: '格式',
          formatter: (row: DatasetItemDTO) => {
            return h(
              ElTag,
              {
                size: 'small',
                type: row.format === 'json' ? 'primary' : row.format === 'csv' ? 'warning' : 'info',
                effect: 'plain'
              },
              () => row.format.toUpperCase()
            )
          }
        },
        {
          prop: 'tag_ids',
          label: '标签',
          width: 210,
          formatter: (row: DatasetItemDTO) => {
            const tags = resolveTags(row.tag_ids || [])
            if (tags.length === 0) {
              return h('span', { class: 'text-xs text-g-400' }, '—')
            }
            return h(
              'div',
              { class: 'flex flex-wrap gap-1' },
              tags.map((t) =>
                h(
                  ElTag,
                  {
                    size: 'small',
                    effect: 'dark',
                    style: { backgroundColor: t.tag_color, borderColor: t.tag_color }
                  },
                  () => t.tag_name
                )
              )
            )
          }
        },
        {
          prop: 'file_size',
          label: '大小',
          sortable: true,
          formatter: (row: DatasetItemDTO) => formatSize(row.file_size)
        },
        {
          prop: 'status',
          label: '状态',
          formatter: (row: DatasetItemDTO) => {
            const config = getStatusConfig(row.status)
            return h('div', { class: 'flex items-center gap-1.5' }, [
              h('span', {
                class: 'inline-block w-2 h-2 rounded-full flex-shrink-0',
                style: { backgroundColor: config.dot }
              }),
              h('span', { class: 'text-sm' }, config.text)
            ])
          }
        },
        {
          prop: 'updated_at',
          label: '最后修改',
          width: 210,
          sortable: true,
          formatter: (row: DatasetItemDTO) => {
            const date = new Date(row.updated_at)
            return date.toLocaleDateString('zh-CN', {
              year: 'numeric',
              month: '2-digit',
              day: '2-digit',
              hour: '2-digit',
              minute: '2-digit'
            })
          }
        },
        {
          prop: 'operation',
          label: '操作',
          fixed: 'right',
          formatter: (row: DatasetItemDTO) =>
            h('div', { class: 'flex gap-1' }, [
              h(ArtButtonTable, {
                type: 'edit',
                onClick: () => openDatasetDrawer(row, 'edit')
              }),
              h(ArtButtonTable, {
                type: 'delete',
                onClick: () => handleDelete(row)
              })
            ])
        }
      ]
    },
    transform: {
      dataTransformer: (records: DatasetItemDTO[]) => applyLocalFilters(records)
    }
  })

  // 工具栏搜索
  const handleToolbarSearch = () => {
    Object.assign(searchParams, {
      name: searchKeyword.value || undefined,
      tag: filterTag.value || undefined,
      format: filterFormat.value || undefined,
      status: filterStatus.value || undefined
    })
    refreshSoft()
  }

  // 工具栏重置
  const handleSearchReset = () => {
    searchKeyword.value = ''
    filterTag.value = ''
    filterFormat.value = ''
    filterStatus.value = ''
    Object.assign(searchParams, {
      name: undefined,
      tag: undefined,
      format: undefined,
      status: undefined
    })
    refreshSoft()
  }

  onMounted(() => {
    tagStore.fetchTags()
    fetchTimes()
  })

  const openDatasetDrawer = (row: DatasetItemDTO, tab: string = 'meta') => {
    currentDataset.value = row
    drawerVisible.value = true
    nextTick(() => {
      drawerRef.value?.setActiveTab(tab)
    })
  }

  // 非阻塞上传：立即添加到任务队列，后台上传
  const handleUploadStart = (fileInfo: { name: string; size: number; raw: File }) => {
    const task: UploadTaskItem = {
      id: Date.now(),
      name: fileInfo.name,
      progress: 0,
      status: 'preparing',
      speed: '—',
      remaining: '等待中...',
      file: fileInfo.raw
    }
    uploadTasks.value.unshift(task)

    uploadDataset(fileInfo.raw, (percent, phase, detail) => {
      const idx = uploadTasks.value.findIndex((t) => t.id === task.id)
      if (idx === -1) return

      const updatedTask = { ...uploadTasks.value[idx] }
      updatedTask.progress = percent

      switch (phase) {
        case 'hashing':
          updatedTask.status = 'preparing'
          updatedTask.remaining = '计算哈希...'
          updatedTask.speed = '—'
          break
        case 'hash_complete':
          updatedTask.remaining = '开始上传...'
          break
        case 'initiating':
          updatedTask.status = 'uploading'
          updatedTask.remaining = '初始化中...'
          break
        case 'uploading':
          updatedTask.status = 'uploading'
          if (detail) {
            updatedTask.remaining = `上传分片 ${detail.current}/${detail.total}`
          }
          break
        case 'completing':
          updatedTask.remaining = '合并文件中...'
          break
        case 'complete':
          updatedTask.progress = 100
          updatedTask.status = 'completed'
          updatedTask.remaining = '—'
          updatedTask.speed = '—'
          break
      }

      uploadTasks.value[idx] = updatedTask
    })
      .then((response: any) => {
        const celTaskId = response?.task_id
        if (celTaskId) {
          handleTrackCeleryProgress(task.id, celTaskId)
        } else {
          completeUploadTask(task.id)
          ElMessage.success(`数据集「${fileInfo.name}」上传完成`)
          refreshData()
          fetchTimes()
        }
      })
      .catch((err: any) => {
        const idx = uploadTasks.value.findIndex((t) => t.id === task.id)
        if (idx !== -1) {
          uploadTasks.value[idx] = {
            ...uploadTasks.value[idx],
            status: 'error',
            remaining: err.message || '上传失败'
          }
        }
        ElMessage.error('上传失败: ' + (err.message || '未知错误'))
      })
  }

  // 通过 WebSocket 追踪 Celery 任务进度
  const handleTrackCeleryProgress = (uiTaskId: number, celTaskId: string) => {
    const wsUrl = `${import.meta.env.VITE_WS_URL || 'ws://localhost:8000'}/ws/progress`
    const ws = new WebSocket(`${wsUrl}?task_id=${celTaskId}`)

    ws.onopen = () => {
      console.log('[WS] 已连接到任务:', celTaskId)
    }

    ws.onmessage = (event) => {
      try {
        const data = JSON.parse(event.data)
        if (data.type === 'heartbeat' || data.type === 'pong') return

        const idx = uploadTasks.value.findIndex((t) => t.id === uiTaskId)
        if (idx === -1) return

        const updatedTask = { ...uploadTasks.value[idx] }
        updatedTask.progress = data.percentage || updatedTask.progress
        updatedTask.remaining =
          data.phase === 'merging'
            ? `合并中 ${data.current}/${data.total}`
            : data.phase === 'saving'
              ? '保存中...'
              : data.message || data.phase

        if (data.status === 'success') {
          updatedTask.progress = 100
          updatedTask.status = 'completed'
          updatedTask.speed = '—'
          updatedTask.remaining = '—'
          uploadTasks.value[idx] = updatedTask
          console.log('[WS] 收到成功信号，任务完成:', uiTaskId)
          ws.close()
          completeUploadTask(uiTaskId)
          ElMessage.success(data.message || '上传任务完成')
          refreshData()
          fetchTimes()
          return
        } else if (data.status === 'failure') {
          updatedTask.status = 'error'
          updatedTask.remaining = data.message || '合并失败'
          uploadTasks.value[idx] = updatedTask
          console.log('[WS] 收到失败信号:', data.message)
          ws.close()
          ElMessage.error(data.message || '文件合并失败')
          return
        }

        uploadTasks.value[idx] = updatedTask
      } catch (e) {
        console.error('[WS] 消息解析失败:', e)
      }
    }

    ws.onerror = () => {
      console.warn('[WS] 连接失败，将通过HTTP轮询确认任务状态')
      pollTaskStatus(celTaskId, uiTaskId)
    }

    ws.onclose = () => {
      console.log('[WS] 连接已关闭:', celTaskId)
    }

    // 兜底：30秒后未收到完成信号，通过HTTP轮询确认
    setTimeout(() => {
      const currentTask = uploadTasks.value.find((t) => t.id === uiTaskId)
      if (currentTask && currentTask.status === 'uploading') {
        pollTaskStatus(celTaskId, uiTaskId)
      }
    }, 30000)
  }

  // HTTP轮询Celery任务状态作为兜底方案
  // 注意：任务进度由WebSocket实时推送，此处仅作为极端情况下的降级处理
  const pollTaskStatus = async (celTaskId: string, uiTaskId: number) => {
    const idx = uploadTasks.value.findIndex((t) => t.id === uiTaskId)
    if (idx === -1) return

    const currentStatus = uploadTasks.value[idx].status
    if (currentStatus === 'completed' || currentStatus === 'error') return

    // WebSocket未连接且30秒内未收到完成信号时，提示用户刷新页面确认状态
    ElMessage.warning('上传已进入最后阶段，请刷新页面查看最新状态')
    uploadTasks.value[idx] = {
      ...uploadTasks.value[idx],
      remaining: '等待最终确认...'
    }
  }

  // 标记上传任务完成
  const completeUploadTask = (uiTaskId: number) => {
    const idx = uploadTasks.value.findIndex((t) => t.id === uiTaskId)
    if (idx !== -1) {
      uploadTasks.value[idx] = {
        ...uploadTasks.value[idx],
        progress: 100,
        status: 'completed',
        speed: '—',
        remaining: '—'
      }
    }
  }

  const pauseTask = (task: UploadTaskItem) => {
    task.status = 'paused'
    const idx = uploadTasks.value.findIndex((t) => t.id === task.id)
    if (idx !== -1) uploadTasks.value[idx] = { ...task }
  }

  const resumeTask = (task: UploadTaskItem) => {
    const idx = uploadTasks.value.findIndex((t) => t.id === task.id)
    if (idx === -1) return

    if (task.status === 'error' && task.file) {
      uploadTasks.value[idx] = { ...task, progress: 0, status: 'uploading', remaining: '计算中...' }

      uploadDataset(task.file, (percent, phase) => {
        const i = uploadTasks.value.findIndex((t) => t.id === task.id)
        if (i === -1) return

        const updated = { ...uploadTasks.value[i] }
        updated.progress = percent

        if (phase === 'initiating') {
          updated.remaining = '初始化中...'
        } else if (phase === 'uploading') {
          updated.remaining = '上传中...'
        } else if (phase === 'completing') {
          updated.remaining = '处理中...'
        } else if (phase === 'complete') {
          updated.progress = 100
          updated.remaining = '文件合并中...'
        }

        uploadTasks.value[i] = updated
      })
        .then((response: any) => {
          const celTaskId = response?.task_id
          if (celTaskId) {
            handleTrackCeleryProgress(task.id, celTaskId)
          } else {
            completeUploadTask(task.id)
            ElMessage.success(`数据集「${task.name}」上传完成`)
            refreshData()
            fetchTimes()
          }
        })
        .catch((err: any) => {
          const i = uploadTasks.value.findIndex((t) => t.id === task.id)
          if (i !== -1) {
            uploadTasks.value[i] = {
              ...uploadTasks.value[i],
              status: 'error',
              remaining: err.response?.data?.detail || err.message || '上传失败'
            }
          }
          ElMessage.error('上传失败: ' + (err.response?.data?.detail || err.message || '未知错误'))
        })
    } else if (task.status === 'paused') {
      uploadTasks.value[idx] = { ...task, status: 'uploading' }
    }
  }

  const removeTask = (task: UploadTaskItem) => {
    const idx = uploadTasks.value.findIndex((t) => t.id === task.id)
    if (idx !== -1) {
      uploadTasks.value.splice(idx, 1)
    }
  }

  const clearCompletedTasks = () => {
    uploadTasks.value = uploadTasks.value.filter((t) => t.status !== 'completed')
  }

  // 批量删除
  const handleBatchDelete = async () => {
    if (selectedRows.value.length === 0) return
    try {
      await ElMessageBox.confirm(
        `确定要删除选中的 ${selectedRows.value.length} 个数据集吗？删除后不可恢复。`,
        '批量删除',
        {
          confirmButtonText: '确定删除',
          cancelButtonText: '取消',
          type: 'warning'
        }
      )
      const ids = selectedRows.value.map((row) => row.id)
      await deleteDatasets(ids)
      ElMessage.success(`已删除 ${ids.length} 个数据集`)
      selectedRows.value = []
      refreshData()
      fetchTimes()
    } catch (err: any) {
      if (err !== 'cancel') {
        ElMessage.error('删除失败: ' + (err.message || '未知错误'))
      }
    }
  }

  // 单行删除
  const handleDelete = async (row: DatasetItemDTO) => {
    try {
      await ElMessageBox.confirm(
        `确定要删除数据集「${row.name}」吗？删除后不可恢复。`,
        '删除数据集',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
      )
      await deleteDatasets([row.id])
      ElMessage.success('删除成功')
      refreshData()
      fetchTimes()
    } catch (err: any) {
      if (err !== 'cancel') {
        ElMessage.error('删除失败: ' + (err.message || '未知错误'))
      }
    }
  }

  const handleSelectionChange = (selection: DatasetItemDTO[]) => {
    selectedRows.value = selection
  }
</script>

<style lang="scss" scoped>
  .dataset-hub-page {
    padding: 16px 20px;
  }
  .page-header {
    position: relative;
    display: flex;
    flex-direction: column;
    justify-content: center;
    padding: 20px 2rem;
    overflow: hidden;
    color: white;
    background-color: color-mix(in srgb, var(--el-color-primary) 60%, transparent);
    border-radius: calc(var(--custom-radius, 8px) + 2px);

    &::after {
      position: absolute;
      right: -10%;
      bottom: -20%;
      width: 60%;
      height: 140%;
      content: '';
      background: rgb(255 255 255 / 12%);
      border-radius: 30%;
      transform: rotate(-20deg);
    }

    &__title {
      position: relative;
      z-index: 1;
      margin: 0 0 0.25rem;
      font-size: 1.5rem;
      font-weight: 700;
      color: #fff;
    }

    &__subtitle {
      position: relative;
      z-index: 1;
      margin: 0;
      font-size: 0.9rem;
      opacity: 0.9;
      color: #fff;
    }

    &__button {
      position: relative;
      z-index: 1;
      background-color: #5b90ff;
      color: #fff;
      border-color: transparent;
      transition: all 0.3s;

      &:hover {
        opacity: 0.8;
      }
    }
  }
  .fusion-panel {
    min-height: 220px;
  }

  // 任务队列样式
  .task-queue-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    height: 50px;
    padding: 0 20px;
    border-bottom: 1px solid var(--art-gray-200);

    .task-count-badge {
      display: inline-flex;
      align-items: center;
      justify-content: center;
      min-width: 16px;
      min-height: 16px;
      font-size: 11px;
      font-weight: 500;
      color: #fff;
      background-color: var(--el-color-primary);
      border-radius: 10px;
      margin-left: 2px;
    }
  }

  .task-empty {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: calc(100% - 50px);
  }

  .task-list {
    padding: 0 16px 16px;
    height: calc(100% - 50px);
    overflow: hidden;
  }

  .task-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 10px 14px;
    margin-top: 8px;
    background-color: var(--art-gray-100);
    border: 1px solid var(--art-gray-200);
    border-radius: calc(var(--custom-radius, 8px) + 2px);
    transition: all 0.2s ease;

    &:hover {
      background-color: var(--art-gray-200);
      border-color: var(--art-gray-300);
    }

    &.task-item-error {
      background-color: rgba(245, 108, 108, 0.08);
      border-color: rgba(245, 108, 108, 0.25);

      .task-icon {
        background-color: rgba(245, 108, 108, 0.12);
        color: #f56c6c;
      }
    }

    &.task-item-success {
      background-color: rgba(103, 194, 58, 0.08);
      border-color: rgba(103, 194, 58, 0.25);

      .task-icon {
        background-color: rgba(103, 194, 58, 0.12);
        color: #67c23a;
      }
    }

    &.task-item-paused {
      .task-icon {
        background-color: rgba(230, 162, 60, 0.12);
        color: #e6a23c;
      }
    }
  }

  .task-icon {
    display: flex;
    align-items: center;
    justify-content: center;
    flex-shrink: 0;
    width: 40px;
    height: 40px;
    background-color: rgba(64, 158, 255, 0.12);
    color: #409eff;
    border-radius: 10px;

    &.icon-error {
      background-color: rgba(245, 108, 108, 0.12);
      color: #f56c6c;
    }

    &.icon-success {
      background-color: rgba(103, 194, 58, 0.12);
      color: #67c23a;
    }

    &.icon-paused {
      background-color: rgba(230, 162, 60, 0.12);
      color: #e6a23c;
    }
  }

  .task-info {
    flex: 1;
    min-width: 0;
    padding-right: 8px;

    .task-name {
      font-size: 13px;
      font-weight: 500;
      color: var(--art-gray-800);
    }

    .task-percent {
      font-size: 12px;
      font-weight: 500;
      color: var(--art-gray-600);
    }

    .task-progress {
      margin-top: 8px;
      padding-right: 60px;

      .el-progress {
        .el-progress-bar__outer {
          background-color: var(--art-gray-200) !important;
        }
      }
    }

    .task-meta {
      display: flex;
      align-items: center;
      gap: 6px;
      margin-top: 6px;
      font-size: 12px;
      color: var(--art-gray-600);

      .text-success {
        color: #67c23a;
      }

      .text-danger {
        color: #f56c6c;
      }
    }

    .task-error-msg {
      display: flex;
      align-items: center;
      margin-top: 6px;
      font-size: 12px;
      color: #f56c6c;
    }
  }

  .task-actions {
    display: flex;
    align-items: center;
    gap: 4px;
    transition: opacity 0.2s ease;
    flex-shrink: 0;

    .el-button {
      padding: 0;
      display: flex;
      align-items: center;
      justify-content: center;
    }
  }
  .toolbar {
    background: var(--el-bg-color);
    border-radius: 8px 8px 0 0;
  }
</style>
