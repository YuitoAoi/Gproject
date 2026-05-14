<template>
  <div class="step4-confirm">
    <div class="step-title mb-6">
      <LfpSvgIcon icon="ri:file-check-line" class="text-xl text-primary mr-2" />
      <span class="text-lg font-semibold">确认提交</span>
      <span class="text-sm text-g-500 ml-2">请检查以下配置信息，确认无误后提交训练任务</span>
    </div>

    <!-- 基础配置 -->
    <div class="confirm-section">
      <h3 class="confirm-section__title">
        <LfpSvgIcon icon="ri:settings-3-line" class="mr-1.5" />基础配置
      </h3>
      <ElDescriptions :column="2" border>
        <ElDescriptionsItem label="任务名称">{{ basicConfig.taskName }}</ElDescriptionsItem>
        <ElDescriptionsItem label="基础模型">
          <ElTag size="small" effect="plain">{{ basicConfig.baseModel }}</ElTag>
        </ElDescriptionsItem>
        <ElDescriptionsItem label="微调方法">
          <ElTag :type="methodTagType" size="small" effect="dark">{{ methodLabel }}</ElTag>
        </ElDescriptionsItem>
        <ElDescriptionsItem label="配置模式">
          {{ basicConfig.configMode === 'beginner' ? '新手模式' : '专家模式' }}
        </ElDescriptionsItem>
      </ElDescriptions>
    </div>

    <!-- 数据集配置 -->
    <div class="confirm-section">
      <h3 class="confirm-section__title">
        <LfpSvgIcon icon="ri:database-2-line" class="mr-1.5" />数据集
      </h3>
      <ElDescriptions :column="2" border>
        <ElDescriptionsItem label="数据集名称">{{ datasetConfig.datasetName || '—' }}</ElDescriptionsItem>
        <ElDescriptionsItem label="数据集ID">{{ datasetConfig.datasetId ?? '—' }}</ElDescriptionsItem>
      </ElDescriptions>
    </div>

    <!-- 训练参数 -->
    <div class="confirm-section">
      <h3 class="confirm-section__title">
        <LfpSvgIcon icon="ri:settings-4-line" class="mr-1.5" />训练参数
      </h3>
      <ElDescriptions :column="2" border>
        <ElDescriptionsItem label="训练轮数">{{ trainingParams.epochs }}</ElDescriptionsItem>
        <ElDescriptionsItem label="批次大小">{{ trainingParams.batchSize }}</ElDescriptionsItem>
        <ElDescriptionsItem label="学习率">{{ trainingParams.learningRate }}</ElDescriptionsItem>
        <ElDescriptionsItem label="最大序列长度">{{ trainingParams.maxSeqLength }}</ElDescriptionsItem>
      </ElDescriptions>

      <!-- LoRA 参数（专家模式 + LoRA 方法） -->
      <template v-if="isLoraMethod && basicConfig.configMode === 'expert'">
        <h4 class="confirm-subsection__title mt-4">LoRA 参数</h4>
        <ElDescriptions :column="2" border>
          <ElDescriptionsItem label="LoRA Rank">{{ trainingParams.loraRank }}</ElDescriptionsItem>
          <ElDescriptionsItem label="LoRA Alpha">{{ trainingParams.loraAlpha }}</ElDescriptionsItem>
          <ElDescriptionsItem label="LoRA Dropout">{{ trainingParams.loraDropout }}</ElDescriptionsItem>
          <ElDescriptionsItem label="LoRA Target">{{ trainingParams.loraTarget }}</ElDescriptionsItem>
        </ElDescriptions>
      </template>

      <!-- 专家模式额外参数 -->
      <template v-if="basicConfig.configMode === 'expert'">
        <h4 class="confirm-subsection__title mt-4">高级参数</h4>
        <ElDescriptions :column="2" border>
          <ElDescriptionsItem label="梯度累积步数">{{ trainingParams.gradientAccumulationSteps }}</ElDescriptionsItem>
          <ElDescriptionsItem label="权重衰减">{{ trainingParams.weightDecay }}</ElDescriptionsItem>
          <ElDescriptionsItem label="Warmup Ratio">{{ trainingParams.warmupRatio }}</ElDescriptionsItem>
          <ElDescriptionsItem label="优化器">{{ trainingParams.optimizer }}</ElDescriptionsItem>
          <ElDescriptionsItem label="学习率调度器">{{ trainingParams.scheduler }}</ElDescriptionsItem>
          <ElDescriptionsItem label="精度">
            <ElTag v-if="trainingParams.bf16" size="small" type="primary" effect="plain" class="mr-1">BF16</ElTag>
            <ElTag v-if="trainingParams.fp16" size="small" type="warning" effect="plain" class="mr-1">FP16</ElTag>
            <span v-if="!trainingParams.bf16 && !trainingParams.fp16">FP32</span>
          </ElDescriptionsItem>
          <ElDescriptionsItem label="梯度检查点">
            <ElTag :type="trainingParams.gradientCheckpointing ? 'success' : 'info'" size="small" effect="plain">
              {{ trainingParams.gradientCheckpointing ? '已启用' : '未启用' }}
            </ElTag>
          </ElDescriptionsItem>
        </ElDescriptions>
      </template>
    </div>

    <!-- 显存预估提醒 -->
    <ElAlert
      :title="vramAlertTitle"
      :description="vramAlertDesc"
      :type="vramAlertType"
      show-icon
      :closable="false"
      class="mb-5"
    />

    <!-- 提交前提示 -->
    <div class="tips-card">
      <div class="tips-card__header">
        <LfpSvgIcon icon="ri:lightbulb-line" class="text-warning mr-2" />
        <span class="font-medium">提交须知</span>
      </div>
      <ul class="tips-list">
        <li>训练任务将被推入后台队列异步执行，提交后可在<strong>任务调度中心</strong>查看进度。</li>
        <li>训练过程中请勿关闭后端服务，否则任务将被中断。</li>
        <li>训练完成后的模型文件将保存在服务器本地输出目录中。</li>
        <li>如果显存不足，建议减小批次大小或使用 QLoRA 方法。</li>
      </ul>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { computed } from 'vue'
  import LfpSvgIcon from '@/components/core/base/lfp-svg-icon/index.vue'

  interface BasicConfig {
    taskName: string
    baseModel: string
    finetuneMethod: 'lora' | 'qlora' | 'full'
    configMode: 'beginner' | 'expert'
  }

  interface DatasetConfig {
    datasetId: number | null
    datasetName: string
  }

  interface TrainingParams {
    epochs: number
    batchSize: number
    learningRate: number
    maxSeqLength: number
    loraRank: number
    loraAlpha: number
    loraDropout: number
    loraTarget: string
    gradientAccumulationSteps: number
    weightDecay: number
    warmupRatio: number
    optimizer: string
    scheduler: string
    fp16: boolean
    bf16: boolean
    gradientCheckpointing: boolean
  }

  const props = defineProps<{
    basicConfig: BasicConfig
    datasetConfig: DatasetConfig
    trainingParams: TrainingParams
  }>()

  const isLoraMethod = computed(() =>
    props.basicConfig.finetuneMethod === 'lora' || props.basicConfig.finetuneMethod === 'qlora'
  )

  const methodLabel = computed(() => {
    const map: Record<string, string> = { lora: 'LoRA 微调', qlora: 'QLoRA 微调', full: '全量微调' }
    return map[props.basicConfig.finetuneMethod] || props.basicConfig.finetuneMethod
  })

  const methodTagType = computed(() => {
    const map: Record<string, string> = { lora: 'success', qlora: 'warning', full: 'danger' }
    return (map[props.basicConfig.finetuneMethod] || 'info') as 'success' | 'warning' | 'danger' | 'info'
  })

  /** 显存预估 */
  const estimatedVram = computed(() => {
    const modelSizeMap: Record<number, number> = { 512: -1, 1024: 0, 2048: 1, 4096: 3 }
    let base = 0
    const method = props.basicConfig.finetuneMethod
    if (method === 'lora') base = 8
    else if (method === 'qlora') base = 5
    else base = 16

    const seqAdj = modelSizeMap[props.trainingParams.maxSeqLength] ?? 0
    const batchAdj = (props.trainingParams.batchSize - 1) * 1.5
    const checkpointSave = props.trainingParams.gradientCheckpointing ? -2 : 0
    return Math.max(2, Math.round((base + seqAdj + batchAdj + checkpointSave) * 10) / 10)
  })

  const vramPercent = computed(() => Math.min(100, Math.round((estimatedVram.value / 24) * 100)))

  const vramAlertType = computed(() => {
    if (vramPercent.value <= 50) return 'success'
    if (vramPercent.value <= 75) return 'warning'
    return 'error'
  })

  const vramAlertTitle = computed(() => `显存预估: ~${estimatedVram.value} GB / 24 GB (${vramPercent.value}%)`)

  const vramAlertDesc = computed(() => {
    if (vramPercent.value <= 50) return '当前配置显存占用充裕，可以安全提交训练任务。'
    if (vramPercent.value <= 75) return '当前配置显存占用适中，请确保没有其他程序占用 GPU。'
    return '当前配置显存占用较高，可能导致 OOM 错误。建议减小批次大小、序列长度或切换为 QLoRA。'
  })
</script>

<style lang="scss" scoped>
  .step4-confirm {
    flex: 1;
  }

  .step-title {
    display: flex;
    align-items: center;
  }

  .confirm-section {
    margin-bottom: 24px;

    &__title {
      display: flex;
      align-items: center;
      font-size: 14px;
      font-weight: 600;
      color: var(--lfp-gray-800);
      margin: 0 0 12px;
    }
  }

  .confirm-subsection__title {
    font-size: 13px;
    font-weight: 600;
    color: var(--lfp-gray-700);
    margin: 0 0 8px;
  }

  .tips-card {
    padding: 16px 20px;
    background: var(--el-fill-color-lighter);
    border-radius: var(--custom-radius, 8px);
    border: 1px solid var(--lfp-gray-200);

    &__header {
      display: flex;
      align-items: center;
      margin-bottom: 12px;
    }
  }

  .tips-list {
    margin: 0;
    padding-left: 20px;
    list-style: disc;

    li {
      font-size: 13px;
      color: var(--lfp-gray-600);
      line-height: 2;
    }
  }
</style>
