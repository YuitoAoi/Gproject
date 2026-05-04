<template>
  <div class="step3-execution">
    <div class="split-layout">
      <!-- ========== 左侧：任务大盘与产出漏斗 (40%) ========== -->
      <div class="left-panel">
        <ElScrollbar>
          <div class="left-panel__inner">
            <h3 class="panel-title">
              <span class="ri:dashboard-line mr-2"></span>任务大盘与产出漏斗
            </h3>

            <template v-if="task">
              <!-- 任务状态卡片 -->
              <div class="status-card" :class="`status-${task.status}`">
                <div class="flex items-center justify-between mb-4">
                  <div class="flex items-center gap-3">
                    <div class="status-indicator" :class="statusClass">
                      <span v-if="task.status === 'processing'" class="ri:loader-4-line animate-spin text-xl"></span>
                      <span v-else-if="task.status === 'completed'" class="ri:check-line text-xl"></span>
                      <span v-else-if="task.status === 'failed'" class="ri:close-line text-xl"></span>
                      <span v-else class="ri:time-line text-xl"></span>
                    </div>
                    <div>
                      <div class="text-sm font-medium">{{ statusLabel }}</div>
                      <div class="text-xs text-g-500 mt-0.5">{{ task.datasetName }}</div>
                    </div>
                  </div>
                  <span class="text-xs text-g-500">{{ task.taskId }}</span>
                </div>

                <!-- 进度条 -->
                <div v-if="task.status === 'processing'" class="mb-3">
                  <ElProgress
                    :percentage="task.progress"
                    :stroke-width="8"
                    :show-text="true"
                    :color="progressColor"
                  />
                  <div class="text-xs text-g-500 mt-2">预计剩余: {{ task.eta }}</div>
                </div>

                <!-- 完成态 -->
                <div v-else-if="task.status === 'completed'" class="completion-badge">
                  <span class="ri:check-double-line mr-1"></span>任务已完成
                </div>

                <!-- 失败态 -->
                <div v-else-if="task.status === 'failed'" class="error-badge">
                  <span class="ri:error-warning-line mr-1"></span>任务执行失败
                </div>
              </div>

              <!-- 数据质量漏斗 -->
              <div class="funnel-section">
                <h4 class="section-subtitle">
                  <span class="ri:funnel-line mr-1.5"></span>数据质量漏斗 (Data Yield Funnel)
                </h4>
                <div class="funnel-chart">
                  <!-- 原始数据 -->
                  <div class="funnel-row">
                    <div class="funnel-bar" style="width: 100%">
                      <div class="funnel-bar__fill funnel-raw"></div>
                      <span class="funnel-bar__label">原始数据总量</span>
                      <span class="funnel-bar__count">{{ formatNumber(task.rawCount) }} 条</span>
                    </div>
                  </div>

                  <!-- 箭头 -->
                  <div class="funnel-arrow">
                    <span class="ri:arrow-down-line text-g-400"></span>
                    <span class="text-xs text-g-500">— {{ formatNumber(task.filteredCount) }} 条</span>
                  </div>

                  <!-- 过滤清洗后 -->
                  <div class="funnel-row">
                    <div class="funnel-bar" :style="{ width: filterRatio + '%' }">
                      <div class="funnel-bar__fill funnel-filter"></div>
                      <span class="funnel-bar__label">过滤与清洗</span>
                      <span class="funnel-bar__count">{{ formatNumber(task.rawCount - task.filteredCount) }} 条</span>
                    </div>
                  </div>

                  <!-- 箭头 -->
                  <div class="funnel-arrow">
                    <span class="ri:arrow-down-line text-g-400"></span>
                    <span class="text-xs text-g-500">— {{ formatNumber(task.dedupedCount) }} 条</span>
                  </div>

                  <!-- 相似度去重后 -->
                  <div class="funnel-row">
                    <div class="funnel-bar" :style="{ width: dedupRatio + '%' }">
                      <div class="funnel-bar__fill funnel-dedup"></div>
                      <span class="funnel-bar__label">相似度去重</span>
                      <span class="funnel-bar__count">{{ formatNumber(task.rawCount - task.filteredCount - task.dedupedCount) }} 条</span>
                    </div>
                  </div>
                </div>

                <!-- 最终产出 -->
                <div class="funnel-result">
                  <div class="funnel-result__icon">
                    <span class="ri:checkbox-circle-line text-2xl text-success"></span>
                  </div>
                  <div>
                    <div class="text-xs text-g-500">最终有效产出</div>
                    <div class="text-xl font-bold text-success">{{ formatNumber(task.finalCount) }} 条</div>
                    <div class="text-xs text-g-400">产出率: {{ ((task.finalCount / task.rawCount) * 100).toFixed(1) }}%</div>
                  </div>
                </div>
              </div>
            </template>

            <template v-else>
              <div class="status-card status-pending">
                <div class="flex items-center justify-center py-8">
                  <span class="ri:loader-4-line animate-spin text-2xl text-primary mr-3"></span>
                  <span class="text-sm text-g-600">正在启动任务...</span>
                </div>
              </div>
            </template>

            <!-- 操作按钮 -->
            <div class="mt-5">
              <ElButton class="w-full" @click="$emit('returnPool')">
                <span class="ri:home-line mr-1"></span>返回资产池
              </ElButton>
              <p class="text-xs text-g-600 text-center mt-2">
                清洗任务在服务器端运行，关闭浏览器或跳转页面不会导致任务中断。
              </p>
            </div>
          </div>
        </ElScrollbar>
      </div>

      <!-- ========== 右侧：流式运行日志面板 (60%) ========== -->
      <div class="right-panel">
        <div class="right-panel__header">
          <h3 class="panel-title">
            <span class="ri:terminal-box-line mr-2"></span>终端日志 Terminal
          </h3>
          <ElButton size="small" text>
            <span class="ri:download-line mr-1"></span>导出日志
          </ElButton>
        </div>

        <div class="terminal" ref="terminalRef">
          <ElScrollbar ref="scrollbarRef" class="terminal__scroll">
            <div class="terminal__content">
              <div
                v-for="(log, i) in logs"
                :key="i"
                class="terminal-line"
                :class="`terminal-${log.level.toLowerCase()}`"
              >
                <span class="terminal-line__time">[{{ log.time }}]</span>
                <span class="terminal-line__level">[{{ log.level }}]</span>
                <span class="terminal-line__msg">{{ log.message }}</span>
              </div>
              <!-- 光标闪烁 -->
              <div class="terminal-line terminal-cursor" v-if="task && task.status === 'processing'">
                <span class="terminal-cursor__blink">_</span>
              </div>
            </div>
          </ElScrollbar>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'

defineOptions({ name: 'Step3Execution' })

const props = defineProps<{
  task: Api.DataManage.DataProcessing.ProcessingTask | null
  logs: Api.DataManage.DataProcessing.ProcessingLog[]
  config: Api.DataManage.DataProcessing.CleaningConfig
}>()

defineEmits<{
  returnPool: []
}>()

const terminalRef = ref<HTMLElement | null>(null)
const scrollbarRef = ref<{ setScrollTop: (top: number) => void } | null>(null)

const statusLabel = computed(() => {
  if (!props.task) return ''
  const map: Record<string, string> = {
    pending: '⏳ 等待中 (Pending)',
    processing: '处理中 (Processing)',
    completed: '✅ 已完成 (Completed)',
    failed: '❌ 执行失败 (Failed)'
  }
  return map[props.task.status] || props.task.status
})

const statusClass = computed(() => {
  if (!props.task) return ''
  return `indicator-${props.task.status}`
})

const progressColor = computed(() => {
  if (!props.task || !props.task.progress) return '#409EFF'
  if (props.task.progress < 30) return '#E6A23C'
  if (props.task.progress < 70) return '#409EFF'
  return '#67C23A'
})

const filterRatio = computed(() => {
  if (!props.task || !props.task.rawCount) return 100
  return Math.max(((props.task.rawCount - props.task.filteredCount) / props.task.rawCount) * 100, 20)
})

const dedupRatio = computed(() => {
  if (!props.task || !props.task.rawCount) return 100
  return Math.max(((props.task.rawCount - props.task.filteredCount - props.task.dedupedCount) / props.task.rawCount) * 100, 20)
})

function formatNumber(n: number): string {
  return n.toLocaleString()
}

watch(() => props.logs.length, async () => {
  await nextTick()
  scrollbarRef.value?.setScrollTop(999999)
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

  &.indicator-pending { background: var(--art-gray-400); }
  &.indicator-processing { background: #409eff; }
  &.indicator-completed { background: #67c23a; }
  &.indicator-failed { background: #f56c6c; }
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

    &.funnel-raw { background: #409eff; }
    &.funnel-filter { background: #e6a23c; }
    &.funnel-dedup { background: #67c23a; }
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
    .terminal-line__level { color: var(--el-color-primary); }
  }

  &.terminal-warn {
    .terminal-line__level { color: #d97706; }
    .terminal-line__msg { color: #92400e; }
  }

  &.terminal-error {
    .terminal-line__level { color: #dc2626; }
    .terminal-line__msg { color: #b91c1c; }
  }
}

.terminal-cursor {
  &__blink {
    color: var(--el-color-primary);
    animation: blink 1s step-end infinite;
  }
}

@keyframes blink {
  0%, 100% { opacity: 1; }
  50% { opacity: 0; }
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
