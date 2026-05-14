<template>
  <div class="export-monitoring-page">
    <!-- 顶部导航栏 -->
    <div class="monitoring-header">
      <div class="header-left">
        <ElButton text @click="handleBack">
          <LfpSvgIcon icon="ri:arrow-left-line" class="mr-1" />
          调度中心
        </ElButton>
        <span class="header-separator">|</span>
        <LfpSvgIcon icon="ri:download-2-line" class="text-lg text-warning mr-2" />
        <span class="task-name">导出任务: #{{ taskId }} ({{ taskName }})</span>
        <ElTag :type="statusConfig.type" effect="dark" class="ml-3">
          {{ statusConfig.label }}
        </ElTag>
      </div>
      <div class="header-right">
        <ElButton type="danger" @click="handleTerminate" v-if="taskStatus === 'running'">
          <LfpSvgIcon icon="ri:stop-circle-line" class="mr-1" />
          强制终止
        </ElButton>
      </div>
    </div>

    <!-- 导出配置概览 -->
    <div class="config-section lfp-card p-4 mb-4">
      <div class="section-header mb-3">
        <LfpSvgIcon icon="ri:settings-3-line" class="text-base text-primary mr-2" />
        <span>导出配置</span>
      </div>
      <div class="config-grid">
        <div class="config-item">
          <label>源模型</label>
          <span class="config-value">{{ exportConfig.base_model || '-' }}</span>
        </div>
        <div class="config-item">
          <label>检查点</label>
          <span class="config-value">{{ exportConfig.adapter_path || '-' }}</span>
        </div>
        <div class="config-item">
          <label>导出格式</label>
          <span class="config-value">{{ exportConfig.export_format?.toUpperCase() || 'GGUF' }}</span>
        </div>
        <div class="config-item">
          <label>量化方法</label>
          <span class="config-value">{{ exportConfig.quantization_method?.toUpperCase() || 'Q4_K_M' }}</span>
        </div>
        <div class="config-item" v-if="exportConfig.export_path">
          <label>输出路径</label>
          <span class="config-value export-path">{{ exportConfig.export_path }}</span>
        </div>
      </div>
    </div>

    <!-- 进度条（running 时显示） -->
    <div class="progress-section lfp-card p-4 mb-4" v-if="taskStatus === 'running' || taskStatus === 'pending'">
      <div class="flex items-center justify-between mb-2">
        <span class="progress-stage">
          <LfpSvgIcon v-if="taskStatus === 'running'" icon="ri:loader-2-line" class="animate-spin mr-2" />
          {{ currentStage }}
        </span>
        <span class="progress-pct">{{ Math.round(displayProgress * 100) }}%</span>
      </div>
      <ElProgress :percentage="Math.round(displayProgress * 100)" :stroke-width="16" :show-text="false" />
      <div v-if="currentMessage" class="progress-message">{{ currentMessage }}</div>
    </div>

    <!-- 完成后产物信息 -->
    <div class="complete-section lfp-card p-4 mb-4" v-if="taskStatus === 'done'">
      <div class="complete-content">
        <LfpSvgIcon icon="ri:checkbox-circle-line" class="text-4xl text-success mb-3" />
        <h3 class="mb-2">导出完成</h3>
        <p class="text-g-600" v-if="exportConfig.export_path">产物路径: {{ exportConfig.export_path }}</p>
        <p class="text-g-600" v-if="fileSize">文件大小: {{ formatFileSize(fileSize) }}</p>
        <ElButton type="primary" class="mt-3" @click="handleDownload">
          <LfpSvgIcon icon="ri:download-2-line" class="mr-1" />
          下载模型
        </ElButton>
      </div>
    </div>

    <!-- 终端日志 -->
    <div class="terminal-section">
      <Terminal :logs="terminalLogs" v-model:auto-scroll="autoScroll" />
    </div>
  </div>
</template>

<script setup lang="ts">
  import { computed, onMounted, onBeforeUnmount, ref, watch } from 'vue'
  import { useRoute, useRouter } from 'vue-router'
  import { ElMessage } from 'element-plus'
  import LfpSvgIcon from '@/components/core/base/lfp-svg-icon/index.vue'
  import Terminal from '@/components/business/task-dispatch/modules/task-monitoring/terminal.vue'
  import { useWebSocketTask } from '@/hooks/core/useWebSocketTask'
  import { getTask } from '@/api/task'
  import { getExportLog, terminateExport, type ExportLogResponse } from '@/api/llamafactory'
  import { TASK_STATUS_CONFIG } from '@/mock/modules/task-dispatch'

  defineOptions({ name: 'ExportMonitoringPage' })

  const route = useRoute()
  const router = useRouter()

  const taskId = computed(() => Number(route.params.id))
  const taskName = ref('')
  const taskStatus = ref<'running' | 'pending' | 'done' | 'failed' | 'cancelled'>('pending')
  const exportConfig = ref<Record<string, any>>({})
  const fileSize = ref(0)
  const currentStage = ref('准备中')
  const currentMessage = ref('')
  const displayProgress = ref(0)
  const terminalLogs = ref<any[]>([])
  const autoScroll = ref(true)

  const statusConfig = computed(() => {
    return TASK_STATUS_CONFIG[taskStatus.value] || TASK_STATUS_CONFIG.pending
  })

  const wsHook = useWebSocketTask('')
  const { connect: wsConnect, disconnect: wsDisconnect, trainingProgress } = wsHook

  watch(trainingProgress, (data) => {
    if (!data) return
    taskStatus.value = (data.status as any) || taskStatus.value
    currentStage.value = data.stage || currentStage.value
    currentMessage.value = data.message || ''
    displayProgress.value = data.progress ?? displayProgress.value
    if (data.export_path) {
      exportConfig.value.export_path = data.export_path
    }
    if (data.file_size) {
      fileSize.value = data.file_size
    }
  })

  async function loadTask() {
    try {
      const resp = await getTask(taskId.value)
      if (resp.task) {
        taskName.value = resp.task.task_name
        taskStatus.value = resp.task.status as any
        try {
          const cfg = JSON.parse(resp.task.config || '{}')
          exportConfig.value = cfg
          if (cfg.job_id) {
            wsHook.jobId.value = cfg.job_id
          }
        } catch {
          // ignore
        }
      }
    } catch {
      ElMessage.error('加载任务失败')
    }
  }

  async function loadLogs() {
    const resp: ExportLogResponse = await getExportLog(taskId.value)
    if (resp.lines) {
      terminalLogs.value = resp.lines.map((line: string) => ({
        time: '',
        level: parseLevel(line),
        message: line
      }))
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

  async function handleTerminate() {
    try {
      const resp = await terminateExport(taskId.value)
      if (resp.success) {
        ElMessage.success('导出任务已终止')
        taskStatus.value = 'cancelled'
      } else {
        ElMessage.error(resp.message || '终止失败')
      }
    } catch {
      ElMessage.error('终止请求失败')
    }
  }

  function handleDownload() {
    const path = exportConfig.value.export_path
    if (!path) {
      ElMessage.warning('未找到导出产物路径')
      return
    }
    window.open(`/api/llamafactory/export/${taskId.value}/download`)
  }

  function formatFileSize(bytes: number): string {
    if (bytes < 1024 * 1024) return `${(bytes / 1024).toFixed(1)} KB`
    if (bytes < 1024 * 1024 * 1024) return `${(bytes / 1024 / 1024).toFixed(1)} MB`
    return `${(bytes / 1024 / 1024 / 1024).toFixed(2)} GB`
  }

  function handleBack() {
    router.push('/workbench/task-dispatch')
  }

  onMounted(async () => {
    await loadTask()
    await loadLogs()
    if (wsHook.jobId.value) {
      wsConnect()
    }
  })

  onBeforeUnmount(() => {
    wsDisconnect()
  })
</script>

<style lang="scss" scoped>
  .export-monitoring-page {
    height: 100%;
    display: flex;
    flex-direction: column;
    padding: 16px 20px;
    min-height: 0;
    gap: 12px;
    overflow: hidden;
  }

  .monitoring-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 12px 16px;
    background: #fff;
    border-radius: var(--custom-radius, 8px);
    border: 1px solid var(--lfp-gray-200);

    .header-left {
      display: flex;
      align-items: center;
    }

    .header-separator {
      margin: 0 12px;
      color: var(--lfp-gray-300);
    }

    .task-name {
      font-size: 14px;
      font-weight: 600;
      color: var(--lfp-gray-700);
    }
  }

  .config-section {
    .config-grid {
      display: grid;
      grid-template-columns: repeat(auto-fill, minmax(200px, 1fr));
      gap: 12px;

      .config-item {
        display: flex;
        flex-direction: column;
        gap: 4px;

        label {
          font-size: 12px;
          color: var(--lfp-gray-500);
        }

        .config-value {
          font-size: 14px;
          font-weight: 500;
          color: var(--lfp-gray-800);

          &.export-path {
            font-family: 'Consolas', 'Monaco', monospace;
            font-size: 12px;
            word-break: break-all;
          }
        }
      }
    }
  }

  .progress-section {
    .progress-stage {
      display: flex;
      align-items: center;
      font-size: 14px;
      font-weight: 500;
      color: var(--lfp-gray-700);
    }

    .progress-pct {
      font-size: 14px;
      font-weight: 600;
      color: var(--el-color-primary);
    }

    .progress-message {
      margin-top: 8px;
      font-size: 12px;
      color: var(--lfp-gray-500);
    }
  }

  .complete-section {
    .complete-content {
      display: flex;
      flex-direction: column;
      align-items: center;
      text-align: center;

      h3 {
        font-size: 1.1rem;
        font-weight: 600;
        margin: 0 0 4px;
      }

      p {
        margin: 4px 0;
        font-size: 13px;
        color: var(--lfp-gray-600);
      }
    }
  }

  .terminal-section {
    flex: 1;
    min-height: 0;
    border-radius: var(--custom-radius, 8px);
    overflow: hidden;
  }

  .animate-spin {
    animation: spin 1s linear infinite;
  }

  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }
</style>