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
          <span
            class="wizard-step__label"
            @click="handleStepClick(idx + 1)"
          >{{ step.label }}</span>
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
        :config="cleaningConfig"
        @update:config="handleConfigUpdate"
        @refresh-samples="handleRefreshSamples"
      />
      <Step3Execution
        v-if="currentStep === 3"
        :task="taskInfo"
        :logs="taskLogs"
        :config="cleaningConfig"
        @return-pool="handleReturnPool"
      />
    </div>

    <!-- ========== 底部操作栏 ========== -->
    <div class="wizard-footer" v-if="currentStep !== 3">
      <ElButton @click="handleCancel">取消</ElButton>
      <div class="flex gap-3">
        <ElButton
          v-if="currentStep > 1"
          @click="currentStep--"
        >
          上一步
        </ElButton>
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
import { fetchGetDatasetListMock, fetchSubmitCleaningTaskMock, fetchGetProcessingTaskMock, fetchGetProcessingLogsMock, fetchGetDefaultCleaningConfigMock } from '@/api/data-manage'
import type { DatasetItem } from '@/mock/temp/formData'
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
const datasets = ref<DatasetItem[]>([])
const submitting = ref(false)

const cleaningConfig = reactive<Api.DataManage.DataProcessing.CleaningConfig>({
  fieldMapping: { instruction: '', input: '', output: '' },
  filters: { dropEmpty: true, dropShortText: true, minLength: 10 },
  formatters: { stripHtml: true, unifyPunctuation: false },
  piiMaskers: { phone: true, idCard: false, email: true, bankCard: false },
  deduplication: { enabled: true, threshold: 0.85 }
})

const taskInfo = ref<Api.DataManage.DataProcessing.ProcessingTask | null>(null)
const taskLogs = ref<Api.DataManage.DataProcessing.ProcessingLog[]>([])

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

function handleConfigUpdate(config: Api.DataManage.DataProcessing.CleaningConfig) {
  Object.assign(cleaningConfig, config)
}

function handleRefreshSamples() { }

async function handleNextStep() {
  if (!selectedDatasetId.value) return

  // 如果选择的数据集与上次不同，重置配置
  if (previousDatasetId.value !== null && previousDatasetId.value !== selectedDatasetId.value) {
    resetCleaningConfig()
  }

  currentStep.value = 2
}

async function handleSubmitTask() {
  submitting.value = true
  try {
    const configToSend = { ...cleaningConfig, fieldMapping: { ...cleaningConfig.fieldMapping } }
    // 将 "__NONE__" 转回空字符串发送
    if (configToSend.fieldMapping.input === '__NONE__') {
      configToSend.fieldMapping.input = ''
    }
    const { taskId } = await fetchSubmitCleaningTaskMock(configToSend)
    currentStep.value = 3

    const [task, logs] = await Promise.all([
      fetchGetProcessingTaskMock(taskId),
      fetchGetProcessingLogsMock(taskId)
    ])
    taskInfo.value = task
    taskLogs.value = logs
  } finally {
    submitting.value = false
  }
}

function handleReturnPool() {
  router.push({ name: 'DatasetHub' })
}

function handleBack() {
  router.push({ name: 'DatasetHub' })
}

function handleCancel() {
  router.push({ name: 'DatasetHub' })
}

function canClickStep(step: number): boolean {
  return currentStep.value >= step && currentStep.value !== step
}

function resetCleaningConfig() {
  Object.assign(cleaningConfig, {
    fieldMapping: { instruction: '', input: '', output: '' },
    filters: { dropEmpty: true, dropShortText: true, minLength: 10 },
    formatters: { stripHtml: true, unifyPunctuation: false },
    piiMaskers: { phone: true, idCard: false, email: true, bankCard: false },
    deduplication: { enabled: true, threshold: 0.85 }
  })
}

function handleStepClick(step: number) {
  if (!canClickStep(step)) return

  if (step === 1) {
    previousDatasetId.value = selectedDatasetId.value
    selectedDatasetId.value = null
    taskInfo.value = null
    taskLogs.value = []
  }

  if (step === 2) {
    resetCleaningConfig()
    taskInfo.value = null
    taskLogs.value = []
  }

  currentStep.value = step
}

onMounted(async () => {
  loading.value = true
  try {
    const result = await fetchGetDatasetListMock({ current: 1, size: 50 })
    datasets.value = result.records as unknown as DatasetItem[]

    const defaultConfig = await fetchGetDefaultCleaningConfigMock()
    Object.assign(cleaningConfig, defaultConfig)

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
  &:hover { color: var(--el-color-primary); }
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

  &:last-child::after { display: none; }

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
    .wizard-step__label { color: var(--el-color-primary); }
    &::after { background: var(--el-color-primary); }
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
