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

    <!-- 训练任务：使用原有训练布局（含自动导出阶段） -->
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
          <span class="task-name">任务: #{{ taskId }} ({{ displayData?.name }})</span>
          <ElTag :type="statusConfig.type" effect="dark" class="ml-3">
            {{ statusConfig.label }}
          </ElTag>
          <ElTag v-if="currentPhase === 'exporting'" type="warning" effect="dark" class="ml-2">
            导出中
          </ElTag>
          <ElTag v-else-if="currentPhase === 'export-done'" type="success" effect="dark" class="ml-2">
            训练+导出完成
          </ElTag>
        </div>
        <div class="header-right">
          <ElButton
            v-if="displayData?.status === 'running' || displayData?.status === 'pending'"
            type="danger"
            @click="handleForceTerminate"
          >
            <LfpSvgIcon icon="ri:stop-circle-line" class="mr-1" />
            强制终止
          </ElButton>
        </div>
      </div>

      <!-- ========== 训练阶段进度条 ========== -->
      <div v-if="currentPhase === 'training'" class="progress-section">
        <div class="progress-bar-container">
          <ElProgress :percentage="displayData?.progress ?? 0" :stroke-width="16" :show-text="false" />
        </div>
        <div class="progress-info">
          <span class="progress-text">
            Step {{ displayData?.currentStep ?? 0 }} / {{ displayData?.totalSteps ?? 0 }} ({{ displayData?.progress ?? 0 }}%)
          </span>
          <span class="progress-time">
            <LfpSvgIcon icon="ri:time-line" class="mr-1" />
            已用时间: {{ displayData?.elapsedTime ?? '-' }}
          </span>
        </div>
      </div>

      <!-- ========== 导出阶段进度条 ========== -->
      <div v-else-if="currentPhase === 'exporting'" class="progress-section">
        <div class="phase-stepper">
          <ElSteps :active="1" finish-status="success" simple class="export-stepper">
            <ElStep title="模型训练" status="finish" />
            <ElStep title="GGUF 导出" status="process" />
          </ElSteps>
        </div>
        <div class="progress-bar-container">
          <ElProgress :percentage="exportProgressPct" :stroke-width="16" :show-text="false" />
        </div>
        <div class="progress-info">
          <span class="progress-text">
            <LfpSvgIcon v-if="currentPhase === 'exporting'" icon="ri:loader-2-line" class="animate-spin mr-1" />
            {{ exportStage }}
          </span>
          <span class="progress-pct">{{ exportProgressPct }}%</span>
        </div>
        <div v-if="exportMessage" class="progress-message">{{ exportMessage }}</div>
      </div>

      <!-- ========== 导出完成摘要 ========== -->
      <div v-else-if="currentPhase === 'export-done'" class="progress-section">
        <div class="phase-stepper">
          <ElSteps :active="2" finish-status="success" simple class="export-stepper">
            <ElStep title="模型训练" status="finish" />
            <ElStep title="GGUF 导出" status="finish" />
          </ElSteps>
        </div>
        <div class="export-complete-banner">
          <LfpSvgIcon icon="ri:checkbox-circle-line" class="text-2xl text-success mr-2" />
          <span>训练与导出已完成</span>
          <span class="ml-auto text-sm text-g-500" v-if="exportInfo.size">
            文件大小: {{ formatFileSize(exportInfo.size) }}
          </span>
        </div>
      </div>

      <!-- ========== 中部区域：训练阶段 ========== -->
      <div v-if="currentPhase === 'training'" class="main-content">
        <div class="metrics-section">
          <div class="section-header">
            <LfpSvgIcon icon="ri:line-chart-line" class="text-base text-primary mr-2" />
            <span>训练指标 (Metrics)</span>
            <div class="metrics-stats ml-auto">
              <span class="stat-item">
                <LfpSvgIcon icon="ri:flask-line" class="mr-1" />
                LR: {{ displayData?.learningRateValue ?? '-' }}
              </span>
              <span class="stat-item">
                <LfpSvgIcon icon="ri:speed-line" class="mr-1" />
                Loss: {{ displayData?.loss ?? '-' }}
              </span>
              <span class="stat-item">
                <LfpSvgIcon icon="ri:memory-device-line" class="mr-1" />
                Eval Loss: {{ displayData?.evalLoss ?? '-' }}
              </span>
            </div>
          </div>
          <div class="metrics-chart">
            <LossChart :data="lossChartData" />
          </div>
        </div>
        <div class="terminal-section">
          <Terminal :logs="terminalLogs" v-model:auto-scroll="autoScroll" />
        </div>
      </div>

      <!-- ========== 中部区域：导出阶段 / 导出完成 ========== -->
      <div v-else class="main-content">
        <!-- 左侧：训练摘要 -->
        <div class="metrics-section">
          <div class="section-header">
            <LfpSvgIcon icon="ri:bar-chart-box-line" class="text-base text-primary mr-2" />
            <span>训练摘要</span>
          </div>
          <div class="training-summary">
            <div class="summary-item">
              <span class="summary-label">最终 Loss</span>
              <span class="summary-value">{{ displayData?.loss ?? '-' }}</span>
            </div>
            <div class="summary-item">
              <span class="summary-label">Eval Loss</span>
              <span class="summary-value">{{ displayData?.evalLoss ?? '-' }}</span>
            </div>
            <div class="summary-item">
              <span class="summary-label">学习率</span>
              <span class="summary-value">{{ displayData?.learningRateValue ?? '-' }}</span>
            </div>
            <div class="summary-item" v-if="currentPhase === 'export-done'">
              <span class="summary-label">导出路径</span>
              <span class="summary-value export-path-value">{{ exportInfo.path || '-' }}</span>
            </div>
            <div class="summary-item" v-if="currentPhase === 'export-done'">
              <span class="summary-label">文件大小</span>
              <span class="summary-value">{{ exportInfo.size ? formatFileSize(exportInfo.size) : '-' }}</span>
            </div>
            <div class="summary-actions" v-if="currentPhase === 'export-done' && exportInfo.path">
              <ElButton type="primary" @click="handleDownloadExport">
                <LfpSvgIcon icon="ri:download-2-line" class="mr-1" />
                下载模型
              </ElButton>
            </div>
          </div>
        </div>
        <div class="terminal-section">
          <Terminal :logs="exportTerminalLogs" v-model:auto-scroll="autoScroll" />
        </div>
      </div>

      <!-- ========== 底部区域 ========== -->
      <div class="bottom-content">
        <div class="config-section">
          <ConfigSnapshot :config="displayData" />
        </div>
        <div class="gpu-section" v-if="currentPhase === 'training' && gpuStats">
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
        <div class="checkpoint-section" v-if="currentPhase === 'training'">
          <CheckpointTable :checkpoints="checkpoints" :base-model="trainingBaseModel" />
        </div>
      </div>
    </template>

    <!-- 导出任务：跳转到独立的导出监控页面 -->
    <template v-else-if="taskType === 'export'">
      <div class="export-redirect">
        <div class="redirect-content">
          <LfpSvgIcon icon="ri:download-2-line" class="text-5xl text-warning mb-4" />
          <h2>格式导出任务</h2>
          <p class="text-g-500">正在跳转到导出监控页面...</p>
          <ElButton type="primary" @click="goToExportMonitor">
            <LfpSvgIcon icon="ri:arrow-right-line" class="mr-1" />
            前往导出监控
          </ElButton>
        </div>
      </div>
    </template>

    <!-- 清洗任务：跳转到清洗监控页面 -->
    <template v-else-if="taskType === 'cleaning'">
      <div class="export-redirect">
        <div class="redirect-content">
          <LfpSvgIcon icon="ri:cleaning-2-line" class="text-5xl text-primary mb-4" />
          <h2>数据清洗任务</h2>
          <p class="text-g-500">正在跳转到清洗监控页面...</p>
          <ElButton type="primary" @click="goToCleaningMonitor">
            <LfpSvgIcon icon="ri:arrow-right-line" class="mr-1" />
            前往清洗监控
          </ElButton>
        </div>
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
  import {
    getTask as fetchTask,
    terminateTask,
    getTrainingExportLog,
    type TaskItem as ApiTask,
  } from '@/api/task'
  import { getCheckpoints } from '@/api/llamafactory'
  import { useWebSocketTask } from '@/hooks/core/useWebSocketTask'

  defineOptions({ name: 'TaskMonitoringPage' })

  const route = useRoute()
  const router = useRouter()

  const taskType = computed(() => (route.query.type as string) || 'training')

  const rawTask = ref<ApiTask | null>(null)
  const taskIdParam = computed(() => route.params.id as string)
  const taskId = computed(() => Number(taskIdParam.value))

  const terminalLogs = ref<any[]>([])
  const exportTerminalLogs = ref<any[]>([])
  const checkpoints = ref<any[]>([])
  const trainingBaseModel = computed(() => {
    const t = rawTask.value
    if (!t) return ''
    try {
      const cfg = JSON.parse(t.config || '{}')
      return cfg.base_model || ''
    } catch {
      return ''
    }
  })

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

  // WebSocket hook
  const wsHook = useWebSocketTask('')
  const { connect: wsConnect, disconnect: wsDisconnect, lossHistory, trainingProgress } = wsHook

  /** 当前任务阶段：training / exporting / export-done */
  const currentPhase = computed(() => {
    // 优先从 WebSocket 实时数据判断
    const wsPhase = trainingProgress.value?.phase
    if (wsPhase === 'exporting') {
      // 导出阶段中
      if (trainingProgress.value?.status === 'done') return 'export-done'
      return 'exporting'
    }
    // 回退到 DB 数据判断（页面刷新场景）
    const task = rawTask.value
    if (task) {
      if (task.phase === 'exporting' && task.status === 'running') return 'exporting'
      if (task.status === 'done') {
        try {
          const cfg = JSON.parse(task.config || '{}')
          if (cfg.export_path) return 'export-done'
        } catch { /* ignore */ }
      }
    }
    return 'training'
  })

  /** 导出进度（0-100） */
  const exportProgressPct = computed(() => {
    const p = trainingProgress.value
    if (!p) return 0
    return Math.round((p.progress ?? 0) * 100)
  })

  /** 导出阶段文字 */
  const exportStage = computed(() => trainingProgress.value?.stage ?? '准备中')

  /** 导出阶段消息 */
  const exportMessage = computed(() => trainingProgress.value?.message ?? '')

  /** 导出产物信息 */
  const exportInfo = computed(() => {
    const p = trainingProgress.value
    const task = rawTask.value
    let path = p?.export_path ?? ''
    let size = p?.file_size ?? 0
    // 回退从 task config 读取
    if (!path && task) {
      try {
        const cfg = JSON.parse(task.config || '{}')
        path = cfg.export_path ?? ''
        size = cfg.export_file_size ?? 0
      } catch { /* ignore */ }
    }
    return { path, size }
  })

  /** GPU 显存监控数据 */
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

  /** 合并后的展示数据 */
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
        terminalLogs.value = [{ time: '', level: 'WARN', message: data.error }]
      }
    } catch {
      terminalLogs.value = [{ time: '', level: 'WARN', message: '无法加载训练日志' }]
    }
  }

  /** 加载导出日志 */
  async function loadExportLogs() {
    const id = taskId.value
    if (isNaN(id)) return
    try {
      const resp = await getTrainingExportLog(id)
      if (resp.lines) {
        exportTerminalLogs.value = resp.lines.map((line: string) => ({
          time: '',
          level: parseLevel(line),
          message: line
        }))
      } else if (resp.error) {
        exportTerminalLogs.value = [{ time: '', level: 'WARN', message: resp.error }]
      }
    } catch {
      exportTerminalLogs.value = [{ time: '', level: 'WARN', message: '无法加载导出日志' }]
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

  async function refreshTask() {
    const id = taskId.value
    if (isNaN(id)) return
    try {
      const resp = await fetchTask(id)
      if (resp.task) {
        rawTask.value = resp.task
      }
    } catch {
      // 静默失败
    }
  }

  async function loadCheckpoints() {
    const id = taskId.value
    if (isNaN(id)) return
    try {
      const resp = await getCheckpoints(id)
      if (resp.success && resp.checkpoints) {
        checkpoints.value = resp.checkpoints
      }
    } catch {
      // 静默失败
    }
  }

  function formatFileSize(bytes: number): string {
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`
    return `${(bytes / 1024 / 1024 / 1024).toFixed(2)} GB`
  }

  function handleDownloadExport() {
    const path = exportInfo.value.path
    if (!path) {
      ElMessage.warning('未找到导出产物路径')
      return
    }
    window.open(`/api/llamafactory/export/${taskId.value}/download`)
  }

  function goToExportMonitor() {
    router.push(`/workbench/export-monitoring/${taskId.value}`)
  }

  function goToCleaningMonitor() {
    router.push(`/workbench/cleaning-monitor/${taskId.value}`)
  }

  /** 监听阶段切换，自动加载导出日志 */
  watch(currentPhase, (phase) => {
    if (phase === 'exporting' || phase === 'export-done') {
      loadExportLogs()
    }
  })

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
      if (taskType.value === 'training') {
        await loadCheckpoints()
      }

      // 如果已处于导出阶段（刷新场景），加载导出日志
      if (currentPhase.value === 'exporting' || currentPhase.value === 'export-done') {
        await loadExportLogs()
      }

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
        display: flex;
        align-items: center;
        font-size: 14px;
        font-weight: 500;
        color: var(--lfp-gray-800);
      }

      .progress-time {
        font-size: 13px;
        color: var(--lfp-gray-600);
      }

      .progress-pct {
        font-size: 14px;
        font-weight: 600;
        color: var(--el-color-primary);
      }
    }

    .progress-message {
      margin-top: 8px;
      font-size: 12px;
      color: var(--lfp-gray-500);
      word-break: break-all;
    }
  }

  .phase-stepper {
    margin-bottom: 16px;

    .export-stepper {
      padding: 8px 16px;
    }
  }

  .export-complete-banner {
    display: flex;
    align-items: center;
    margin-top: 12px;
    padding: 12px 16px;
    background: var(--el-color-success-light-9);
    border-radius: var(--custom-radius, 8px);
    font-size: 14px;
    font-weight: 500;
    color: var(--el-color-success-dark-2);
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

      .training-summary {
        display: flex;
        flex-direction: column;
        gap: 12px;
        padding: 12px 0;

        .summary-item {
          display: flex;
          flex-direction: column;
          gap: 4px;

          .summary-label {
            font-size: 12px;
            color: var(--lfp-gray-500);
          }

          .summary-value {
            font-size: 16px;
            font-weight: 600;
            color: var(--lfp-gray-800);
            font-family: 'Consolas', 'Monaco', monospace;

            &.export-path-value {
              font-size: 12px;
              font-weight: 400;
              word-break: break-all;
            }
          }
        }

        .summary-actions {
          margin-top: 8px;
        }
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

  .export-redirect {
    display: flex;
    align-items: center;
    justify-content: center;
    height: 100%;
    min-height: 400px;

    .redirect-content {
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;

      h2 {
        font-size: 1.25rem;
        font-weight: 600;
        margin: 0 0 8px;
      }

      p {
        margin: 0 0 20px;
      }
    }
  }

  .animate-spin {
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
</style>
