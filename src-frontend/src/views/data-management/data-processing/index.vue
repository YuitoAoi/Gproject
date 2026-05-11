<template>
  <div class="data-processing-page">
    <!-- ========== 顶部流程向导条 ========== -->
    <div class="wizard-header">
      <div class="wizard-header__left">
        <ElButton class="wizard-back-btn" text @click="handleBack">
          <ArtSvgIcon icon="ri:arrow-left-line" class="mr-2" />
          返回管理页
        </ElButton>
      </div>
      <div class="wizard-header__steps">
        <div
          v-for="(step, idx) in steps"
          :key="idx"
          class="wizard-step"
          :class="{
            'is-active': currentStep === idx + 1,
            'is-done': currentStep > idx + 1,
            'is-clickable': canClickStep(idx + 1)
          }"
        >
          <div class="wizard-step__dot">
            <span class="wizard-step__num">{{ idx + 1 }}</span>
          </div>
          <span class="wizard-step__label" @click="handleStepClick(idx + 1)">{{ step.label }}</span>
        </div>
      </div>
    </div>

    <!-- ========== 步骤内容区 ========== -->
    <div class="wizard-content">
      <Step1DataSource
        v-if="currentStep === 1"
        :datasets="datasets"
        :loading="loading"
        :selected-id="selectedDatasetId"
        @select="handleSelectDataset"
        @upload="handleTempUpload"
      />
      <Step2Mapping
        v-if="currentStep === 2"
        :dataset="selectedDataset"
        :config="processConfig"
        @update:config="handleConfigUpdate"
      />
      <Step3Execution
        v-if="currentStep === 3"
        :task="taskInfo"
        :logs="taskLogs"
        :config="processConfig"
        @return-pool="handleReturnPool"
      />
    </div>

    <!-- ========== 底部操作栏 ========== -->
    <div class="wizard-footer" v-if="currentStep !== 3">
      <ElButton @click="handleCancel">取消</ElButton>
      <div class="flex gap-3">
        <ElButton v-if="currentStep > 1" @click="goPreviousStep"> 上一步 </ElButton>
        <ElButton
          v-if="currentStep === 1"
          type="primary"
          :disabled="!selectedDatasetId"
          @click="handleNextStep"
        >
          下一步：配置清洗规则
          <span class="ri:arrow-right-line ml-1"></span>
        </ElButton>
        <ElButton
          v-if="currentStep === 2"
          type="primary"
          @click="handleSubmitTask"
          :loading="submitting"
        >
          <span class="ri:rocket-line mr-1"></span>提交并开始异步清洗任务
        </ElButton>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import { getDatasets, processDataset, type DatasetItemDTO } from '@/api/dataset'
  import Step1DataSource from './modules/step1-datasource.vue'
  import Step2Mapping from './modules/step2-mapping.vue'
  import Step3Execution from './modules/step3-execution.vue'

  defineOptions({ name: 'DataProcessingPage' })

  const DEFAULT_PROCESS_CONFIG: Api.DataManage.DataProcessing.ProcessConfig = {
    api_key:
      'sk-cp-VkpJUr7Be-n8QMuOGwjaeWl5_LWjlj17SV0BFQ-hEkt1x2Fh9hjL8zLvjwhT-Rqc0tXx_Mz4T97dHlM2r6mzGUane7TZNquKlVJyPfNmt4UaVNeShX91Xps',
    synthesizer_url: 'https://api.minimaxi.com/v1',
    synthesizer_model: 'MiniMax-M2.7',
    mode: 'atomic',
    data_format: 'Alpaca',
    content_field: 'content',
    tokenizer: 'cl100k_base',
    chunk_size: 1024,
    chunk_overlap: 100,
    quiz_samples: 2,
    partition_method: 'ece',
    rpm: 1000,
    tpm: 50000
  }

  const router = useRouter()
  const route = useRoute()

  type StepConfig = { label: string }
  const steps: StepConfig[] = [
    { label: '选择源数据' },
    { label: '映射字段' },
    { label: '执行任务' }
  ]

  const currentStep = ref(1)
  const selectedDatasetId = ref<number | null>(null)
  const loading = ref(false)
  const datasets = ref<DatasetItemDTO[]>([])
  const submitting = ref(false)

  const processConfig = reactive<Api.DataManage.DataProcessing.ProcessConfig>({
    ...DEFAULT_PROCESS_CONFIG
  })

  const taskInfo = ref<Api.DataManage.DataProcessing.ProcessingTask | null>(null)
  const taskLogs = ref<Api.DataManage.DataProcessing.ProcessingLog[]>([])
  const currentJobId = ref<string | null>(null)

  const selectedDataset = computed(() => {
    return datasets.value.find((d) => d.id === selectedDatasetId.value) || null
  })

  const previousDatasetId = ref<number | null>(null)

  function handleSelectDataset(id: number) {
    selectedDatasetId.value = id
  }

  function handleTempUpload() {
    // 复用数据集管理页面的上传弹窗逻辑，完成后自动选中并进入Step2
    ElMessage.info('临时导入功能将调用数据集管理页相同的上传组件')
  }

  function handleConfigUpdate(config: Api.DataManage.DataProcessing.ProcessConfig) {
    Object.assign(processConfig, config)
  }

  function goPreviousStep() {
    if (currentStep.value === 2) {
      previousDatasetId.value = selectedDatasetId.value
    }
    if (currentStep.value === 3) {
      stopProgressWs()
      taskInfo.value = null
      taskLogs.value = []
    }
    currentStep.value--
  }

  async function handleNextStep() {
    if (!selectedDatasetId.value) return

    // 如果选择的数据集与上次不同，重置配置
    if (previousDatasetId.value !== null && previousDatasetId.value !== selectedDatasetId.value) {
      resetProcessConfig()
    }

    currentStep.value = 2
  }

  async function handleSubmitTask() {
    if (!selectedDatasetId.value) {
      ElMessage.error('请先选择数据集')
      return
    }
    submitting.value = true
    try {
      const response = await processDataset(selectedDatasetId.value, processConfig)
      if (response.error) {
        ElMessage.error('提交任务失败: ' + response.error)
        return
      }
      currentJobId.value = response.job_id
      currentStep.value = 3

      taskInfo.value = {
        taskId: response.job_id,
        datasetName: selectedDataset.value?.name || '',
        status: 'pending',
        progress: 0,
        eta: '计算中...',
        rawCount: 0,
        filteredCount: 0,
        dedupedCount: 0,
        finalCount: 0
      }

      taskLogs.value = []
      appendLog('INFO', `任务已提交，Job ID: ${response.job_id}`)
      appendLog('INFO', `使用模型: ${processConfig.synthesizer_model}`)
      appendLog('INFO', `生成模式: ${processConfig.mode}`)
      appendLog('INFO', `输出格式: ${processConfig.data_format}`)

      startProgressWs(response.job_id)
    } finally {
      submitting.value = false
    }
  }

  function handleReturnPool() {
    stopProgressWs()
    router.push({ name: 'DatasetHub' })
  }

  // ── WebSocket 进度连接 ────────────────────────────────────

  let progressWs: WebSocket | null = null
  let taskStartTime = 0
  let lastStageKey = ''

  function resolveWsBase(): string {
    const env = import.meta.env.VITE_WS_URL
    if (env) return env
    const api = import.meta.env.VITE_API_URL
    if (typeof api === 'string' && api.startsWith('http')) {
      return api.replace(/^http/, 'ws')
    }
    return 'ws://localhost:8088'
  }

  function startProgressWs(jobId: string) {
    stopProgressWs()
    const url = `${resolveWsBase()}/ws/progress?job_id=${jobId}`
    progressWs = new WebSocket(url)

    progressWs.onopen = () => {
      taskStartTime = Date.now()
      appendLog('INFO', '已连接任务进度通道')
    }

    progressWs.onmessage = (event: MessageEvent) => {
      try {
        const data = JSON.parse(event.data)

        if (data.type === 'engine_log') {
          appendEngineLog(data.line)
          return
        }

        if (data.type === 'heartbeat') {
          if (taskInfo.value && taskInfo.value.status === 'processing') {
            const elapsed = Math.round((Date.now() - taskStartTime) / 1000)
            const min = Math.floor(elapsed / 60)
            const sec = elapsed % 60
            taskInfo.value.eta = min > 0 ? `已运行 ${min}m${sec}s` : `已运行 ${sec}s`
          }
          return
        }

        const { stage, progress, status, message } = data

        if (taskInfo.value) {
          taskInfo.value.progress = Math.round(progress * 100)
          taskInfo.value.status =
            status === 'done'
              ? 'completed'
              : status === 'failed' || status === 'cancelled'
                ? 'failed'
                : status === 'running'
                  ? 'processing'
                  : 'pending'
          if (taskInfo.value.status === 'completed') {
            taskInfo.value.eta = '已完成'
          }
        }

        if (stage && status !== 'pending') {
          appendStageLog(stage, Math.round(progress * 100), status)
        }

        if (status === 'done') {
          if (taskInfo.value) {
            taskInfo.value.status = 'completed'
            taskInfo.value.progress = 100
            taskInfo.value.eta = '已完成'
          }
          appendLog('INFO', '任务执行完成！')
          stopProgressWs()
        } else if (status === 'failed') {
          if (taskInfo.value) {
            taskInfo.value.status = 'failed'
          }
          appendLog('ERROR', `任务失败: ${message || '未知错误'}`)
          stopProgressWs()
        }
      } catch (e) {
        console.error('[WS] 消息解析失败:', e)
      }
    }

    progressWs.onclose = () => {
      appendLog('WARN', '进度通道已断开')
      progressWs = null
    }

    progressWs.onerror = () => {
      if (
        taskInfo.value &&
        taskInfo.value.status !== 'completed' &&
        taskInfo.value.status !== 'failed'
      ) {
        appendLog('WARN', '进度通道连接异常')
      }
    }
  }

  function stopProgressWs() {
    if (progressWs) {
      progressWs.close(1000)
      progressWs = null
    }
  }

  function appendLog(level: 'INFO' | 'WARN' | 'ERROR', message: string) {
    const now = new Date()
    const time = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`
    taskLogs.value.push({ time, level, message })
  }

  function appendStageLog(stage: string, pct: number, status: string) {
    const now = new Date()
    const time = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`
    const level =
      status === 'done' ? 'STAGE_DONE' : status === 'failed' ? 'STAGE_ERROR' : 'STAGE_INPROGRESS'
    const displayMsg = status === 'failed' ? `▸ ${stage}` : `▸ ${stage}  ${pct}%`
    taskLogs.value.push({ time, level: level as any, message: displayMsg })
  }

  function appendEngineLog(line: string) {
    const now = new Date()
    const time = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`

    const levelMatch = line.match(/\] (DEBUG|INFO|WARNING|ERROR|CRITICAL) \[/)
    let level: 'INFO' | 'WARN' | 'ERROR' = 'INFO'
    if (levelMatch) {
      const raw = levelMatch[1]
      if (raw === 'WARNING') level = 'WARN'
      else if (raw === 'CRITICAL') level = 'ERROR'
      else if (raw === 'ERROR') level = 'ERROR'
      else level = 'INFO'
    }

    const MAX_LEN = 500
    const display = line.length > MAX_LEN ? line.slice(0, MAX_LEN) + '...' : line
    taskLogs.value.push({ time, level, message: display })
  }

  function handleBack() {
    stopProgressWs()
    router.push({ name: 'DatasetHub' })
  }

  function handleCancel() {
    stopProgressWs()
    router.push({ name: 'DatasetHub' })
  }

  function canClickStep(step: number): boolean {
    return currentStep.value >= step && currentStep.value !== step
  }

  function resetProcessConfig() {
    Object.assign(processConfig, { ...DEFAULT_PROCESS_CONFIG })
  }

  function handleStepClick(step: number) {
    if (!canClickStep(step)) return

    if (currentStep.value === 3) {
      stopProgressWs()
    }

    if (step === 1) {
      previousDatasetId.value = selectedDatasetId.value
      taskInfo.value = null
      taskLogs.value = []
    }

    if (step === 2) {
      taskInfo.value = null
      taskLogs.value = []
    }

    currentStep.value = step
  }

  function resetForNewTask() {
    stopProgressWs()
    taskInfo.value = null
    taskLogs.value = []
    currentJobId.value = null
    selectedDatasetId.value = null
    previousDatasetId.value = null
    resetProcessConfig()
    currentStep.value = 1
    lastStageKey = ''
    taskStartTime = 0
  }

  onDeactivated(() => {
    resetForNewTask()
  })

  onActivated(async () => {
    if (datasets.value.length === 0) {
      loading.value = true
      try {
        const result = await getDatasets()
        datasets.value = result.records
      } finally {
        loading.value = false
      }
    }
  })

  onMounted(async () => {
    loading.value = true
    try {
      const result = await getDatasets()
      datasets.value = result.records
    } finally {
      loading.value = false
    }
  })

  watch(
    () => route.query.datasetId,
    (newId) => {
      if (newId) {
        selectedDatasetId.value = Number(newId)
        currentStep.value = 2
      }
    },
    { immediate: true }
  )

  onUnmounted(() => {
    stopProgressWs()
  })
</script>

<style lang="scss" scoped>
  .data-processing-page {
    display: flex;
    flex-direction: column;
    height: calc(100vh - 120px);
    min-height: 600px;
    padding: 16px 20px;
  }

  // 步骤向导条
  .wizard-header {
    display: flex;
    align-items: center;
    padding: 12px 10px;
    background: #fff;
    margin-bottom: 16px;
    box-shadow: 0 1px 3px rgba(0, 0, 0, 0.06);
    gap: 32px;

    &__left {
      flex-shrink: 0;
    }

    &__steps {
      display: flex;
      align-items: center;
      flex: 1;
    }
  }

  .wizard-back-btn {
    color: var(--art-gray-600);
    &:hover {
      color: var(--el-color-primary);
    }
    margin-right: 200px;
  }

  .wizard-step {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 0 50px;
    position: relative;

    &::after {
      content: '';
      position: absolute;
      left: calc(100% - 30px);
      top: 50%;
      width: 60px;
      height: 2px;
      background: var(--art-gray-200);
      transform: translateY(-50%);
    }

    &:last-child::after {
      display: none;
    }

    &.is-active {
      .wizard-step__dot {
        background: var(--el-color-primary);
        color: #fff;
        border-color: var(--el-color-primary);
        box-shadow: 0 0 0 4px rgba(var(--el-color-primary-rgb, 64, 158, 255), 0.15);
      }
      .wizard-step__label {
        color: var(--el-color-primary);
        font-weight: 600;
      }
    }

    &.is-done {
      .wizard-step__dot {
        background: var(--el-color-primary);
        color: #fff;
        border-color: var(--el-color-primary);
      }
      .wizard-step__label {
        color: var(--el-color-primary);
      }
      &::after {
        background: var(--el-color-primary);
      }
    }

    &.is-clickable {
      .wizard-step__label {
        cursor: pointer;
        &:hover {
          color: var(--el-color-primary);
          font-weight: 600;
        }
      }
      .wizard-step__dot {
        cursor: pointer;
      }
    }

    &__dot {
      width: 25px;
      height: 25px;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      border: 2px solid var(--art-gray-300);
      background: #fff;
      color: var(--art-gray-500);
      font-size: 13px;
      font-weight: 600;
      flex-shrink: 0;
      transition: all 0.3s ease;
    }

    &__label {
      font-size: 14px;
      color: var(--art-gray-600);
      white-space: nowrap;
      transition: color 0.3s ease;
    }

    &__num {
      font-size: 13px;
    }
  }

  // 内容区
  .wizard-content {
    flex: 1;
    overflow: auto;
    min-height: 0;
  }

  // 底部操作栏
  .wizard-footer {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 16px;
  }
</style>
