<template>
  <div class="task-dashboard">
    <!-- 左侧：任务状态分布 -->
    <div class="dashboard-left">
      <div class="stat-card">
        <div class="stat-header">
          <LfpSvgIcon icon="ri:target-line" class="text-lg text-primary" />
          <span class="stat-title">任务状态分布</span>
        </div>
        <div class="stat-content">
          <div class="stat-item">
            <span class="stat-dot running"></span>
            <span class="stat-label">运行中</span>
            <span class="stat-value">{{ data.running }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-dot pending"></span>
            <span class="stat-label">排队中</span>
            <span class="stat-value">{{ data.pending }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-dot completed"></span>
            <span class="stat-label">已完成</span>
            <span class="stat-value">{{ data.completed }}</span>
          </div>
          <div class="stat-item">
            <span class="stat-dot failed"></span>
            <span class="stat-label">异常失败</span>
            <span class="stat-value">{{ data.failed }}</span>
          </div>
        </div>
      </div>

      <div class="stat-card">
        <div class="stat-header">
          <LfpSvgIcon icon="ri:time-line" class="text-lg text-warning" />
          <span class="stat-title">平均等待时长</span>
        </div>
        <div class="stat-value-large">{{ data.avgWaitTime }}</div>
      </div>

      <div class="stat-card">
        <div class="stat-header">
          <LfpSvgIcon icon="ri:line-chart-line" class="text-lg text-success" />
          <span class="stat-title">任务成功率</span>
        </div>
        <div class="stat-value-large">{{ data.successRate }}</div>
      </div>
    </div>

    <!-- 右侧：GPU配额 -->
    <div class="dashboard-right">
      <div class="gpu-quota-card">
        <div class="gpu-quota-header">
          <LfpSvgIcon icon="ri:flashlight-line" class="text-lg text-primary" />
          <span class="gpu-quota-title">平台可用逻辑 GPU 总量</span>
          <span class="gpu-quota-total">{{ data.totalGpu }} 卡</span>
        </div>
        <div class="gpu-quota-body">
          <div class="gpu-quota-info">
            <span class="gpu-label">当前已被预占 (Allocated)</span>
            <span class="gpu-value">{{ data.allocatedGpu }} 卡</span>
          </div>
          <ElProgress
            :percentage="gpuPercentage"
            :stroke-width="12"
            :show-text="false"
            :color="gpuProgressColor"
          />
          <div class="gpu-percentage-text">
            <span class="text-g-600">已用 {{ gpuPercentage }}%</span>
            <span class="text-g-500">{{ data.totalGpu - data.allocatedGpu }} 卡可用</span>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
  import LfpSvgIcon from '@/components/core/base/lfp-svg-icon/index.vue'
  import { getTasks, type TaskItem } from '@/api/task'

  defineOptions({ name: 'TaskDashboard' })

  const rawTasks = ref<TaskItem[]>([])

  async function fetchStats() {
    const resp = await getTasks()
    rawTasks.value = resp.items || []
  }

  const data = computed(() => {
    const running = rawTasks.value.filter((t) => t.status === 'running').length
    const pending = rawTasks.value.filter((t) => t.status === 'pending').length
    const completed = rawTasks.value.filter((t) => t.status === 'done').length
    const failed = rawTasks.value.filter((t) => t.status === 'failed').length
    const total = rawTasks.value.length

    const avgWaitTimeMs =
      pending > 0
        ? rawTasks.value
            .filter((t) => t.status === 'pending')
            .reduce((sum, t) => sum + (Date.now() - new Date(t.created_at).getTime()), 0) / pending
        : 0
    const avgWaitMin = Math.round(avgWaitTimeMs / 60000)

    return {
      running,
      pending,
      completed,
      failed,
      avgWaitTime: avgWaitMin > 0 ? `${avgWaitMin} 分钟` : '—',
      successRate: total > 0 ? `${Math.round((completed / total) * 100)}%` : '—',
      totalGpu: 8,
      allocatedGpu: running
    }
  })

  const gpuPercentage = computed(() => {
    if (data.value.totalGpu === 0) return 0
    return Math.round((data.value.allocatedGpu / data.value.totalGpu) * 100)
  })

  const gpuProgressColor = computed(() => {
    const percentage = gpuPercentage.value
    if (percentage > 80) return '#F56C6C'
    if (percentage > 50) return '#E6A23C'
    return '#67C23A'
  })

  onMounted(() => {
    fetchStats()
  })
</script>

<style lang="scss" scoped>
  .task-dashboard {
    display: grid;
    grid-template-columns: 1fr 320px;
    gap: 16px;
    margin-bottom: 20px;
  }

  .dashboard-left {
    display: grid;
    grid-template-columns: repeat(3, 1fr);
    gap: 16px;
  }

  .dashboard-right {
    display: flex;
    align-items: stretch;
  }

  .stat-card {
    display: flex;
    flex-direction: column;
    padding: 16px 20px;
    background: var(--el-fill-color-lighter);
    border-radius: var(--custom-radius, 8px);
    border: 1px solid var(--lfp-gray-200);

    .stat-header {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 12px;

      .stat-title {
        font-size: 14px;
        font-weight: 500;
        color: var(--lfp-gray-700);
      }
    }

    .stat-content {
      display: flex;
      flex-direction: column;
      gap: 8px;
    }

    .stat-item {
      display: flex;
      align-items: center;
      gap: 8px;

      .stat-dot {
        width: 8px;
        height: 8px;
        border-radius: 50%;

        &.running {
          background-color: #f56c6c;
        }

        &.pending {
          background-color: #e6a23c;
        }

        &.completed {
          background-color: #67c23a;
        }

        &.failed {
          background-color: #909399;
        }
      }

      .stat-label {
        font-size: 13px;
        color: var(--lfp-gray-600);
      }

      .stat-value {
        margin-left: auto;
        font-size: 14px;
        font-weight: 600;
        color: var(--lfp-gray-800);
      }
    }

    .stat-value-large {
      font-size: 24px;
      font-weight: 600;
      color: var(--lfp-gray-800);
    }
  }

  .gpu-quota-card {
    flex: 1;
    display: flex;
    flex-direction: column;
    padding: 16px 20px;
    background: var(--el-fill-color-lighter);
    border-radius: var(--custom-radius, 8px);
    border: 1px solid var(--lfp-gray-200);

    .gpu-quota-header {
      display: flex;
      align-items: center;
      gap: 8px;
      margin-bottom: 16px;

      .gpu-quota-title {
        font-size: 14px;
        font-weight: 500;
        color: var(--lfp-gray-700);
      }

      .gpu-quota-total {
        margin-left: auto;
        font-size: 16px;
        font-weight: 600;
        color: var(--lfp-gray-800);
      }
    }

    .gpu-quota-body {
      display: flex;
      flex-direction: column;
      gap: 8px;

      .gpu-quota-info {
        display: flex;
        justify-content: space-between;
        align-items: center;

        .gpu-label {
          font-size: 13px;
          color: var(--lfp-gray-600);
        }

        .gpu-value {
          font-size: 14px;
          font-weight: 600;
          color: var(--lfp-gray-800);
        }
      }

      .gpu-percentage-text {
        display: flex;
        justify-content: space-between;
        align-items: center;
        font-size: 12px;
      }
    }
  }
</style>
