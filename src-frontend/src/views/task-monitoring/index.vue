<template>
  <div class="task-monitoring-page">
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
  </div>
</template>

<script setup lang="ts">
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import LossChart from '@/components/business/task-dispatch/modules/task-monitoring/loss-chart.vue'
  import Terminal from '@/components/business/task-dispatch/modules/task-monitoring/terminal.vue'
  import ConfigSnapshot from '@/components/business/task-dispatch/modules/task-monitoring/config-snapshot.vue'
  import CheckpointTable from '@/components/business/task-dispatch/modules/task-monitoring/checkpoint-table.vue'
  import { ElMessage, ElMessageBox } from 'element-plus'
  import {
    taskDetailMockData,
    checkpointListMockData,
    lossChartMockData,
    TASK_STATUS_CONFIG
  } from '@/mock/modules/task-dispatch'

  defineOptions({ name: 'TaskMonitoringPage' })

  const route = useRoute()
  const router = useRouter()

  const taskId = computed(() => route.params.id as string)

  const taskData = ref({ ...taskDetailMockData })
  const checkpoints = ref([...checkpointListMockData])
  const lossChartData = ref([...lossChartMockData])
  const autoScroll = ref(true)

  const terminalLogs = ref([
    { timestamp: '14:20:00', level: 'INFO', message: 'Task ID: cln_9fa82b started.' },
    { timestamp: '14:20:01', level: 'INFO', message: 'Loading dataset from S3...' },
    { timestamp: '14:20:05', level: 'WARN', message: 'Chunk 1: Dropped 452 empty rows.' },
    { timestamp: '14:20:12', level: 'INFO', message: 'PII Masker: Masked 1,204 phones.' },
    { timestamp: '14:21:03', level: 'WARN', message: 'Chunk 2: Dropped 89 short texts.' },
    { timestamp: '14:21:30', level: 'INFO', message: 'MinHash Dedup: Scanning...' },
    { timestamp: '14:22:15', level: 'INFO', message: 'Chunk 3 processing...' },
    { timestamp: '14:22:30', level: 'INFO', message: '[INFO] epoch 1, step 4000' },
    { timestamp: '14:22:31', level: 'INFO', message: "{'loss': 0.85, 'learning_rate': 2e-5}" },
    { timestamp: '14:22:35', level: 'INFO', message: '[INFO] Saving checkpoint-4000...' },
    { timestamp: '14:22:45', level: 'INFO', message: '[INFO] step 4500, loss: 0.82' }
  ])

  const statusConfig = computed(() => TASK_STATUS_CONFIG[taskData.value.status])

  const handleBack = () => {
    router.push('/workbench/task-dispatch')
  }

  const handleForceTerminate = () => {
    ElMessageBox.confirm(
      `确定要强制终止任务 #${taskId.value} 吗？此操作不可恢复。`,
      '确认强制终止',
      {
        confirmButtonText: '确定终止',
        cancelButtonText: '取消',
        type: 'warning'
      }
    )
      .then(() => {
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
