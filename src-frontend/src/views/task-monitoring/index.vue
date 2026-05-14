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

    <!-- 训练任务：使用原有训练布局 -->
    <template v-else-if="taskType === 'training'">
      <!-- 顶部导航栏 -->
      <div class="monitoring-header">
        <div class="header-left">
          <ElButton text @click="handleBack">
            <LfpSvgIcon icon="ri:arrow-left-line" class="mr-1" />
            调度中心
          </ElButton>
          <span class="header-separator">|</span>
          <LfpSvgIcon icon="ri:brain-line" class="text-lg text-primary mr-2" />
          <span class="task-name">任务: #{{ taskId }} ({{ displayData.name }})</span>
          <ElTag :type="statusConfig.type" effect="dark" class="ml-3">
            {{ statusConfig.label }}
          </ElTag>
        </div>
        <div class="header-right">
          <ElButton type="danger" @click="handleForceTerminate">
            <LfpSvgIcon icon="ri:stop-circle-line" class="mr-1" />
            强制终止
          </ElButton>
        </div>
      </div>

      <!-- 进度条 -->
      <div class="progress-section">
        <div class="progress-bar-container">
          <ElProgress :percentage="displayData.progress" :stroke-width="16" :show-text="false" />
        </div>
        <div class="progress-info">
          <span class="progress-text">
            Step {{ displayData.currentStep }} / {{ displayData.totalSteps }} ({{ displayData.progress }}%)
          </span>
          <span class="progress-time">
            <LfpSvgIcon icon="ri:time-line" class="mr-1" />
            已用时间: {{ displayData.elapsedTime }}
          </span>
        </div>
      </div>

      <!-- 中部区域：训练指标 + 终端日志 -->
      <div class="main-content">
        <!-- 左侧：训练指标 -->
        <div class="metrics-section">
          <div class="section-header">
            <LfpSvgIcon icon="ri:line-chart-line" class="text-base text-primary mr-2" />
            <span>训练指标 (Metrics)</span>
            <div class="metrics-stats ml-auto">
              <span class="stat-item">
                <LfpSvgIcon icon="ri:flask-line" class="mr-1" />
                LR: {{ displayData.learningRateValue ?? '-' }}
              </span>
              <span class="stat-item">
                <LfpSvgIcon icon="ri:speed-line" class="mr-1" />
                Loss: {{ displayData.loss ?? '-' }}
              </span>
              <span class="stat-item">
                <LfpSvgIcon icon="ri:memory-device-line" class="mr-1" />
                Eval Loss: {{ displayData.evalLoss ?? '-' }}
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

      <!-- 底部区域：参数快照 + GPU 监控 + 检查点 -->
      <div class="bottom-content">
        <div class="config-section">
          <ConfigSnapshot :config="displayData" />
        </div>
        <!-- GPU 显存监控 -->
        <div class="gpu-section" v-if="gpuStats">
          <div class="section-header">
            <LfpSvgIcon icon="ri:cpu-line" class="text-base text-primary mr-2" />
            <span>GPU 监控</span>
          </div>
          <div class="gpu-cards">
            <div class="gpu-card">
              <div class="gpu-card__label">显存使用</div>
              <div class="gpu-card__value">{{ gpuStats.used }} / {{ gpuStats.total }}</div>
              <ElProgress :percentage="gpuStats.percent" :stroke-width="8" :show-text="true" />
            </div>
            <div class="gpu-card">
              <div class="gpu-card__label">GPU 温度</div>
              <div class="gpu-card__value">{{ gpuStats.temperature != null ? gpuStats.temperature + '°C' : '-' }}</div>
            </div>
          </div>
        </div>
        <div class="checkpoint-section">
          <CheckpointTable :checkpoints="checkpoints" />
        </div>
      </div>
    </template>

    <!-- 清洗/导出任务：不支持在此页面查看 -->
    <template v-else>
      <div class="unsupported-task">
        <div class="unsupported-task__icon">
          <span class="ri:error-warning-line text-5xl text-warning"></span>
        </div>
        <h2 class="unsupported-task__title">此页面不支持查看该任务类型</h2>
        <p class="unsupported-task__desc">
          当前页面仅支持查看
          <strong>训练任务</strong>详情。
        </p>
        <p class="unsupported-task__desc">
          <template v-if="taskType === 'cleaning'"
            >请前往 <strong>清洗监控页面</strong> 查看。</template
          >
          <template v-else-if="taskType === 'export'">格式导出任务详情暂未开放。</template>
          <template v-else>任务类型：{{ taskType }}</template>
        </p>
        <ElButton type="primary" @click="handleBack">
          <span class="ri:arrow-left-line mr-1"></span>返回任务调度中心
        </ElButton>
      </div>
    </template>
  </div>
</template>

<script setup lang="ts">
  import LfpSvgIcon from '@/components/core/base/lfp-svg-icon/index.vue'
  import ExecutionPanel from '@/components/business/execution-panel.vue'
  import LossChart from '@/components/business/task-dispatch/modules/task-monitoring/loss-chart.vue'
  import Terminal from '@/components/business/task-dispatch/modules/task-monitoring/terminal.vue'
  import ConfigSnapshot from '@/components/business/task-dispatch/modules/task-monitoring/config-snapshot.vue'
  import CheckpointTable from '@/components/business/task-dispatch/modules/task-monitoring/checkpoint-table.vue'
  import { ElMessage, ElMessageBox } from 'element-plus'
  import { TASK_STATUS_CONFIG } from '@/mock/modules/task-dispatch'
  import { getTask as fetchTask, terminateTask, type TaskItem as ApiTask } from '@/api/task'
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
      learningRateValue: null as string | null,
      throughput: null as string | null,
      memoryUsage: null as string | null,
      loss: null as string | null,
      evalLoss: null as string | null,
      config: t.config
    }
  })

  // 先声明 WebSocket hook（trainingProgress 在此处可用）
  const wsHook = useWebSocketTask('')
  const { connect: wsConnect, disconnect: wsDisconnect, lossHistory, trainingProgress } = wsHook

  /** GPU 显存监控数据，从 WebSocket 实时推送获取 */
  const gpuStats = computed(() => {
    const p = trainingProgress.value
    if (!p?.gpu?.length) return null
    const g = p.gpu[0]
    const used = g?.used_memory_mb ?? 0
    const total = g?.total_memory_mb ?? 0
    const pct = total > 0 ? Math.round((used / total) * 100) : 0
    return {
      used: (used / 1024).toFixed(1) + ' GB',
      total: (total / 1024).toFixed(1) + ' GB',
      percent: pct,
      temperature: g?.temperature ?? null
    }
  })

  /** 实时进度数据 */
  const liveProgress = computed(() => {
    const p = trainingProgress.value
    const t = taskData.value
    if (!p || !t) return null
    const current = p.current_step ?? 0
    const total = p.total_steps ?? 10
    const pct = p.progress ?? 0
    return {
      currentStep: current,
      totalSteps: total,
      progress: Math.round(pct * 100),
      elapsedTime: t.elapsedTime,
      loss: p.loss != null ? (p.loss as number).toFixed(4) : null,
      evalLoss: p.eval_loss != null ? (p.eval_loss as number).toFixed(4) : null,
      learningRate: p.learning_rate != null ? (p.learning_rate as number).toExponential(2) : null,
    }
  })

  /** 合并后的展示数据：WebSocket 实时数据优先覆盖静态 API 数据 */
  const displayData = computed(() => {
    const base = taskData.value
    if (!base) return null
    const live = liveProgress.value
    if (!live) return base
    return {
      ...base,
      progress: live.progress,
      currentStep: live.currentStep,
      totalSteps: live.totalSteps,
      loss: live.loss,
      evalLoss: live.evalLoss,
      learningRateValue: live.learningRate,
    }
  })

  const statusConfig = computed(() => {
    const status = displayData.value?.status || 'pending'
    return TASK_STATUS_CONFIG[status] || TASK_STATUS_CONFIG.pending
  })

  /** Loss 曲线数据，从 WebSocket 实时累积 */
  const lossChartData = computed(() => lossHistory.value)

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
      const resp = await fetch(`/api/tasks/${taskId.value}/training-log`)
      const data = await resp.json()
      if (data.lines) {
        terminalLogs.value = data.lines.map((line: string) => ({
          time: '',
          level: parseLevel(line),
          message: line
        }))
      } else if (data.error) {
        terminalLogs.value = [
          {
            time: '',
            level: 'WARN',
            message: data.error
          }
        ]
      }
    } catch {
      terminalLogs.value = [
        {
          time: '',
          level: 'WARN',
          message: '无法加载训练日志'
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

  /** WebSocket 推送训练完成/失败时，重新拉取任务数据刷新页面状态 */
  async function refreshTask() {
    const id = taskId.value
    if (isNaN(id)) return
    try {
      const resp = await fetchTask(id)
      if (resp.task) {
        rawTask.value = resp.task
      }
    } catch {
      // 静默失败，不影响用户
    }
  }

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

  watch(trainingProgress, (val) => {
    if (val?.status === 'done' || val?.status === 'failed') {
      refreshTask()
    }
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
          const resp = await terminateTask(id)
          if (resp.success) {
            ElMessage.success(resp.message || '任务已强制终止')
            await refreshTask()
          } else {
            ElMessage.error(resp.message || '终止失败')
            return
          }
        }
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
    border: 1px solid var(--lfp-gray-200);

    .header-left {
      display: flex;
      align-items: center;
      gap: 8px;

      .header-separator {
        color: var(--lfp-gray-400);
        margin: 0 8px;
      }

      .task-name {
        font-size: 14px;
        font-weight: 600;
        color: var(--lfp-gray-800);
      }
    }
  }

  .progress-section {
    padding: 16px 20px;
    background: var(--el-fill-color-lighter);
    border-radius: var(--custom-radius, 8px);
    border: 1px solid var(--lfp-gray-200);

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
        color: var(--lfp-gray-800);
      }

      .progress-time {
        font-size: 13px;
        color: var(--lfp-gray-600);
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
      border: 1px solid var(--lfp-gray-200);

      .section-header {
        display: flex;
        align-items: center;
        margin-bottom: 12px;
        font-size: 14px;
        font-weight: 600;
        color: var(--lfp-gray-800);

        .metrics-stats {
          display: flex;
          gap: 16px;

          .stat-item {
            display: flex;
            align-items: center;
            font-size: 12px;
            font-weight: 400;
            color: var(--lfp-gray-600);
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
    grid-template-columns: 1fr 1fr 1fr;
    gap: 16px;
    min-height: 280px;

    .config-section,
    .checkpoint-section {
      min-height: 280px;
    }

    .gpu-section {
      display: flex;
      flex-direction: column;
      padding: 16px;
      background: var(--el-fill-color-lighter);
      border-radius: var(--custom-radius, 8px);
      border: 1px solid var(--lfp-gray-200);

      .section-header {
        display: flex;
        align-items: center;
        margin-bottom: 12px;
        font-size: 14px;
        font-weight: 600;
        color: var(--lfp-gray-800);
      }

      .gpu-cards {
        display: flex;
        flex-direction: column;
        gap: 16px;

        .gpu-card {
          &__label {
            font-size: 12px;
            color: var(--lfp-gray-500);
            margin-bottom: 4px;
          }

          &__value {
            font-size: 16px;
            font-weight: 600;
            color: var(--lfp-gray-800);
            margin-bottom: 8px;
          }
        }
      }
    }
  }

  .unsupported-task {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    height: 100%;
    min-height: 400px;
    padding: 40px;
    text-align: center;

    &__icon {
      margin-bottom: 24px;
    }

    &__title {
      font-size: 20px;
      font-weight: 600;
      color: var(--lfp-gray-800);
      margin: 0 0 12px;
    }

    &__desc {
      font-size: 14px;
      color: var(--lfp-gray-600);
      margin: 0 0 8px;
    }
  }
</style>
