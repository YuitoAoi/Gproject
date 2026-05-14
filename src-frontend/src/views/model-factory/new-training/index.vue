<template>
  <div class="new-training-page">
    <!-- 页头区域 -->
    <div class="page-header mb-5">
      <div class="flex items-center justify-between">
        <div>
          <h1 class="page-header__title">新建训练任务</h1>
          <p class="page-header__subtitle">配置模型微调参数，一键提交异步训练任务到后台队列。</p>
        </div>
      </div>
    </div>

    <!-- 步骤导航 + 表单区域 -->
    <div class="wizard-container">
      <!-- 左侧步骤导航 -->
      <div class="wizard-steps">
        <ElSteps :active="currentStep" direction="vertical" finish-status="success">
          <ElStep title="基础配置" description="模型与微调方法" />
          <ElStep title="数据集选择" description="选择训练数据" />
          <ElStep title="训练参数" description="超参数配置" />
          <ElStep title="确认提交" description="检查并提交任务" />
        </ElSteps>
      </div>

      <!-- 右侧表单内容 -->
      <div class="wizard-content">
        <div class="lfp-card wizard-form-card">
          <!-- Step 1: 基础配置 -->
          <div v-show="currentStep === 0">
            <Step1Basic ref="step1Ref" v-model="basicConfig" />
          </div>

          <!-- Step 2: 数据集选择 -->
          <div v-show="currentStep === 1">
            <Step2Dataset ref="step2Ref" v-model="datasetConfig" />
          </div>

          <!-- Step 3: 训练参数 -->
          <div v-show="currentStep === 2">
            <Step3Params
              ref="step3Ref"
              v-model="trainingParams"
              :config-mode="basicConfig.configMode"
              :finetune-method="basicConfig.finetuneMethod"
            />
          </div>

          <!-- Step 4: 确认提交 -->
          <div v-show="currentStep === 3">
            <Step4Confirm
              :basic-config="basicConfig"
              :dataset-config="datasetConfig"
              :training-params="trainingParams"
            />
          </div>

          <!-- 底部操作按钮 -->
          <div class="wizard-actions">
            <ElButton v-if="currentStep > 0" @click="handlePrev">
              <LfpSvgIcon icon="ri:arrow-left-line" class="mr-1" />
              上一步
            </ElButton>
            <div class="flex-1"></div>
            <ElButton v-if="currentStep < 3" type="primary" @click="handleNext">
              下一步
              <LfpSvgIcon icon="ri:arrow-right-line" class="ml-1" />
            </ElButton>
            <ElButton
              v-if="currentStep === 3"
              type="primary"
              :loading="submitting"
              @click="handleSubmit"
            >
              <LfpSvgIcon icon="ri:rocket-line" class="mr-1" />
              提交训练任务
            </ElButton>
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { ref } from 'vue'
  import { useRouter } from 'vue-router'
  import { ElMessage } from 'element-plus'
  import LfpSvgIcon from '@/components/core/base/lfp-svg-icon/index.vue'
  import Step1Basic from './modules/step1-basic.vue'
  import Step2Dataset from './modules/step2-dataset.vue'
  import Step3Params from './modules/step3-params.vue'
  import Step4Confirm from './modules/step4-confirm.vue'
  import { submitTraining } from '@/api/llamafactory'

  defineOptions({ name: 'NewTrainingPage' })

  const router = useRouter()

  const currentStep = ref(0)
  const submitting = ref(false)

  const step1Ref = ref<InstanceType<typeof Step1Basic> | null>(null)
  const step2Ref = ref<InstanceType<typeof Step2Dataset> | null>(null)
  const step3Ref = ref<InstanceType<typeof Step3Params> | null>(null)

  const basicConfig = ref({
    taskName: '',
    baseModel: 'Qwen/Qwen2.5-7B-Instruct',
    finetuneMethod: 'lora' as 'lora' | 'qlora' | 'full',
    configMode: 'beginner' as 'beginner' | 'expert'
  })

  const datasetConfig = ref({
    datasetId: null as number | null,
    datasetName: ''
  })

  const trainingParams = ref({
    epochs: 3,
    batchSize: 2,
    learningRate: 5e-5,
    maxSeqLength: 1024,
    loraRank: 8,
    loraAlpha: 16,
    loraDropout: 0.05,
    loraTarget: 'all',
    gradientAccumulationSteps: 4,
    weightDecay: 0.01,
    warmupRatio: 0.1,
    optimizer: 'adamw_torch',
    scheduler: 'cosine',
    fp16: false,
    bf16: true,
    gradientCheckpointing: true
  })

  const handleNext = async () => {
    try {
      if (currentStep.value === 0 && step1Ref.value) {
        await step1Ref.value.validate()
      } else if (currentStep.value === 1 && step2Ref.value) {
        await step2Ref.value.validate()
      } else if (currentStep.value === 2 && step3Ref.value) {
        await step3Ref.value.validate()
      }
      currentStep.value++
    } catch {
      ElMessage.warning('请完善当前步骤的必填项')
    }
  }

  const handlePrev = () => {
    currentStep.value--
  }

  const handleSubmit = async () => {
    submitting.value = true
    try {
      const p = trainingParams.value
      const resp = await submitTraining({
        task_name: basicConfig.value.taskName,
        base_model: basicConfig.value.baseModel,
        finetune_method: basicConfig.value.finetuneMethod,
        dataset_id: datasetConfig.value.datasetId!,
        params: {
          epochs: p.epochs,
          batch_size: p.batchSize,
          learning_rate: p.learningRate,
          max_seq_length: p.maxSeqLength,
          lora_rank: p.loraRank,
          lora_alpha: p.loraAlpha,
          lora_dropout: p.loraDropout,
          lora_target: p.loraTarget,
          gradient_accumulation_steps: p.gradientAccumulationSteps,
          weight_decay: p.weightDecay,
          warmup_ratio: p.warmupRatio,
          optimizer: p.optimizer,
          scheduler: p.scheduler,
          fp16: p.fp16,
          bf16: p.bf16,
          gradient_checkpointing: p.gradientCheckpointing,
        }
      })
      if (resp.success) {
        ElMessage.success('训练任务已提交，正在跳转到任务调度中心...')
        setTimeout(() => {
          router.push('/workbench/task-dispatch')
        }, 1500)
      } else {
        ElMessage.error('提交失败: ' + (resp.error || '未知错误'))
      }
    } catch (err: any) {
      ElMessage.error('提交失败: ' + (err.message || '未知错误'))
    } finally {
      submitting.value = false
    }
  }
</script>

<style lang="scss" scoped>
  .new-training-page {
    padding: 16px 20px;
  }

  .page-header {
    position: relative;
    display: flex;
    flex-direction: column;
    justify-content: center;
    padding: 20px 2rem;
    overflow: hidden;
    color: white;
    background-color: color-mix(in srgb, var(--el-color-primary) 60%, transparent);
    border-radius: calc(var(--custom-radius, 8px) + 2px);

    &::after {
      position: absolute;
      right: -10%;
      bottom: -20%;
      width: 60%;
      height: 140%;
      content: '';
      background: rgb(255 255 255 / 12%);
      border-radius: 30%;
      transform: rotate(-20deg);
    }

    &__title {
      position: relative;
      z-index: 1;
      margin: 0 0 0.25rem;
      font-size: 1.5rem;
      font-weight: 700;
      color: #fff;
    }

    &__subtitle {
      position: relative;
      z-index: 1;
      margin: 0;
      font-size: 0.9rem;
      opacity: 0.9;
      color: #fff;
    }
  }

  .wizard-container {
    display: grid;
    grid-template-columns: 220px 1fr;
    gap: 20px;
    min-height: 600px;
  }

  .wizard-steps {
    padding: 24px 16px;
    background: var(--el-fill-color-lighter);
    border-radius: var(--custom-radius, 8px);
    border: 1px solid var(--lfp-gray-200);

    :deep(.el-steps) {
      .el-step__title {
        font-size: 14px;
        font-weight: 600;
      }

      .el-step__description {
        font-size: 12px;
      }
    }
  }

  .wizard-form-card {
    padding: 24px;
    min-height: 560px;
    display: flex;
    flex-direction: column;
  }

  .wizard-actions {
    display: flex;
    align-items: center;
    padding-top: 20px;
    margin-top: auto;
    border-top: 1px solid var(--lfp-gray-200);
  }
</style>
