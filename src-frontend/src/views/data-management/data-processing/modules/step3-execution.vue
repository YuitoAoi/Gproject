<template>
  <ExecutionPanel
    :task="task"
    :logs="logs"
    :funnel-data="funnelData"
    :show-return-button="true"
    @return-pool="$emit('returnPool')"
  />
</template>

<script setup lang="ts">
  import ExecutionPanel from '@/components/business/execution-panel.vue'

  defineOptions({ name: 'Step3Execution' })

  const props = defineProps<{
    task: Api.DataManage.DataProcessing.ProcessingTask | null
    logs: Api.DataManage.DataProcessing.ProcessingLog[]
  }>()

  defineEmits<{
    returnPool: []
  }>()

  const funnelData = computed(() => {
    if (!props.task) return undefined
    return {
      rawCount: props.task.rawCount || 0,
      filteredCount: props.task.filteredCount || 0,
      dedupedCount: props.task.dedupedCount || 0,
      finalCount: props.task.finalCount || 0
    }
  })
</script>

<style lang="scss" scoped>
  .step3-execution {
    height: 100%;
  }

  .split-layout {
    display: flex;
    gap: 16px;
    height: 100%;
  }

  .left-panel {
    width: 40%;
    flex-shrink: 0;
    background: #fff;
    border-radius: calc(var(--custom-radius, 8px) + 2px);
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);

    &__inner {
      padding: 16px;
    }
  }

  .right-panel {
    flex: 1;
    min-width: 0;
    background: #fff;
    border-radius: calc(var(--custom-radius, 8px) + 2px);
    display: flex;
    flex-direction: column;
    overflow: hidden;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);

    &__header {
      display: flex;
      align-items: center;
      justify-content: space-between;
      padding: 14px 16px;
      border-bottom: 1px solid var(--art-gray-100);
      flex-shrink: 0;
    }
  }

  .panel-title {
    font-size: 15px;
    font-weight: 600;
    color: var(--art-gray-800);
    display: flex;
    align-items: center;
  }

  // 状态卡片
  .status-card {
    padding: 18px;
    border-radius: calc(var(--custom-radius, 8px) + 2px);
    margin-bottom: 18px;
    border: 1px solid var(--art-gray-100);

    &.status-processing {
      background: linear-gradient(135deg, rgba(64, 158, 255, 0.04) 0%, #fff 100%);
      border-color: rgba(64, 158, 255, 0.15);
    }
    &.status-completed {
      background: linear-gradient(135deg, rgba(103, 194, 58, 0.04) 0%, #fff 100%);
      border-color: rgba(103, 194, 58, 0.15);
    }
    &.status-failed {
      background: linear-gradient(135deg, rgba(245, 108, 108, 0.04) 0%, #fff 100%);
      border-color: rgba(245, 108, 108, 0.15);
    }
  }

  .status-indicator {
    width: 42px;
    height: 42px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    color: #fff;

    &.indicator-pending {
      background: var(--art-gray-400);
    }
    &.indicator-processing {
      background: #409eff;
    }
    &.indicator-completed {
      background: #67c23a;
    }
    &.indicator-failed {
      background: #f56c6c;
    }
  }

  .completion-badge {
    display: flex;
    align-items: center;
    padding: 10px 14px;
    background: rgba(103, 194, 58, 0.08);
    color: #67c23a;
    font-size: 13px;
    font-weight: 500;
    border-radius: 6px;
  }

  .error-badge {
    display: flex;
    align-items: center;
    padding: 10px 14px;
    background: rgba(245, 108, 108, 0.08);
    color: #f56c6c;
    font-size: 13px;
    font-weight: 500;
    border-radius: 6px;
  }

  // 漏斗图
  .funnel-section {
    margin-top: 4px;
  }

  .section-subtitle {
    display: flex;
    align-items: center;
    font-size: 13px;
    font-weight: 600;
    color: var(--art-gray-700);
    margin: 0 0 14px;
  }

  .funnel-chart {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }

  .funnel-row {
    padding: 0 4px;
  }

  .funnel-bar {
    height: 42px;
    border-radius: 6px;
    position: relative;
    min-width: 60px;
    transition: width 0.5s ease;

    &__fill {
      position: absolute;
      inset: 0;
      border-radius: 6px;
      opacity: 0.15;

      &.funnel-raw {
        background: #409eff;
      }
      &.funnel-filter {
        background: #e6a23c;
      }
      &.funnel-dedup {
        background: #67c23a;
      }
    }

    &__label {
      position: absolute;
      left: 12px;
      top: 50%;
      transform: translateY(-50%);
      font-size: 12px;
      font-weight: 500;
      color: var(--art-gray-600);
    }

    &__count {
      position: absolute;
      right: 12px;
      top: 50%;
      transform: translateY(-50%);
      font-size: 13px;
      font-weight: 700;
      color: var(--art-gray-800);
    }
  }

  .funnel-arrow {
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    padding: 4px 0;
  }

  .funnel-result {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px;
    margin-top: 12px;
    background: linear-gradient(135deg, rgba(103, 194, 58, 0.06) 0%, #fff 100%);
    border: 1px solid rgba(103, 194, 58, 0.2);
    border-radius: calc(var(--custom-radius, 8px) + 2px);
  }

  // 终端日志
  .terminal {
    flex: 1;
    min-height: 0;
    background: #f8f9fb;
    border-top: 1px solid var(--art-gray-150);
    overflow: hidden;

    &__scroll {
      height: 100%;
    }

    &__content {
      padding: 14px 0;
    }
  }

  .terminal-line {
    display: flex;
    gap: 4px;
    padding: 2px 18px;
    font-family: 'Cascadia Code', 'Fira Code', 'JetBrains Mono', 'Consolas', monospace;
    font-size: 12px;
    line-height: 1.8;

    &__time {
      color: var(--art-gray-400);
      flex-shrink: 0;
    }

    &__level {
      flex-shrink: 0;
      font-weight: 600;
    }

    &__msg {
      color: var(--art-gray-700);
    }

    &.terminal-info {
      .terminal-line__time {
        color: var(--art-gray-500);
      }
      .terminal-line__level {
        color: var(--art-gray-500);
      }
      .terminal-line__msg {
        color: var(--art-gray-500);
      }
    }

    &.terminal-warn {
      .terminal-line__time {
        color: #d97706;
      }
      .terminal-line__level {
        color: #d97706;
      }
      .terminal-line__msg {
        color: #d97706;
      }
    }

    &.terminal-error {
      .terminal-line__time {
        color: #dc2626;
      }
      .terminal-line__level {
        color: #dc2626;
      }
      .terminal-line__msg {
        color: #dc2626;
      }
    }

    &.terminal-stage {
      font-weight: 700;
      border-left: 3px solid;
      padding-left: 9px;

      .terminal-line__level {
        display: none;
      }

      &.terminal-stage--inprogress {
        color: var(--el-color-primary);
        border-color: var(--el-color-primary);
        .terminal-line__time {
          color: var(--el-color-primary);
        }
        .terminal-line__msg {
          color: var(--el-color-primary);
        }
      }
      &.terminal-stage--done {
        color: #16a34a;
        border-color: #16a34a;
        .terminal-line__time {
          color: #16a34a;
        }
        .terminal-line__msg {
          color: #16a34a;
        }
      }
      &.terminal-stage--error {
        color: #dc2626;
        border-color: #dc2626;
        .terminal-line__time {
          color: #dc2626;
        }
        .terminal-line__msg {
          color: #dc2626;
        }
      }
    }
  }

  .terminal-cursor {
    &__blink {
      color: var(--el-color-primary);
      animation: blink 1s step-end infinite;
    }
  }

  @keyframes blink {
    0%,
    100% {
      opacity: 1;
    }
    50% {
      opacity: 0;
    }
  }

  // 覆盖 Terminal 内部的 el-scrollbar 颜色
  .terminal {
    :deep(.el-scrollbar__thumb) {
      background-color: rgba(148, 163, 184, 0.25) !important;
    }
    :deep(.el-scrollbar__bar.is-vertical) {
      right: 2px;
    }
  }
</style>
