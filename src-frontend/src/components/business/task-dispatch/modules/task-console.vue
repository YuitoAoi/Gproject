<template>
  <div class="task-console">
    <!-- 工具栏 -->
    <div
      class="toolbar flex items-center justify-between flex-wrap gap-3 px-5 py-3 border-b border-g-100"
    >
      <!-- 左侧：搜索筛选 -->
      <div class="flex items-center gap-2 flex-wrap">
        <ElInput
          v-model="searchKeyword"
          placeholder="搜索任务ID/名称..."
          class="!w-52"
          clearable
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <span class="ri:search-line text-g-400"></span>
          </template>
        </ElInput>
        <ElSelect v-model="filterType" placeholder="类型: 全部" class="!w-32" clearable>
          <ElOption label="文件上传" value="upload" />
          <ElOption label="指令微调" value="training" />
          <ElOption label="数据清洗" value="cleaning" />
          <ElOption label="格式导出" value="export" />
          <ElOption label="模型推理" value="inference" />
        </ElSelect>
        <ElSelect v-model="filterStatus" placeholder="状态: 全部" class="!w-32" clearable>
          <ElOption label="运行中" value="running" />
          <ElOption label="排队等待" value="pending" />
          <ElOption label="已完成" value="done" />
          <ElOption label="失败" value="failed" />
        </ElSelect>
        <ElButton type="primary" @click="handleSearch">
          <span class="ri:search-line mr-1"></span>查询
        </ElButton>
        <ElButton @click="handleReset"> <span class="ri:refresh-line mr-1"></span>重置 </ElButton>
      </div>

      <!-- 右侧：批量操作 -->
      <div class="flex items-center gap-2">
        <ElButton @click="handleBatchClear">
          <span class="ri:delete-bin-line mr-1"></span>批量清理历史记录
        </ElButton>
      </div>
    </div>

    <!-- 表格 -->
    <LfpTable
      :loading="loading"
      :data="filteredData"
      :columns="columns"
      :pagination="pagination"
      empty-height="400px"
      @selection-change="handleSelectionChange"
      @pagination:size-change="handleSizeChange"
      @pagination:current-change="handleCurrentChange"
    />

    <!-- 强制终止二次确认弹窗 -->
    <ElDialog v-model="terminateDialogVisible" title="确认强制终止" width="400px" append-to-body>
      <p>确定要强制终止任务「{{ currentTask?.name }}」吗？此操作不可恢复。</p>
      <template #footer>
        <ElButton @click="terminateDialogVisible = false">取消</ElButton>
        <ElButton type="danger" @click="confirmTerminate">确定终止</ElButton>
      </template>
    </ElDialog>

    <!-- 删除确认弹窗 -->
    <ElDialog v-model="deleteDialogVisible" title="确认删除" width="400px" append-to-body>
      <p>确定要删除任务「{{ currentTask?.name }}」吗？此操作不可恢复。</p>
      <template #footer>
        <ElButton @click="deleteDialogVisible = false">取消</ElButton>
        <ElButton type="danger" @click="confirmDelete">确定删除</ElButton>
      </template>
    </ElDialog>
  </div>
</template>

<script setup lang="ts">
  import LfpTable from '@/components/core/tables/lfp-table/index.vue'
  import LfpSvgIcon from '@/components/core/base/lfp-svg-icon/index.vue'
  import { ElMessageBox, ElMessage } from 'element-plus'
  import { TASK_STATUS_CONFIG, TASK_TYPE_CONFIG, type TaskItem } from '@/mock/modules/task-dispatch'
  import { getTasks, deleteTask, terminateTask, type TaskItem as ApiTask } from '@/api/task'
  import { mapTaskStatusForDisplay } from '@/utils/task'

  defineOptions({ name: 'TaskConsole' })

  const router = useRouter()

  const rawTasks = ref<ApiTask[]>([])
  const loading = ref(false)

  async function fetchTasks() {
    loading.value = true
    try {
      const resp = await getTasks()
      rawTasks.value = resp.items || []
    } finally {
      loading.value = false
    }
  }

  const allTaskItems = computed<TaskItem[]>(() =>
    rawTasks.value.map((t: ApiTask) => {
      const mappedStatus = mapTaskStatusForDisplay(t.status)
      const isFinished = ['done', 'failed', 'cancelled'].includes(mappedStatus)
      const endTime = isFinished ? new Date(t.updated_at).getTime() : Date.now()
      const elapsed = Math.round((endTime - new Date(t.created_at).getTime()) / 1000)
      const min = Math.floor(elapsed / 60)
      const sec = elapsed % 60
      return {
        id: String(t.id),
        name: t.task_name,
        type: (t.task_type as TaskItem['type']) || 'cleaning',
        typeLabel: TASK_TYPE_CONFIG[t.task_type]?.label || t.task_type,
        status: mappedStatus as TaskItem['status'],
        statusLabel: TASK_STATUS_CONFIG[mappedStatus]?.label || mappedStatus,
        elapsedTime: min > 0 ? `${min}m${sec}s` : `${sec}s`,
        progress: Math.round(t.progress * 100),
        gpuCount: 0,
        createdAt: t.created_at
      }
    })
  )

  const searchKeyword = ref('')
  const filterType = ref('')
  const filterStatus = ref('')
  const selectedRows = ref<TaskItem[]>([])
  const terminateDialogVisible = ref(false)
  const currentTask = ref<TaskItem | null>(null)
  const deleteDialogVisible = ref(false)

  const pagination = ref({
    current: 1,
    size: 10,
    total: 0
  })

  watchEffect(() => {
    pagination.value.total = allTaskItems.value.length
  })

  const filteredData = computed(() => {
    let result = allTaskItems.value

    if (searchKeyword.value) {
      const keyword = searchKeyword.value.toLowerCase()
      result = result.filter(
        (item) =>
          item.id.toLowerCase().includes(keyword) || item.name.toLowerCase().includes(keyword)
      )
    }

    if (filterType.value) {
      result = result.filter((item) => item.type === filterType.value)
    }

    if (filterStatus.value) {
      result = result.filter((item) => item.status === filterStatus.value)
    }

    return result
  })

  const columns = computed(() => [
    { type: 'selection', width: 50 },
    { type: 'index', width: 60, label: '#' },
    {
      prop: 'id',
      label: '任务 ID / 名称',
      minWidth: 200,
      formatter: (row: TaskItem) => {
        return h(
          'div',
          {
            class: 'task-name-cell'
          },
          [
            h(
              'span',
              {
                class: 'task-id text-g-500 font-mono text-xs'
              },
              `[${row.id}] `
            ),
            h(
              'span',
              {
                class: 'task-name font-medium cursor-pointer hover:text-primary',
                onClick: () => handleTaskClick(row)
              },
              row.name
            )
          ]
        )
      }
    },
    {
      prop: 'type',
      label: '类型/阶段',
      width: 140,
      formatter: (row: TaskItem) => {
        const config = TASK_TYPE_CONFIG[row.type] || {
          label: row.type,
          icon: 'ri:question-line',
          color: '#909399'
        }
        return h(
          'div',
          {
            class: 'flex items-center gap-1.5'
          },
          [
            h(LfpSvgIcon, {
              icon: config.icon,
              class: 'text-base',
              style: { color: config.color }
            }),
            h('span', { class: 'text-sm' }, config.label)
          ]
        )
      }
    },
    {
      prop: 'status',
      label: '状态',
      width: 120,
      formatter: (row: TaskItem) => {
        const config = TASK_STATUS_CONFIG[row.status]
        return h(
          'div',
          {
            class: 'flex items-center gap-1.5'
          },
          [
            h('span', {
              class: 'inline-block w-2 h-2 rounded-full',
              style: { backgroundColor: config.dot }
            }),
            h(
              'span',
              {
                class: 'text-sm',
                style: { color: config.color }
              },
              config.label
            )
          ]
        )
      }
    },
    {
      prop: 'elapsedTime',
      label: '已耗时',
      width: 100,
      formatter: (row: TaskItem) => {
        return h('span', { class: 'font-mono text-sm' }, row.elapsedTime)
      }
    },
    {
      prop: 'operation',
      label: '操作',
      width: 180,
      fixed: 'right',
      formatter: (row: TaskItem) => {
        const isRunning = row.status === 'running' || row.status === 'pending'
        return h('div', { class: 'flex gap-1' }, [
          h(
            ElButton,
            {
              size: 'small',
              type: isRunning ? 'danger' : 'info',
              text: false,
              disabled: row.status === 'done' || row.status === 'failed',
              onClick: () => handleTerminate(row)
            },
            () => '终止'
          ),
          h(
            ElButton,
            {
              size: 'small',
              type: 'primary',
              text: false,
              onClick: () => handleDelete(row)
            },
            () => '删除'
          )
        ])
      }
    }
  ])

  const handleSearch = () => {
    pagination.value.current = 1
  }

  const handleReset = () => {
    searchKeyword.value = ''
    filterType.value = ''
    filterStatus.value = ''
    pagination.value.current = 1
  }

  const handleSelectionChange = (selection: TaskItem[]) => {
    selectedRows.value = selection
  }

  const handleSizeChange = (val: number) => {
    pagination.value.size = val
    pagination.value.current = 1
  }

  const handleCurrentChange = (val: number) => {
    pagination.value.current = val
  }

  const handleTaskClick = (row: TaskItem) => {
    const type = row.type
    if (type === 'inference') {
      router.push('/model-inference')
    } else if (type === 'upload') {
      router.push('/data-management/dataset-hub')
    } else if (type === 'cleaning') {
      router.push(`/workbench/cleaning-monitor/${row.id}`)
    } else if (type === 'training') {
      router.push(`/workbench/task-monitoring/${row.id}?type=${type}`)
    } else if (type === 'export') {
      ElMessage.warning('格式导出任务详情页暂未开放')
    }
  }

  const handleTerminate = (row: TaskItem) => {
    currentTask.value = row
    terminateDialogVisible.value = true
  }

  const handleDelete = (row: TaskItem) => {
    currentTask.value = row
    deleteDialogVisible.value = true
  }

  const confirmDelete = async () => {
    if (!currentTask.value) return
    const id = Number(currentTask.value.id)
    try {
      await deleteTask(id)
      ElMessage.success(`任务「${currentTask.value?.name}」已删除`)
      deleteDialogVisible.value = false
      currentTask.value = null
      await fetchTasks()
    } catch {
      ElMessage.error('删除失败')
    }
  }

  const confirmTerminate = async () => {
    if (!currentTask.value) return
    const id = Number(currentTask.value.id)
    try {
      const resp = await terminateTask(id)
      if (resp.success) {
        ElMessage.success(resp.message || `任务「${currentTask.value?.name}」已强制终止`)
      } else {
        ElMessage.error(resp.message || '终止失败')
        return
      }
      terminateDialogVisible.value = false
      currentTask.value = null
      await fetchTasks()
    } catch {
      ElMessage.error('终止失败')
    }
  }

  const handleBatchClear = async () => {
    if (selectedRows.value.length === 0) {
      ElMessage.warning('请先选择要清理的任务')
      return
    }
    try {
      await ElMessageBox.confirm(
        `确定要清理选中的 ${selectedRows.value.length} 个历史任务吗？`,
        '批量清理',
        {
          confirmButtonText: '确定',
          cancelButtonText: '取消',
          type: 'warning'
        }
      )
      loading.value = true
      await Promise.all(
        selectedRows.value.map((row) => {
          const id = Number(row.id)
          if (!isNaN(id)) return deleteTask(id)
          return Promise.resolve()
        })
      )
      ElMessage.success('已清理完成')
      selectedRows.value = []
      await fetchTasks()
    } catch (e) {
      if (e !== 'cancel') ElMessage.error('清理失败')
    } finally {
      loading.value = false
    }
  }

  onMounted(() => {
    fetchTasks()
  })
</script>

<style lang="scss" scoped>
  .task-console {
    background: var(--el-bg-color);
    border-radius: var(--custom-radius, 8px);
    border: 1px solid var(--lfp-gray-200);
  }

  .toolbar {
    background: var(--el-fill-color-lighter);
    border-radius: var(--custom-radius, 8px) var(--custom-radius, 8px) 0 0;
  }

  :deep(.task-name-cell) {
    display: flex;
    align-items: center;
    gap: 4px;

    .task-id {
      color: var(--lfp-gray-500);
    }

    .task-name {
      color: var(--lfp-gray-800);

      &:hover {
        color: var(--el-color-primary);
      }
    }
  }
</style>
