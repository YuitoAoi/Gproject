<template>
  <div class="step1-basic">
    <ElForm ref="formRef" :model="modelValue" :rules="rules" label-position="top" class="basic-form">
      <!-- 任务名称 -->
      <div class="lfp-card form-section">
        <div class="form-section__header">
          <LfpSvgIcon icon="ri:file-text-line" class="form-section__icon" />
          <div>
            <h3 class="form-section__title">任务名称</h3>
            <p class="form-section__desc">为本次训练任务设置一个清晰易识别的名称</p>
          </div>
        </div>
        <div class="form-section__body">
          <ElFormItem prop="taskName" label="任务名称" class="form-item-full">
            <ElInput :model-value="modelValue.taskName" placeholder="例如：客服场景 LoRA 微调" maxlength="60" show-word-limit clearable @update:model-value="handleTaskName">
              <template #prefix><LfpSvgIcon icon="ri:price-tag-3-line" class="text-g-400" /></template>
            </ElInput>
          </ElFormItem>
        </div>
      </div>
      <!-- 基础模型 -->
      <div class="lfp-card form-section">
        <div class="form-section__header">
          <LfpSvgIcon icon="ri:brain-line" class="form-section__icon" />
          <div>
            <h3 class="form-section__title">基础模型</h3>
            <p class="form-section__desc">选择用于微调的预训练基础模型</p>
          </div>
          <div class="ml-auto flex items-center gap-2">
            <div v-if="modelsLoading" class="flex items-center gap-1.5 text-sm text-g-400">
              <span class="loading-spinner"></span>加载中
            </div>
            <ElButton text size="small" @click="refreshModels">
              <LfpSvgIcon icon="ri:refresh-line" class="mr-1" />刷新
            </ElButton>
          </div>
        </div>
        <div class="form-section__body">
          <ElFormItem prop="baseModel" label="基础模型" class="form-item-full">
            <ElSelect
              :model-value="modelValue.baseModel"
              placeholder="请选择基础模型"
              class="!w-full"
              filterable
              :loading="modelsLoading"
              @update:model-value="handleBaseModel"
            >
              <template v-if="modelOptions.length === 0 && !modelsLoading">
                <el-empty description="暂无可用模型，请确保 LlamaFactory 推理服务已启动" :image-size="60" />
              </template>
              <template v-else>
  
                <template v-if="llamaModels.length">
                  <ElOptionGroup label="LLaMA 系列">
                    <ElOption v-for="m in llamaModels" :key="m.value" :label="m.label" :value="m.value">
                      <div class="model-option"><span class="model-option__name">{{ m.label }}</span><span class="model-option__tag">{{ m.tag }}</span></div>
                    </ElOption>
                  </ElOptionGroup>
                </template>
                <template v-if="otherModels.length">
                  <ElOptionGroup label="其他模型">
                    <ElOption v-for="m in otherModels" :key="m.value" :label="m.label" :value="m.value">
                      <div class="model-option"><span class="model-option__name">{{ m.label }}</span><span class="model-option__tag">{{ m.tag }}</span></div>
                    </ElOption>
                  </ElOptionGroup>
                </template>
              </template>
            </ElSelect>
          </ElFormItem>
          <Transition name="fade">
            <div v-if="selectedModelInfo" class="model-info-banner">
              <LfpSvgIcon icon="ri:information-line" class="text-sm mr-2 flex-shrink-0" />
              <span>{{ selectedModelInfo }}</span>
            </div>
          </Transition>
        </div>
      </div>
      <!-- 微调方法 -->
      <div class="lfp-card form-section">
        <div class="form-section__header">
          <LfpSvgIcon icon="ri:settings-4-line" class="form-section__icon" />
          <div>
            <h3 class="form-section__title">微调方法</h3>
            <p class="form-section__desc">根据显存资源和训练目标选择合适的微调策略</p>
          </div>
        </div>
        <div class="form-section__body">
          <ElFormItem prop="finetuneMethod" class="form-item-no-label">
            <div class="method-grid">
              <div
                v-for="method in finetuneMethodOptions"
                :key="method.value"
                class="method-card"
                :class="{ 'is-selected': modelValue.finetuneMethod === method.value }"
                @click="handleFinetuneMethod(method.value)"
              >
                <div class="method-card__header">
                  <div class="method-card__radio">
                    <LfpSvgIcon :icon="modelValue.finetuneMethod === method.value ? 'ri:radio-button-line' : 'ri:checkbox-blank-circle-line'" class="text-lg" :style="{ color: modelValue.finetuneMethod === method.value ? 'var(--el-color-primary)' : 'var(--lfp-gray-400)' }" />
                  </div>
                  <div class="method-card__title-wrap">
                    <span class="method-card__name">{{ method.name }}</span>
                    <span v-if="method.badge" class="method-card__badge" :class="['method-card__badge--' + method.badgeType]">{{ method.badge }}</span>
                  </div>
                </div>
                <p class="method-card__desc">{{ method.desc }}</p>
                <div class="method-card__meta">
                  <span class="method-card__meta-item"><LfpSvgIcon icon="ri:cpu-line" class="text-xs mr-1" />{{ method.vram }}</span>
                  <span class="method-card__meta-item"><LfpSvgIcon icon="ri:time-line" class="text-xs mr-1" />{{ method.speed }}</span>
                </div>
              </div>
            </div>
          </ElFormItem>
        </div>
      </div>
      <!-- 配置模式 -->
      <div class="lfp-card form-section">
        <div class="form-section__header">
          <LfpSvgIcon icon="ri:sliders-line" class="form-section__icon" />
          <div>
            <h3 class="form-section__title">配置模式</h3>
            <p class="form-section__desc">选择参数配置方式，新手模式将自动推荐最佳训练参数</p>
          </div>
        </div>
        <div class="form-section__body">
          <ElFormItem prop="configMode" class="form-item-no-label">
            <div class="mode-grid">
              <div
                v-for="mode in configModeOptions"
                :key="mode.value"
                class="mode-card"
                :class="{ 'is-selected': modelValue.configMode === mode.value }"
                @click="handleConfigMode(mode.value)"
              >
                <div class="mode-card__icon-wrap" :class="['mode-card__icon-wrap--' + mode.value]">
                  <LfpSvgIcon :icon="mode.icon" class="text-2xl" />
                </div>
                <div class="mode-card__content">
                  <div class="mode-card__header">
                    <span class="mode-card__name">{{ mode.name }}</span>
                    <LfpSvgIcon :icon="modelValue.configMode === mode.value ? 'ri:checkbox-circle-fill' : 'ri:checkbox-blank-circle-line'" class="text-lg flex-shrink-0" :style="{ color: modelValue.configMode === mode.value ? 'var(--el-color-primary)' : 'var(--lfp-gray-300)' }" />
                  </div>
                  <p class="mode-card__desc">{{ mode.desc }}</p>
                  <ul class="mode-card__features">
                    <li v-for="feat in mode.features" :key="feat" class="mode-card__feature-item">
                      <LfpSvgIcon icon="ri:check-line" class="text-xs mr-1 text-success" />{{ feat }}
                    </li>
                  </ul>
                </div>
              </div>
            </div>
          </ElFormItem>
        </div>
      </div>
    </ElForm>
  </div>
</template>

<script setup lang="ts">
  import { ref, computed, onMounted } from 'vue'
  import type { FormInstance, FormRules } from 'element-plus'
  import LfpSvgIcon from '@/components/core/base/lfp-svg-icon/index.vue'
  import { getLlamaFactoryModels } from '@/api/llamafactory'

  defineOptions({ name: 'Step1Basic' })

  interface ModelOption {
    value: string
    label: string
    tag: string
    org: string
  }

  interface BasicConfig {
    taskName: string
    baseModel: string
    finetuneMethod: 'lora' | 'qlora' | 'full'
    configMode: 'beginner' | 'expert'
  }

  const props = defineProps<{
    modelValue: BasicConfig
  }>()

  const emit = defineEmits<{
    'update:modelValue': [value: BasicConfig]
  }>()

  const formRef = ref<FormInstance>()
  const modelsLoading = ref(false)
  const modelOptions = ref<ModelOption[]>([])

  onMounted(async () => {
    await fetchModels()
  })

  async function fetchModels() {
    modelsLoading.value = true
    try {
      const resp = await getLlamaFactoryModels()
      if (resp.success && resp.models) {
        modelOptions.value = resp.models.map((id: string) => parseModelOption(id))
      }
    } catch {
      modelOptions.value = []
    } finally {
      modelsLoading.value = false
    }
  }

  function refreshModels() {
    fetchModels()
  }

  function parseModelOption(id: string): ModelOption {
    const parts = id.split('/')
    const org = parts.length > 1 ? parts[0] : ''
    const name = parts.length > 1 ? parts.slice(1).join('/') : id
    const sizeMatch = name.match(/(\d+\.?\d*)[Bb]/)
    const tag = sizeMatch ? sizeMatch[0].toUpperCase() : ''
    return { value: id, label: name, tag, org }
  }

    const llamaModels = computed(() => modelOptions.value.filter(m =>
    m.org.toLowerCase().includes('llama') || m.org.toLowerCase().includes('meta')
  ))

  const otherModels = computed(() => {
    const excluded = new Set(llamaModels.value)
    return modelOptions.value.filter(m => !excluded.has(m))
  })

  const allModels = computed(() => modelOptions.value)

  interface MethodOption {
    value: 'lora' | 'qlora' | 'full'
    name: string
    badge: string
    badgeType: string
    desc: string
    vram: string
    speed: string
  }

  const finetuneMethodOptions: MethodOption[] = [
    { value: 'lora', name: 'LoRA 微调', badge: '推荐', badgeType: 'primary', desc: '低秩适配微调，只训练少量额外参数，显存占用低，效果接近全量微调，适合大多数场景。', vram: '显存需求低', speed: '训练速度快' },
    { value: 'qlora', name: 'QLoRA 微调', badge: '低显存', badgeType: 'warning', desc: '量化版 LoRA，将基础模型以 4-bit 量化加载，在显存极为受限的环境下也能完成微调。', vram: '显存需求极低', speed: '训练速度较慢' },
    { value: 'full', name: '全量微调', badge: '高显存', badgeType: 'danger', desc: '对模型全部参数进行训练，效果最佳但需要大量显存，适合有充足 GPU 资源的团队。', vram: '显存需求高', speed: '训练效果最佳' }
  ]

  interface ModeOption {
    value: 'beginner' | 'expert'
    name: string
    icon: string
    desc: string
    features: string[]
  }

  const configModeOptions: ModeOption[] = [
    { value: 'beginner', name: '新手模式', icon: 'ri:magic-line', desc: '系统根据所选模型和微调方法自动推荐最佳超参数配置，无需手动调整。', features: ['自动推荐学习率', '自动配置批次大小', '自动设置训练轮数'] },
    { value: 'expert', name: '专家模式', icon: 'ri:code-s-slash-line', desc: '完全自定义所有训练参数，适合有丰富微调经验、需要精细控制训练过程的用户。', features: ['自定义全部超参数', '精细控制 LoRA 配置', '高级优化器设置'] }
  ]

  /** 当前选中模型的显存提示信息 */
  const selectedModelInfo = computed(() => {
    if (!props.modelValue.baseModel) return ''
    const sizeMap: Record<string, string> = {
      '3B':  '参数量 3B，显存需求约 6GB，适合入门级 GPU',
      '7B':  '参数量 7B，显存需求约 14GB，性能与资源平衡最佳',
      '8B':  '参数量 8B，显存需求约 16GB，推理能力强',
      '14B': '参数量 14B，显存需求约 28GB，效果显著优于 7B'
    }
    const matched = allModels.value.find((m) => m.value === props.modelValue.baseModel)
    if (!matched) return ''
    return sizeMap[matched.tag] ?? ''
  })

  /** 当前选中模型的参数量（数字部分），用于新手模式参数推荐 */
  const selectedModelSize = computed((): number => {
    const matched = allModels.value.find((m) => m.value === props.modelValue.baseModel)
    if (!matched || !matched.tag) return 7
    const num = parseFloat(matched.tag.replace(/[Bb]/g, ''))
    return isNaN(num) ? 7 : num
  })

  /** 暴露给父组件的表单验证方法及模型信息 */
  defineExpose({ validate, selectedModelSize, refreshModels })

  const rules = computed<FormRules<BasicConfig>>(() => ({
    taskName: [
      { required: true, message: '请输入任务名称', trigger: 'blur' },
      { min: 2, max: 60, message: '任务名称长度需在 2~60 个字符之间', trigger: 'blur' }
    ],
    baseModel: [
      { required: true, message: '请选择基础模型', trigger: 'change' }
    ]
  }))

  function handleUpdate<K extends keyof BasicConfig>(key: K, value: BasicConfig[K]) {
    emit('update:modelValue', { ...props.modelValue, [key]: value })
  }

  function handleTaskName(v: string)                                 { handleUpdate('taskName', v) }
  function handleBaseModel(v: string)                               { handleUpdate('baseModel', v) }
  function handleFinetuneMethod(v: 'lora' | 'qlora' | 'full')      { handleUpdate('finetuneMethod', v) }
  function handleConfigMode(v: 'beginner' | 'expert')               { handleUpdate('configMode', v) }

  async function validate() {
    if (!formRef.value) return Promise.reject(new Error('表单实例未就绪'))
    return formRef.value.validate()
  }
</script>

<style lang="scss" scoped>
  .step1-basic { padding: 0; }

  .basic-form { display: flex; flex-direction: column; gap: 20px; }

  .form-section {
    padding: 24px;
    &__header {
      display: flex; align-items: flex-start; gap: 12px;
      margin-bottom: 20px; padding-bottom: 16px;
      border-bottom: 1px solid var(--lfp-gray-300);
    }
    &__icon  { font-size: 20px; color: var(--el-color-primary); margin-top: 2px; flex-shrink: 0; }
    &__title { font-size: 15px; font-weight: 600; color: var(--lfp-gray-800); margin: 0 0 4px; line-height: 1.4; }
    &__desc  { font-size: 13px; color: var(--lfp-gray-500); margin: 0; line-height: 1.5; }
    &__body  { padding: 0 4px; }
  }
  .form-item-full {
    margin-bottom: 0;
    :deep(.el-form-item__label) { font-size: 13px; font-weight: 500; color: var(--lfp-gray-700); }
  }
  .form-item-no-label {
    margin-bottom: 0;
    :deep(.el-form-item__content) { display: block; }
  }
  .model-option {
    display: flex; align-items: center; justify-content: space-between; width: 100%;
    &__name { font-size: 13px; color: var(--lfp-gray-800); }
    &__tag {
      font-size: 11px; font-weight: 600; color: var(--el-color-primary);
      background: rgba(var(--el-color-primary-rgb, 64, 158, 255), 0.1);
      padding: 1px 7px; border-radius: 10px;
    }
  }
  .model-info-banner {
    display: flex; align-items: center; margin-top: 10px; padding: 9px 12px;
    font-size: 12px; color: var(--el-color-primary); line-height: 1.5;
    background: rgba(var(--el-color-primary-rgb, 64, 158, 255), 0.06);
    border: 1px solid rgba(var(--el-color-primary-rgb, 64, 158, 255), 0.15);
    border-radius: 6px;
  }
  .method-grid {
    display: grid; grid-template-columns: repeat(3, 1fr); gap: 12px;
    @media (max-width: 900px) { grid-template-columns: 1fr; }
  }
  .method-card {
    padding: 16px; border: 2px solid var(--lfp-gray-300);
    border-radius: calc(var(--custom-radius, 8px) + 2px);
    cursor: pointer; transition: all 0.2s ease; background: var(--default-box-color);
    &:hover:not(.is-selected) {
      border-color: rgba(var(--el-color-primary-rgb, 64, 158, 255), 0.4);
      box-shadow: 0 2px 8px rgba(var(--el-color-primary-rgb, 64, 158, 255), 0.08);
    }
    &.is-selected {
      border-color: var(--el-color-primary);
      background: linear-gradient(135deg, rgba(var(--el-color-primary-rgb, 64, 158, 255), 0.04) 0%, var(--default-box-color) 100%);
      box-shadow: 0 0 0 3px rgba(var(--el-color-primary-rgb, 64, 158, 255), 0.1);
    }
    &__header      { display: flex; align-items: center; gap: 8px; margin-bottom: 10px; }
    &__radio       { flex-shrink: 0; line-height: 1; }
    &__title-wrap  { display: flex; align-items: center; gap: 6px; flex: 1; min-width: 0; }
    &__name        { font-size: 14px; font-weight: 600; color: var(--lfp-gray-800); }
    &__badge {
      font-size: 10px; font-weight: 600; padding: 1px 6px; border-radius: 4px; flex-shrink: 0;
      &--primary { color: var(--el-color-primary); background: rgba(var(--el-color-primary-rgb, 64, 158, 255), 0.12); }
      &--warning { color: #e6a23c; background: rgba(230, 162, 60, 0.12); }
      &--danger  { color: #f56c6c; background: rgba(245, 108, 108, 0.1); }
    }
    &__desc        { font-size: 12px; color: var(--lfp-gray-600); line-height: 1.6; margin: 0 0 12px; }
    &__meta        { display: flex; flex-direction: column; gap: 4px; }
    &__meta-item   { display: inline-flex; align-items: center; font-size: 11px; color: var(--lfp-gray-500); }
  }
  .mode-grid {
    display: grid; grid-template-columns: repeat(2, 1fr); gap: 12px;
    @media (max-width: 700px) { grid-template-columns: 1fr; }
  }
  .mode-card {
    display: flex; gap: 16px; padding: 20px;
    border: 2px solid var(--lfp-gray-300);
    border-radius: calc(var(--custom-radius, 8px) + 2px);
    cursor: pointer; transition: all 0.2s ease; background: var(--default-box-color); align-items: flex-start;
    &:hover:not(.is-selected) {
      border-color: rgba(var(--el-color-primary-rgb, 64, 158, 255), 0.4);
      box-shadow: 0 2px 8px rgba(var(--el-color-primary-rgb, 64, 158, 255), 0.08);
    }
    &.is-selected {
      border-color: var(--el-color-primary);
      background: linear-gradient(135deg, rgba(var(--el-color-primary-rgb, 64, 158, 255), 0.04) 0%, var(--default-box-color) 100%);
      box-shadow: 0 0 0 3px rgba(var(--el-color-primary-rgb, 64, 158, 255), 0.1);
    }
    &__icon-wrap {
      width: 44px; height: 44px; border-radius: 10px;
      display: flex; align-items: center; justify-content: center; flex-shrink: 0;
      &--beginner { background: linear-gradient(135deg, #a78bfa, #60a5fa); color: #fff; }
      &--expert   { background: linear-gradient(135deg, #34d399, #3b82f6); color: #fff; }
    }
    &__content      { flex: 1; min-width: 0; }
    &__header       { display: flex; align-items: center; justify-content: space-between; margin-bottom: 6px; }
    &__name         { font-size: 14px; font-weight: 600; color: var(--lfp-gray-800); }
    &__desc         { font-size: 12px; color: var(--lfp-gray-500); line-height: 1.6; margin: 0 0 10px; }
    &__features     { list-style: none; margin: 0; padding: 0; display: flex; flex-direction: column; gap: 3px; }
    &__feature-item { display: flex; align-items: center; font-size: 12px; color: var(--lfp-gray-600); }
  }
  .fade-enter-active, .fade-leave-active { transition: opacity 0.2s ease, transform 0.2s ease; }
  .fade-enter-from, .fade-leave-to { opacity: 0; transform: translateY(-4px); }

  .loading-spinner {
    display: inline-block;
    width: 12px;
    height: 12px;
    border: 2px solid var(--lfp-gray-300);
    border-top-color: var(--el-color-primary);
    border-radius: 50%;
    animation: spin 0.8s linear infinite;
  }
  @keyframes spin {
    to { transform: rotate(360deg); }
  }
</style>