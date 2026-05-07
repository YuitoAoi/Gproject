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
        <ElButton v-if="currentStep > 1" @click="currentStep--"> 上一步 </ElButton>
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
  import { getDatasets, getDatasetDetail, processDataset, type DatasetItemDTO } from '@/api/dataset'
  import Step1DataSource from './modules/step1-datasource.vue'
  import Step2Mapping from './modules/step2-mapping.vue'
  import Step3Execution from './modules/step3-execution.vue'

  defineOptions({ name: 'DataProcessingPage' })

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
    api_key: '',
    synthesizer_url: 'https://api.openai.com/v1',
    synthesizer_model: 'gpt-4',
    mode: 'atomic',
    data_format: 'Alpaca',
    tokenizer: 'cl100k_base',
    chunk_size: 1024,
    chunk_overlap: 100,
    quiz_samples: 2,
    partition_method: 'ece',
    rpm: 1000,
    tpm: 50000
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

      // 初始化 mock 日志
      taskLogs.value = []
      appendLog('INFO', `任务已提交，Job ID: ${response.job_id}`)
      appendLog('INFO', `正在初始化处理流程...`)
      appendLog('INFO', `使用模型: ${processConfig.synthesizer_model}`)
      appendLog('INFO', `生成模式: ${processConfig.mode}`)
      appendLog('INFO', `输出格式: ${processConfig.data_format}`)

      // 启动轮询
      startPolling()

      // 启动 mock 日志模拟
      startMockLogs()
    } finally {
      submitting.value = false
    }
  }

  function handleReturnPool() {
    stopPolling()
    router.push({ name: 'DatasetHub' })
  }

  const pollingInterval = ref<ReturnType<typeof setInterval> | null>(null)
  const mockLogInterval = ref<ReturnType<typeof setInterval> | null>(null)
  let mockProgress = 0

  function startPolling() {
    stopPolling()
    pollingInterval.value = setInterval(async () => {
      if (!selectedDatasetId.value || !taskInfo.value) return

      try {
        const dataset = await getDatasetDetail(selectedDatasetId.value)
        if (!dataset) return

        // 根据 dataset status 推断任务状态
        // status: 0=初始化, 1=处理中, 2=已完成, 3=失败
        if (taskInfo.value.status === 'pending' || taskInfo.value.status === 'processing') {
          if (dataset.status === 2) {
            taskInfo.value.status = 'completed'
            taskInfo.value.progress = 100
            taskInfo.value.eta = '已完成'
            taskInfo.value.finalCount =
              taskInfo.value.rawCount > 0 ? Math.floor(taskInfo.value.rawCount * 0.7) : 0
            appendLog('INFO', '任务执行完成！')
            appendLog('INFO', `最终产出: ${taskInfo.value.finalCount} 条`)
            stopPolling()
          } else if (dataset.status === 3) {
            taskInfo.value.status = 'failed'
            appendLog('ERROR', '任务执行失败')
            stopPolling()
          } else if (dataset.status === 1) {
            taskInfo.value.status = 'processing'
          }
        }
      } catch {
        /* 忽略轮询错误 */
      }
    }, 3000)
  }

  function stopPolling() {
    if (pollingInterval.value) {
      clearInterval(pollingInterval.value)
      pollingInterval.value = null
    }
    if (mockLogInterval.value) {
      clearInterval(mockLogInterval.value)
      mockLogInterval.value = null
    }
  }

  function appendLog(level: 'INFO' | 'WARN' | 'ERROR', message: string) {
    const now = new Date()
    const time = `${now.getHours().toString().padStart(2, '0')}:${now.getMinutes().toString().padStart(2, '0')}:${now.getSeconds().toString().padStart(2, '0')}`
    taskLogs.value.push({ time, level, message })
  }

  function startMockLogs() {
    if (mockLogInterval.value) {
      clearInterval(mockLogInterval.value)
    }
    mockProgress = 0

    const phases = [
      { msg: '正在连接 LLM 服务...', delay: 800 },
      { msg: 'LLM 服务连接成功', delay: 1200 },
      { msg: '开始加载数据集...', delay: 800 },
      { msg: '数据集加载完成，共 10,000 条记录', delay: 1000 },
      { msg: '开始图构建阶段...', delay: 1500 },
      { msg: '图节点提取中: 10%', delay: 2000 },
      { msg: '图节点提取中: 25%', delay: 2500 },
      { msg: '图边关系建立中: 40%', delay: 2000 },
      { msg: '图分区完成，开始生成问答对...', delay: 1500 },
      { msg: '问答生成中: 60%', delay: 3000 },
      { msg: '问答生成中: 80%', delay: 2500 },
      { msg: '数据格式化输出中...', delay: 1000 }
    ]

    let idx = 0
    const runPhase = () => {
      if (
        idx >= phases.length ||
        !taskInfo.value ||
        taskInfo.value.status === 'completed' ||
        taskInfo.value.status === 'failed'
      ) {
        return
      }
      const phase = phases[idx]
      appendLog('INFO', phase.msg)
      mockProgress = Math.min(mockProgress + 8, 92)
      if (taskInfo.value) {
        taskInfo.value.progress = mockProgress
        const remaining = Math.max(1, Math.round((100 - mockProgress) * 0.3))
        taskInfo.value.eta = `约 ${remaining} 秒`
      }
      idx++
      mockLogInterval.value = setTimeout(runPhase, phase.delay)
    }

    runPhase()
  }

  function handleBack() {
    stopPolling()
    router.push({ name: 'DatasetHub' })
  }

  function handleCancel() {
    stopPolling()
    router.push({ name: 'DatasetHub' })
  }

  function canClickStep(step: number): boolean {
    return currentStep.value >= step && currentStep.value !== step
  }

  function resetProcessConfig() {
    Object.assign(processConfig, {
      api_key: '',
      synthesizer_url: 'https://api.openai.com/v1',
      synthesizer_model: 'gpt-4',
      mode: 'atomic',
      data_format: 'Alpaca',
      tokenizer: 'cl100k_base',
      chunk_size: 1024,
      chunk_overlap: 100,
      quiz_samples: 2,
      partition_method: 'ece',
      rpm: 1000,
      tpm: 50000
    })
  }

  function handleStepClick(step: number) {
    if (!canClickStep(step)) return

    if (currentStep.value === 3) {
      stopPolling()
    }

    if (step === 1) {
      previousDatasetId.value = selectedDatasetId.value
      selectedDatasetId.value = null
      taskInfo.value = null
      taskLogs.value = []
    }

    if (step === 2) {
      resetProcessConfig()
      taskInfo.value = null
      taskLogs.value = []
    }

    currentStep.value = step
  }

  onMounted(async () => {
    loading.value = true
    try {
      const result = await getDatasets()
      datasets.value = result.records

      // 场景B：从数据集管理页的"去清洗"按钮跳转，携带dataset_id
      const datasetId = route.query.datasetId
      if (datasetId) {
        selectedDatasetId.value = Number(datasetId)
        currentStep.value = 2
      }
    } finally {
      loading.value = false
    }
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
