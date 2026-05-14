<template>
  <div class="step3-params">
    <div class="step-title mb-6">
      <LfpSvgIcon icon="ri:settings-4-line" class="text-xl text-primary mr-2" />
      <span class="text-lg font-semibold">训练参数</span>
      <span class="text-sm text-g-500 ml-2">
        {{ configMode === 'beginner' ? '系统已推荐最佳参数' : '自定义所有超参数' }}
      </span>
    </div>

    <!-- 新手模式提示 -->
    <ElAlert
      v-if="configMode === 'beginner'"
      title="新手模式已启用"
      description="系统已根据所选模型自动推荐训练参数，您只需关注以下核心参数即可。如需完全自定义，请返回第一步切换为专家模式。"
      type="info"
      show-icon
      :closable="false"
      class="mb-5"
    />

    <ElForm ref="formRef" :model="form" :rules="rules" label-position="top" class="param-form">
      <!-- ═══ 核心参数（新手 + 专家都显示） ═══ -->
      <div class="param-section">
        <h3 class="param-section__title">
          <LfpSvgIcon icon="ri:dashboard-line" class="mr-1.5" />核心参数
        </h3>
        <div class="param-grid">
          <ElFormItem label="训练轮数 (Epochs)" prop="epochs">
            <ElInputNumber v-model="form.epochs" :min="1" :max="100" :step="1" controls-position="right" class="!w-full" />
            <div class="param-hint">完整遍历数据集的次数，通常 3~10 轮</div>
          </ElFormItem>
          <ElFormItem label="批次大小 (Batch Size)" prop="batchSize">
            <ElInputNumber v-model="form.batchSize" :min="1" :max="64" :step="1" controls-position="right" class="!w-full" />
            <div class="param-hint">每次送入模型的样本数，越大显存占用越高</div>
          </ElFormItem>
          <ElFormItem label="学习率 (Learning Rate)" prop="learningRate">
            <ElInputNumber v-model="form.learningRate" :min="0.000001" :max="0.01" :step="0.00001" :precision="6" controls-position="right" class="!w-full" />
            <div class="param-hint">参数更新步长，推荐 1e-5 ~ 5e-5</div>
          </ElFormItem>
          <ElFormItem label="最大序列长度" prop="maxSeqLength">
            <ElSelect v-model="form.maxSeqLength" class="!w-full">
              <ElOption :value="512" label="512" />
              <ElOption :value="1024" label="1024" />
              <ElOption :value="2048" label="2048" />
              <ElOption :value="4096" label="4096" />
            </ElSelect>
            <div class="param-hint">输入文本截断长度，越长显存占用越高</div>
          </ElFormItem>
        </div>
      </div>

      <!-- ═══ 以下仅专家模式显示 ═══ -->
      <template v-if="configMode === 'expert'">
        <!-- LoRA 参数（仅 lora / qlora） -->
        <div v-if="showLoraParams" class="param-section">
          <h3 class="param-section__title">
            <LfpSvgIcon icon="ri:flashlight-line" class="mr-1.5" />LoRA 参数
          </h3>
          <div class="param-grid">
            <ElFormItem label="LoRA Rank" prop="loraRank">
              <ElSelect v-model="form.loraRank" class="!w-full">
                <ElOption :value="4" label="4 (轻量)" />
                <ElOption :value="8" label="8 (推荐)" />
                <ElOption :value="16" label="16" />
                <ElOption :value="32" label="32" />
                <ElOption :value="64" label="64 (高精度)" />
              </ElSelect>
              <div class="param-hint">低秩矩阵的秩，越大可学习参数越多</div>
            </ElFormItem>
            <ElFormItem label="LoRA Alpha" prop="loraAlpha">
              <ElInputNumber v-model="form.loraAlpha" :min="1" :max="128" :step="1" controls-position="right" class="!w-full" />
              <div class="param-hint">缩放因子，通常设为 Rank 的 2 倍</div>
            </ElFormItem>
            <ElFormItem label="LoRA Dropout" prop="loraDropout">
              <ElInputNumber v-model="form.loraDropout" :min="0" :max="0.5" :step="0.01" :precision="2" controls-position="right" class="!w-full" />
              <div class="param-hint">Dropout 比例，防止过拟合</div>
            </ElFormItem>
            <ElFormItem label="LoRA Target" prop="loraTarget">
              <ElSelect v-model="form.loraTarget" class="!w-full">
                <ElOption value="all" label="all (所有线性层)" />
                <ElOption value="q_proj,v_proj" label="q_proj,v_proj" />
                <ElOption value="q_proj,k_proj,v_proj,o_proj" label="q_proj,k_proj,v_proj,o_proj" />
              </ElSelect>
              <div class="param-hint">应用 LoRA 适配器的目标模块</div>
            </ElFormItem>
          </div>
        </div>

        <!-- 优化器与调度器 -->
        <div class="param-section">
          <h3 class="param-section__title">
            <LfpSvgIcon icon="ri:speed-line" class="mr-1.5" />优化器与调度
          </h3>
          <div class="param-grid">
            <ElFormItem label="梯度累积步数" prop="gradientAccumulationSteps">
              <ElInputNumber v-model="form.gradientAccumulationSteps" :min="1" :max="64" :step="1" controls-position="right" class="!w-full" />
              <div class="param-hint">模拟更大 Batch，等效 Batch = 批次大小 x 累积步数</div>
            </ElFormItem>
            <ElFormItem label="权重衰减 (Weight Decay)" prop="weightDecay">
              <ElInputNumber v-model="form.weightDecay" :min="0" :max="1" :step="0.001" :precision="3" controls-position="right" class="!w-full" />
              <div class="param-hint">正则化系数，防止过拟合，推荐 0.01</div>
            </ElFormItem>
            <ElFormItem label="Warmup Ratio" prop="warmupRatio">
              <ElInputNumber v-model="form.warmupRatio" :min="0" :max="0.5" :step="0.01" :precision="2" controls-position="right" class="!w-full" />
              <div class="param-hint">预热阶段占总训练步数的比例</div>
            </ElFormItem>
            <ElFormItem label="优化器" prop="optimizer">
              <ElSelect v-model="form.optimizer" class="!w-full">
                <ElOption value="adamw_torch" label="AdamW (PyTorch)" />
                <ElOption value="adamw_hf" label="AdamW (HuggingFace)" />
                <ElOption value="sgd" label="SGD" />
                <ElOption value="adafactor" label="Adafactor" />
              </ElSelect>
            </ElFormItem>
            <ElFormItem label="学习率调度器" prop="scheduler">
              <ElSelect v-model="form.scheduler" class="!w-full">
                <ElOption value="cosine" label="Cosine (推荐)" />
                <ElOption value="linear" label="Linear" />
                <ElOption value="constant" label="Constant" />
                <ElOption value="cosine_with_restarts" label="Cosine with Restarts" />
              </ElSelect>
            </ElFormItem>
          </div>
        </div>

        <!-- 精度与显存优化 -->
        <div class="param-section">
          <h3 class="param-section__title">
            <LfpSvgIcon icon="ri:cpu-line" class="mr-1.5" />精度与显存优化
          </h3>
          <div class="switch-grid">
            <div class="switch-item">
              <div class="switch-item__info">
                <span class="switch-item__label">FP16 半精度</span>
                <span class="switch-item__desc">使用 16 位浮点数，减少显存占用（NVIDIA GPU）</span>
              </div>
              <ElSwitch v-model="form.fp16" @change="handleFp16Change" />
            </div>
            <div class="switch-item">
              <div class="switch-item__info">
                <span class="switch-item__label">BF16 半精度</span>
                <span class="switch-item__desc">Brain Float 16，推荐 A100/H100 等新架构 GPU</span>
              </div>
              <ElSwitch v-model="form.bf16" @change="handleBf16Change" />
            </div>
            <div class="switch-item">
              <div class="switch-item__info">
                <span class="switch-item__label">梯度检查点</span>
                <span class="switch-item__desc">以计算换显存，显著降低显存占用但训练速度略降</span>
              </div>
              <ElSwitch v-model="form.gradientCheckpointing" />
            </div>
          </div>
        </div>
      </template>

      <!-- ═══ 显存预估卡片 ═══ -->
      <div class="vram-card">
        <div class="vram-card__header">
          <LfpSvgIcon icon="ri:memory-device-line" class="text-lg mr-2" />
          <span class="font-semibold">显存预估</span>
          <ElTag :type="vramLevel.type" size="small" effect="dark" class="ml-auto">
            {{ vramLevel.label }}
          </ElTag>
        </div>
        <ElProgress
          :percentage="vramPercent"
          :stroke-width="12"
          :color="vramLevel.color"
          :show-text="false"
          class="mb-3"
        />
        <div class="flex justify-between text-sm">
          <span class="text-g-600">预估占用: ~{{ estimatedVram }} GB</span>
          <span class="text-g-400">参考 GPU: 24 GB (RTX 4090)</span>
        </div>
      </div>
    </ElForm>
  </div>
</template>

<script setup lang="ts">
  import { computed, ref, watch } from 'vue'
  import type { FormInstance, FormRules } from 'element-plus'
  import LfpSvgIcon from '@/components/core/base/lfp-svg-icon/index.vue'

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
    modelValue: TrainingParams
    configMode: 'beginner' | 'expert'
    finetuneMethod: 'lora' | 'qlora' | 'full'
    modelSize: number
  }>()

  const emit = defineEmits<{
    'update:modelValue': [value: TrainingParams]
  }>()
  void props.modelSize // suppress unused warning

  const formRef = ref<FormInstance>()

  const form = computed({
    get: () => props.modelValue,
    set: (val) => emit('update:modelValue', val)
  })

  const showLoraParams = computed(() =>
    props.finetuneMethod === 'lora' || props.finetuneMethod === 'qlora'
  )

  interface RecommendedParams {
    epochs: number
    batchSize: number
    learningRate: number
    maxSeqLength: number
    loraRank: number
    loraAlpha: number
    gradientCheckpointing: boolean
  }

  function getRecommendedParams(modelSize: number, method: string): RecommendedParams {
    // 根据模型参数量推荐 batch_size 和学习率
    const batchSize = modelSize <= 3 ? 8 : modelSize <= 7 ? 4 : modelSize <= 14 ? 2 : 1
    const learningRate = modelSize <= 3 ? 5e-5 : modelSize <= 7 ? 3e-5 : modelSize <= 14 ? 2e-5 : 1e-5
    const maxSeqLength = modelSize >= 14 ? 512 : modelSize >= 7 ? 1024 : 2048
    return {
      epochs: 3,
      batchSize,
      learningRate,
      maxSeqLength,
      loraRank: 8,
      loraAlpha: 16,
      gradientCheckpointing: true
    }
  }

  function applyRecommendedParams() {
    const params = getRecommendedParams(props.modelSize, props.finetuneMethod)
    emit('update:modelValue', { ...props.modelValue, ...params })
  }

  watch(
    () => props.modelSize,
    () => {
      if (props.configMode === 'beginner') {
        applyRecommendedParams()
      }
    }
  )

  watch(
    () => props.configMode,
    (mode) => {
      if (mode === 'beginner') {
        applyRecommendedParams()
      }
    }
  )

  /** FP16 和 BF16 互斥 */
  function handleFp16Change(val: boolean | string | number) {
    if (val) {
      emit('update:modelValue', { ...props.modelValue, bf16: false })
    }
  }

  function handleBf16Change(val: boolean | string | number) {
    if (val) {
      emit('update:modelValue', { ...props.modelValue, fp16: false })
    }
  }

  /** 粗略显存预估（GB） */
  const estimatedVram = computed(() => {
    const modelSizeMap: Record<number, number> = {
      512: -1, 1024: 0, 2048: 1, 4096: 3
    }
    let base = 0
    const method = props.finetuneMethod
    if (method === 'lora') base = 8
    else if (method === 'qlora') base = 5
    else base = 16

    const seqAdj = modelSizeMap[form.value.maxSeqLength] ?? 0
    const batchAdj = (form.value.batchSize - 1) * 1.5
    const checkpointSave = form.value.gradientCheckpointing ? -2 : 0

    return Math.max(2, Math.round((base + seqAdj + batchAdj + checkpointSave) * 10) / 10)
  })

  const vramPercent = computed(() => Math.min(100, Math.round((estimatedVram.value / 24) * 100)))

  const vramLevel = computed(() => {
    const p = vramPercent.value
    if (p <= 50) return { label: '充裕', type: 'success' as const, color: '#67C23A' }
    if (p <= 75) return { label: '适中', type: 'warning' as const, color: '#E6A23C' }
    return { label: '紧张', type: 'danger' as const, color: '#F56C6C' }
  })

  const rules: FormRules = {
    epochs: [{ required: true, message: '请设置训练轮数', trigger: 'blur' }],
    batchSize: [{ required: true, message: '请设置批次大小', trigger: 'blur' }],
    learningRate: [{ required: true, message: '请设置学习率', trigger: 'blur' }],
    maxSeqLength: [{ required: true, message: '请选择最大序列长度', trigger: 'change' }]
  }

  async function validate() {
    if (!formRef.value) throw new Error('表单实例未就绪')
    await formRef.value.validate()
  }

  defineExpose({ validate })
</script>

<style lang="scss" scoped>
  .step3-params {
    flex: 1;
  }

  .step-title {
    display: flex;
    align-items: center;
  }

  .param-form {
    max-width: 800px;
  }

  .param-section {
    margin-bottom: 28px;

    &__title {
      display: flex;
      align-items: center;
      font-size: 14px;
      font-weight: 600;
      color: var(--lfp-gray-800);
      margin: 0 0 16px;
      padding-bottom: 8px;
      border-bottom: 1px solid var(--lfp-gray-200);
    }
  }

  .param-grid {
    display: grid;
    grid-template-columns: repeat(2, 1fr);
    gap: 0 24px;
  }

  .param-hint {
    font-size: 12px;
    color: var(--lfp-gray-500);
    margin-top: 4px;
    line-height: 1.4;
  }

  .switch-grid {
    display: flex;
    flex-direction: column;
    gap: 12px;
  }

  .switch-item {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 14px 16px;
    background: var(--el-fill-color-lighter);
    border-radius: var(--custom-radius, 8px);
    border: 1px solid var(--lfp-gray-200);

    &__info {
      display: flex;
      flex-direction: column;
      gap: 2px;
    }

    &__label {
      font-size: 14px;
      font-weight: 500;
      color: var(--lfp-gray-800);
    }

    &__desc {
      font-size: 12px;
      color: var(--lfp-gray-500);
    }
  }

  .vram-card {
    margin-top: 24px;
    padding: 20px;
    background: var(--el-fill-color-lighter);
    border-radius: var(--custom-radius, 8px);
    border: 1px solid var(--lfp-gray-200);

    &__header {
      display: flex;
      align-items: center;
      margin-bottom: 12px;
    }
  }
</style>
