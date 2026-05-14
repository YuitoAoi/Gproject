<template>
  <div class="cleaning-monitor-page">
    <div class="split-layout">
      <div class="left-panel">
        <ElScrollbar>
          <div class="left-panel__inner">
            <h3 class="panel-title"> <span class="ri:broom-line mr-2"></span>清洗任务监控 </h3>

            <template v-if="rawTask">
              <div class="status-card" :class="`status-${taskStatus}`">
                <div class="flex items-center justify-between mb-4">
                  <div class="flex items-center gap-3">
                    <div class="status-indicator" :class="statusClass">
                      <span
                        v-if="taskStatus === 'processing' || taskStatus === 'running'"
                        class="ri:loader-4-line animate-spin text-xl"
                      ></span>
                      <span
                        v-else-if="taskStatus === 'completed'"
                        class="ri:check-line text-xl"
                      ></span>
                      <span
                        v-else-if="taskStatus === 'failed'"
                        class="ri:close-line text-xl"
                      ></span>
                      <span v-else class="ri:time-line text-xl"></span>
                    </div>
                    <div>
                      <div class="text-sm font-medium">{{ statusLabel }}</div>
                      <div v-if="rawTask.task_name" class="text-xs text-g-500 mt-0.5">
                        {{ rawTask.task_name }}
                      </div>
                    </div>
                  </div>
                  <span v-if="taskIdParam" class="text-xs text-g-500">#{{ taskIdParam }}</span>
                </div>

                <div v-if="taskStatus === 'processing' || taskStatus === 'running'" class="mb-3">
                  <ElProgress
                    :percentage="Math.round((rawTask.progress || 0) * 100)"
                    :stroke-width="8"
                    :show-text="true"
                    :color="progressColor"
                  />
                  <div v-if="currentStageLabel" class="text-xs text-g-500 mt-2">
                    当前阶段: {{ currentStageLabel }}
                  </div>
                </div>

                <div v-else-if="taskStatus === 'completed'" class="completion-badge">
                  <span class="ri:check-double-line mr-1"></span>清洗任务已完成
                </div>

                <div v-else-if="taskStatus === 'failed'" class="error-badge">
                  <span class="ri:error-warning-line mr-1"></span>清洗任务执行失败
                </div>
              </div>

              <div class="phase-flow-section">
                <h4 class="section-subtitle">
                  <span class="ri:flow-chart mr-1.5"></span>处理阶段 (Processing Stages)
                </h4>
                <div class="phase-flow">
                  <div
                    v-for="(stage, index) in stages"
                    :key="stage.key"
                    class="phase-item"
                    :class="{
                      'phase-item--done': stage.status === 'done',
                      'phase-item--inprogress': stage.status === 'inprogress',
                      'phase-item--pending': stage.status === 'pending'
                    }"
                  >
                    <div class="phase-item__indicator">
                      <span v-if="stage.status === 'done'" class="ri:check-line"></span>
                      <span
                        v-else-if="stage.status === 'inprogress'"
                        class="ri:loader-4-line animate-spin"
                      ></span>
                      <span v-else class="phase-item__num">{{ index + 1 }}</span>
                    </div>
                    <div class="phase-item__content">
                      <div class="phase-item__label">{{ stage.label }}</div>
                      <div class="phase-item__desc">{{ stage.description }}</div>
                    </div>
                    <div v-if="stage.status === 'done'" class="phase-item__check">
                      <span class="ri:checkbox-circle-line text-success"></span>
                    </div>
                  </div>
                </div>
              </div>

              <div class="data-stats-section">
                <h4 class="section-subtitle">
                  <span class="ri:bar-chart-box mr-1.5"></span>数据规模 (Data Scale)
                </h4>
                <div class="data-stats">
                  <div class="stat-card stat-card--input">
                    <div class="stat-card__icon">
                      <span class="ri:file-list-3-line text-xl"></span>
                    </div>
                    <div class="stat-card__content">
                      <div class="stat-card__label">输入规模</div>
                      <div class="stat-card__value">
                        {{ formatNumber(summaryData.rawCount) }}
                        <span class="stat-card__unit">条</span>
                      </div>
                      <div class="stat-card__desc">原始数据总量</div>
                    </div>
                  </div>
                  <div class="stat-arrow">
                    <span class="ri:arrow-right-line text-g-400"></span>
                  </div>
                  <div class="stat-card stat-card--output">
                    <div class="stat-card__icon">
                      <span class="ri:file-check-line text-xl"></span>
                    </div>
                    <div class="stat-card__content">
                      <div class="stat-card__label">输出规模</div>
                      <div class="stat-card__value">
                        {{ formatNumber(summaryData.finalCount) }}
                        <span class="stat-card__unit">条</span>
                      </div>
                      <div class="stat-card__desc">
                        产出率:
                        {{
                          summaryData.rawCount && summaryData.finalCount
                            ? ((summaryData.finalCount / summaryData.rawCount) * 100).toFixed(1)
                            : '0.0'
                        }}%
                      </div>
                    </div>
                  </div>
                </div>
              </div>
            </template>

            <template v-else>
              <div class="status-card status-pending">
                <div class="flex items-center justify-center py-8">
                  <span class="ri:loader-4-line animate-spin text-2xl text-primary mr-3"></span>
                  <span class="text-sm text-g-600">正在加载任务...</span>
                </div>
              </div>
            </template>

            <div class="mt-5">
              <ElButton class="w-full" @click="handleBack">
                <span class="ri:arrow-left-line mr-1"></span>返回任务调度中心
              </ElButton>
              <p class="text-xs text-g-600 text-center mt-2">
                清洗任务在服务器端运行，关闭浏览器或跳转页面不会导致任务中断。
              </p>
            </div>
          </div>
        </ElScrollbar>
      </div>

      <div class="right-panel">
        <div class="right-panel__header">
          <h3 class="panel-title">
            <span class="ri:terminal-box-line mr-2"></span>终端日志 Terminal
          </h3>
          <ElButton size="small" text>
            <span class="ri:download-line mr-1"></span>导出日志
          </ElButton>
        </div>

        <div class="terminal">
          <ElScrollbar ref="scrollbarRef" class="terminal__scroll">
            <div class="terminal__content">
              <div
                v-for="(log, i) in terminalLogs"
                :key="i"
                class="terminal-line"
                :class="{
                  'terminal-info': log.level === 'INFO',
                  'terminal-warn': log.level === 'WARN',
                  'terminal-error': log.level === 'ERROR',
                  'terminal-stage terminal-stage--inprogress': log.level === 'STAGE_INPROGRESS',
                  'terminal-stage terminal-stage--done': log.level === 'STAGE_DONE',
                  'terminal-stage terminal-stage--error': log.level === 'STAGE_ERROR'
                }"
              >
                <span class="terminal-line__time">[{{ log.time }}]</span>
                <span class="terminal-line__level">[{{ log.level }}]</span>
                <span class="terminal-line__msg">{{ log.message }}</span>
              </div>
              <div
                class="terminal-line terminal-cursor"
                v-if="rawTask && (taskStatus === 'processing' || taskStatus === 'running')"
              >
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
  import { ElMessage } from 'element-plus'
  import { getTask as fetchTask, type TaskItem } from '@/api/task'
  import { getDatasetLogs } from '@/api/dataset'
  import { useWebSocketTask } from '@/hooks/core/useWebSocketTask'

  defineOptions({ name: 'CleaningMonitorPage' })

  const route = useRoute()
  const router = useRouter()

  const taskIdParam = computed(() => route.params.id as string)
  const taskId = computed(() => Number(taskIdParam.value))

  const rawTask = ref<TaskItem | null>(null)
  const terminalLogs = ref<any[]>([])
  const scrollbarRef = ref<{ setScrollTop: (top: number) => void } | null>(null)

  interface Stage {
    key: string
    label: string
    description: string
    status: 'done' | 'inprogress' | 'pending'
  }

  const stageMapping: Record<string, { label: string; description: string }> = {
    read: { label: '读取源数据', description: '从数据源读取原始数据' },
    chunk: { label: '读取源数据', description: '数据分块与预处理' },
    build_kg: { label: '构建知识图谱', description: '实体识别与关系抽取' },
    partition: { label: '构建知识图谱', description: '知识图谱分区与索引' },
    generate: { label: '生成结构化结果', description: '生成清洗后的结构化数据' },
    save: { label: '保存清洗产物', description: '输出最终清洗结果' }
  }

  const stages = computed<Stage[]>(() => {
    const currentPhase = rawTask.value?.phase || 'read'
    const phaseOrder = ['read', 'chunk', 'build_kg', 'partition', 'generate', 'save']
    const currentIndex = phaseOrder.indexOf(currentPhase)
    const isRunning = taskStatus.value === 'running' || taskStatus.value === 'processing'

    const stageKeys = ['read', 'build_kg', 'generate', 'save']
    const mappedStages: Stage[] = []

    stageKeys.forEach((key) => {
      let status: Stage['status'] = 'pending'
      if (!isRunning && rawTask.value?.status === 'completed') {
        status = 'done'
      } else if (!isRunning && rawTask.value?.status === 'failed') {
        const failPhaseIndex = currentIndex >= 0 ? currentIndex : 0
        const mappedIdx = key === 'read' ? 0 : key === 'build_kg' ? 1 : key === 'generate' ? 2 : 3
        status = mappedIdx < failPhaseIndex ? 'done' : 'pending'
      } else if (isRunning) {
        const stagePhaseMap: Record<string, number> = { read: 0, build_kg: 1, generate: 2, save: 3 }
        const stageIdx = stagePhaseMap[key]
        if (stageIdx < currentIndex) {
          status = 'done'
        } else if (stageIdx === currentIndex) {
          status = 'inprogress'
        } else {
          status = 'pending'
        }
      }

      mappedStages.push({
        key,
        label: stageMapping[key].label,
        description: stageMapping[key].description,
        status
      })
    })

    return mappedStages
  })

  const summaryData = ref({
    rawCount: 0,
    finalCount: 0
  })

  const taskStatus = computed(() => {
    if (!rawTask.value) return 'pending'
    const status = rawTask.value.status
    if (status === 'done') return 'completed'
    if (status === 'failed') return 'failed'
    if (status === 'running') return 'running'
    if (status === 'pending') return 'pending'
    return 'processing'
  })

  const statusLabel = computed(() => {
    const map: Record<string, string> = {
      pending: '⏳ 等待中 (Pending)',
      processing: '处理中 (Processing)',
      running: '处理中 (Running)',
      completed: '✅ 已完成 (Completed)',
      failed: '❌ 执行失败 (Failed)'
    }
    return map[taskStatus.value] || taskStatus.value
  })

  const statusClass = computed(() => `indicator-${taskStatus.value}`)

  const currentStageLabel = computed(() => {
    const phase = rawTask.value?.phase || 'read'
    return stageMapping[phase]?.label || phase
  })

  const progressColor = computed(() => {
    const p = rawTask.value?.progress || 0
    if (p < 0.3) return '#E6A23C'
    if (p < 0.7) return '#409EFF'
    return '#67C23A'
  })

  function formatNumber(n: number): string {
    return n.toLocaleString()
  }

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
        terminalLogs.value = resp.lines.map((line: string) => ({
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

      if (resp.task.config) {
        try {
          const cfg = JSON.parse(resp.task.config)
          summaryData.value.rawCount = cfg.raw_count || 0
          summaryData.value.finalCount = cfg.final_count || 0
        } catch {
          // config 解析失败时使用默认值
        }
      }

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

  watch(
    () => terminalLogs.value.length,
    async () => {
      await nextTick()
      scrollbarRef.value?.setScrollTop(999999)
    }
  )

  const handleBack = () => {
    router.push('/workbench/task-dispatch')
  }
</script>

<style lang="scss" scoped>
  .cleaning-monitor-page {
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
      border-bottom: 1px solid var(--lfp-gray-100);
      flex-shrink: 0;
    }
  }

  .panel-title {
    font-size: 15px;
    font-weight: 600;
    color: var(--lfp-gray-800);
    display: flex;
    align-items: center;
  }

  .status-card {
    padding: 18px;
    border-radius: calc(var(--custom-radius, 8px) + 2px);
    margin-bottom: 18px;
    border: 1px solid var(--lfp-gray-100);

    &.status-processing,
    &.status-running {
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
      background: var(--lfp-gray-400);
    }
    &.indicator-processing,
    &.indicator-running {
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

  .phase-flow-section {
    margin-bottom: 18px;
  }

  .section-subtitle {
    display: flex;
    align-items: center;
    font-size: 13px;
    font-weight: 600;
    color: var(--lfp-gray-700);
    margin: 0 0 14px;
  }

  .phase-flow {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }

  .phase-item {
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 12px 14px;
    border-radius: 8px;
    background: var(--el-fill-color-lighter);
    border: 1px solid var(--lfp-gray-100);
    transition: all 0.3s ease;

    &--done {
      background: rgba(103, 194, 58, 0.06);
      border-color: rgba(103, 194, 58, 0.2);
    }

    &--inprogress {
      background: rgba(64, 158, 255, 0.06);
      border-color: rgba(64, 158, 255, 0.2);
    }

    &--pending {
      opacity: 0.6;
    }

    &__indicator {
      width: 32px;
      height: 32px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 14px;
      font-weight: 600;
      flex-shrink: 0;

      .phase-item--done & {
        background: #67c23a;
        color: #fff;
      }

      .phase-item--inprogress & {
        background: #409eff;
        color: #fff;
      }

      .phase-item--pending & {
        background: var(--lfp-gray-300);
        color: var(--lfp-gray-600);
      }
    }

    &__num {
      font-size: 12px;
    }

    &__content {
      flex: 1;
    }

    &__label {
      font-size: 13px;
      font-weight: 600;
      color: var(--lfp-gray-800);
    }

    &__desc {
      font-size: 11px;
      color: var(--lfp-gray-500);
      margin-top: 2px;
    }

    &__check {
      flex-shrink: 0;
    }
  }

  .data-stats-section {
    margin-bottom: 18px;
  }

  .data-stats {
    display: flex;
    align-items: center;
    gap: 12px;
  }

  .stat-card {
    flex: 1;
    display: flex;
    align-items: center;
    gap: 12px;
    padding: 14px;
    border-radius: 8px;
    background: var(--el-fill-color-lighter);
    border: 1px solid var(--lfp-gray-100);

    &--input {
      background: rgba(64, 158, 255, 0.04);
      border-color: rgba(64, 158, 255, 0.15);
    }

    &--output {
      background: rgba(103, 194, 58, 0.04);
      border-color: rgba(103, 194, 58, 0.15);
    }

    &__icon {
      width: 40px;
      height: 40px;
      border-radius: 8px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;

      .stat-card--input & {
        background: rgba(64, 158, 255, 0.1);
        color: #409eff;
      }

      .stat-card--output & {
        background: rgba(103, 194, 58, 0.1);
        color: #67c23a;
      }
    }

    &__content {
      min-width: 0;
    }

    &__label {
      font-size: 11px;
      color: var(--lfp-gray-500);
    }

    &__value {
      font-size: 20px;
      font-weight: 700;
      color: var(--lfp-gray-800);
      line-height: 1.2;
    }

    &__unit {
      font-size: 12px;
      font-weight: 400;
      color: var(--lfp-gray-500);
    }

    &__desc {
      font-size: 11px;
      color: var(--lfp-gray-500);
      margin-top: 2px;
    }
  }

  .stat-arrow {
    flex-shrink: 0;
  }

  .terminal {
    flex: 1;
    min-height: 0;
    background: #f8f9fb;
    border-top: 1px solid var(--lfp-gray-150);
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
      color: var(--lfp-gray-400);
      flex-shrink: 0;
    }

    &__level {
      flex-shrink: 0;
      font-weight: 600;
    }

    &__msg {
      color: var(--lfp-gray-700);
    }

    &.terminal-info {
      .terminal-line__time {
        color: var(--lfp-gray-500);
      }
      .terminal-line__level {
        color: var(--lfp-gray-500);
      }
      .terminal-line__msg {
        color: var(--lfp-gray-500);
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

  .terminal {
    :deep(.el-scrollbar__thumb) {
      background-color: rgba(148, 163, 184, 0.25) !important;
    }
    :deep(.el-scrollbar__bar.is-vertical) {
      right: 2px;
    }
  }
</style>
