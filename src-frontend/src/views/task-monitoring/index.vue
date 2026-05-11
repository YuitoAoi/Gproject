<template>
  <div class="task-monitoring-page">
    <!-- 上传任务：使用 ExecutionPanel -->
    <template v-if="taskType === 'upload'">
      <ExecutionPanel
        :task="executionTask"
        :task-name="rawTask?.task_name"
        :task-id="String(taskId)"
        :logs="terminalLogs"
        :show-return-button="true"
        @return-pool="handleBack"
      />
    </template>

    <!-- 训练/清洗任务：使用原有布局 -->
    <template v-else>
      <!-- 顶部导航栏 -->
      <div class="monitoring-header">
        <div class="header-left">
          <ElButton text @click="handleBack">
            <ArtSvgIcon icon="ri:arrow-left-line" class="mr-1" />
            调度中心
          </ElButton>
          <span class="header-separator">|</span>
          <ArtSvgIcon icon="ri:brain-line" class="text-lg text-primary mr-2" />
          <span class="task-name">任务: #{{ taskId }} ({{ taskData.name }})</span>
          <ElTag :type="statusConfig.type" effect="dark" class="ml-3">
            {{ statusConfig.label }}
          </ElTag>
        </div>
        <div class="header-right">
          <ElButton type="danger" @click="handleForceTerminate">
            <ArtSvgIcon icon="ri:stop-circle-line" class="mr-1" />
            强制终止
          </ElButton>
        </div>
      </div>

      <!-- 进度条 -->
      <div class="progress-section">
        <div class="progress-bar-container">
          <ElProgress :percentage="taskData.progress" :stroke-width="16" :show-text="false" />
        </div>
        <div class="progress-info">
          <span class="progress-text">
            Step {{ taskData.currentStep }} / {{ taskData.totalSteps }} ({{ taskData.progress }}%)
          </span>
          <span class="progress-time">
            <ArtSvgIcon icon="ri:time-line" class="mr-1" />
            已用时间: {{ taskData.elapsedTime }}
          </span>
        </div>
      </div>

      <!-- 中部区域：训练指标 + 终端日志 -->
      <div class="main-content">
        <!-- 左侧：训练指标 -->
        <div class="metrics-section">
          <div class="section-header">
            <ArtSvgIcon icon="ri:line-chart-line" class="text-base text-primary mr-2" />
            <span>训练指标 (Metrics)</span>
            <div class="metrics-stats ml-auto">
              <span class="stat-item">
                <ArtSvgIcon icon="ri:flask-line" class="mr-1" />
                LR: {{ taskData.learningRateValue }}
              </span>
              <span class="stat-item">
                <ArtSvgIcon icon="ri:speed-line" class="mr-1" />
                吞吐: {{ taskData.throughput }}
              </span>
              <span class="stat-item">
                <ArtSvgIcon icon="ri:memory-device-line" class="mr-1" />
                分配显存: {{ taskData.memoryUsage }}
              </span>
            </div>
          </div>
          <div class="metrics-chart">
            <LossChart :data="lossChartData" />
          </div>
        </div>

        <!-- 右侧：终端日志 -->
        <div class="terminal-section">
          <Terminal :logs="terminalLogs" v-model:auto-scroll="autoScroll" />
        </div>
      </div>

      <!-- 底部区域：参数快照 + 检查点 -->
      <div class="bottom-content">
        <div class="config-section">
          <ConfigSnapshot :config="taskData" />
        </div>
        <div class="checkpoint-section">
          <CheckpointTable :checkpoints="checkpoints" />
        </div>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import ExecutionPanel from '@/components/business/execution-panel.vue'
  import LossChart from '@/components/business/task-dispatch/modules/task-monitoring/loss-chart.vue'
  import Terminal from '@/components/business/task-dispatch/modules/task-monitoring/terminal.vue'
  import ConfigSnapshot from '@/components/business/task-dispatch/modules/task-monitoring/config-snapshot.vue'
  import CheckpointTable from '@/components/business/task-dispatch/modules/task-monitoring/checkpoint-table.vue'
  import { ElMessage, ElMessageBox } from 'element-plus'
  import { TASK_STATUS_CONFIG } from '@/mock/modules/task-dispatch'
  import { getTask as fetchTask, deleteTask, type TaskItem as ApiTask } from '@/api/task'
  import { getDatasetLogs } from '@/api/dataset'
  import { useWebSocketTask } from '@/hooks/core/useWebSocketTask'

  defineOptions({ name: 'TaskMonitoringPage' })

  const route = useRoute()
  const router = useRouter()

  const taskType = computed(() => (route.query.type as string) || 'training')

  const rawTask = ref<ApiTask | null>(null)
  const taskIdParam = computed(() => route.params.id as string)
  const taskId = computed(() => Number(taskIdParam.value))

  const terminalLogs = ref<any[]>([])
  const checkpoints = ref<any[]>([])
  const lossChartData = ref<any[]>([])
  const autoScroll = ref(true)

  const executionTask = computed(() => {
    if (!rawTask.value) return null
    const t = rawTask.value
    return {
      status:
        t.status === 'done'
          ? 'completed'
          : t.status === 'failed'
            ? 'failed'
            : t.status === 'running'
              ? 'running'
              : 'pending',
      progress: t.progress,
      eta: undefined
    }
  })

  const taskData = computed(() => {
    const t = rawTask.value
    if (!t) return null
    const elapsed = Math.round((Date.now() - new Date(t.created_at).getTime()) / 1000)
    const min = Math.floor(elapsed / 60)
    const sec = elapsed % 60
    const mappedStatus =
      t.status === 'done'
        ? 'completed'
        : t.status === 'failed'
          ? 'failed'
          : t.status === 'running'
            ? 'running'
            : 'pending'
    return {
      id: String(t.id),
      name: t.task_name,
      status: mappedStatus,
      progress: Math.round(t.progress * 100),
      currentStep: Math.round(t.progress * 10) || 1,
      totalSteps: 10,
      elapsedTime: min > 0 ? `${min}m${sec}s` : `${sec}s`,
      learningRateValue: null,
      throughput: null,
      memoryUsage: null,
      config: t.config
    }
  })

  const statusConfig = computed(() => {
    const status = taskData.value?.status || 'pending'
    return TASK_STATUS_CONFIG[status] || TASK_STATUS_CONFIG.pending
  })

  async function loadLogs() {
    const t = rawTask.value
    if (!t) return
    let jobId = ''
    try {
      const cfg = JSON.parse(t.config || '{}')
      jobId = cfg.job_id || ''
    } catch {
      return
    }
    if (!jobId) return
    try {
      const resp = await getDatasetLogs(jobId)
      if (resp.lines) {
        terminalLogs.value = resp.lines.map((line) => ({
          time: new Date().toLocaleTimeString('zh-CN', { hour12: false }),
          level: parseLevel(line),
          message: line
        }))
      } else if (resp.error) {
        terminalLogs.value = [
          {
            time: '',
            level: 'WARN',
            message: resp.error
          }
        ]
      }
    } catch {
      terminalLogs.value = [
        {
          time: '',
          level: 'WARN',
          message: '无法加载日志'
        }
      ]
    }
  }

  function parseLevel(line: string): string {
    const match = line.match(/\] (DEBUG|INFO|WARNING|ERROR|CRITICAL) \[/)
    if (match) {
      if (match[1] === 'WARNING') return 'WARN'
      if (match[1] === 'CRITICAL') return 'ERROR'
      return match[1]
    }
    return 'INFO'
  }

  const wsHook = useWebSocketTask('')
  const { connect: wsConnect, disconnect: wsDisconnect } = wsHook

  onMounted(async () => {
    const id = taskId.value
    if (isNaN(id)) {
      ElMessage.error('无效的任务ID')
      router.push('/workbench/task-dispatch')
      return
    }

    try {
      const resp = await fetchTask(id)
      if (!resp.task) {
        ElMessage.error('任务不存在')
        router.push('/workbench/task-dispatch')
        return
      }
      rawTask.value = resp.task

      await loadLogs()

      if (resp.task.status === 'running' || resp.task.status === 'pending') {
        const cfg = JSON.parse(resp.task.config || '{}')
        if (cfg.job_id) {
          wsHook.jobId.value = cfg.job_id
          wsConnect()
        }
      }
    } catch {
      ElMessage.error('加载任务详情失败')
      router.push('/workbench/task-dispatch')
    }
  })

  onBeforeUnmount(() => {
    wsDisconnect()
  })

  const handleBack = () => {
    router.push('/workbench/task-dispatch')
  }

  const handleForceTerminate = () => {
    ElMessageBox.confirm(
      `确定要强制终止任务 #${taskIdParam.value} 吗？此操作不可恢复。`,
      '确认强制终止',
      {
        confirmButtonText: '确定终止',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
      .then(async () => {
        const id = taskId.value
        if (!isNaN(id)) {
          await deleteTask(id)
        }
        ElMessage.success('任务已强制终止')
        router.push('/workbench/task-dispatch')
      })
      .catch(() => {})
  }
</script>

<style lang="scss" scoped>
  .task-monitoring-page {
    display: flex;
    flex-direction: column;
    height: 100%;
    padding: 16px 20px;
    gap: 16px;
  }

  .monitoring-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    background: var(--el-fill-color-lighter);
    border-radius: var(--custom-radius, 8px);
    border: 1px solid var(--art-gray-200);

    .header-left {
      display: flex;
      align-items: center;
      gap: 8px;

      .header-separator {
        color: var(--art-gray-400);
        margin: 0 8px;
      }

      .task-name {
        font-size: 14px;
        font-weight: 600;
        color: var(--art-gray-800);
      }
    }
  }

  .progress-section {
    padding: 16px 20px;
    background: var(--el-fill-color-lighter);
    border-radius: var(--custom-radius, 8px);
    border: 1px solid var(--art-gray-200);

    .progress-bar-container {
      margin-bottom: 12px;
    }

    .progress-info {
      display: flex;
      justify-content: space-between;
      align-items: center;

      .progress-text {
        font-size: 14px;
        font-weight: 500;
        color: var(--art-gray-800);
      }

      .progress-time {
        font-size: 13px;
        color: var(--art-gray-600);
      }
    }
  }

  .main-content {
    display: grid;
    grid-template-columns: 3fr 2fr;
    gap: 16px;
    min-height: 320px;

    .metrics-section {
      display: flex;
      flex-direction: column;
      padding: 16px;
      background: var(--el-fill-color-lighter);
      border-radius: var(--custom-radius, 8px);
      border: 1px solid var(--art-gray-200);

      .section-header {
        display: flex;
        align-items: center;
        margin-bottom: 12px;
        font-size: 14px;
        font-weight: 600;
        color: var(--art-gray-800);

        .metrics-stats {
          display: flex;
          gap: 16px;

          .stat-item {
            display: flex;
            align-items: center;
            font-size: 12px;
            font-weight: 400;
            color: var(--art-gray-600);
          }
        }
      }

      .metrics-chart {
        flex: 1;
      }
    }

    .terminal-section {
      min-height: 280px;
    }
  }

  .bottom-content {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
    min-height: 280px;

    .config-section,
    .checkpoint-section {
      min-height: 280px;
    }
  }
</style>
