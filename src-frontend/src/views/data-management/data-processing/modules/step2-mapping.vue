<template>
  <div class="step2-mapping">
    <div class="split-layout">
      <!-- ========== 左侧：清洗算子编排 (40%) ========== -->
      <div class="left-panel">
        <ElScrollbar>
          <div class="left-panel__inner">
            <!-- 当前数据集信息 -->
            <div class="dataset-info art-card" v-if="dataset">
              <div class="flex items-center gap-2 mb-1">
                <span class="ri:file-text-line text-theme"></span>
                <span class="text-sm font-medium text-g-700 truncate">{{ dataset.name }}</span>
              </div>
              <div class="text-xs text-g-500">
                {{ dataset.format }} · {{ formatSize(dataset.size) }} · {{ dataset.records?.toLocaleString() }} 条记录
              </div>
            </div>

            <ElCollapse v-model="activeOperators" class="operator-accordion">
              <!-- 1. 模型字段映射 -->
              <ElCollapseItem title="1. 模型字段映射" name="fieldMapping">
                <div class="operator-content">
                  <!-- 表格式映射布局 -->
                  <div class="field-map-table">
                    <div class="field-map-table__header">
                      <span class="col-source">请选择源数据表头</span>
                      <span class="col-arrow"></span>
                      <span class="col-target">映射到模型字段</span>
                    </div>

                    <!-- instruction 行（必填） -->
                    <div class="field-map-table__row">
                      <div class="col-source">
                        <ElSelect
                          :model-value="config.fieldMapping.instruction"
                          class="!w-full"
                          size="default"
                          clearable
                          placeholder="请选择"
                          @update:model-value="(v: string) => updateField('instruction', v)"
                        >
                          <ElOption
                            v-for="f in sourceHeaders"
                            :key="f"
                            :label="f"
                            :value="f"
                          />
                        </ElSelect>
                      </div>
                      <div class="col-arrow">
                        <span class="ri:arrow-right-line text-g-400 text-lg"></span>
                      </div>
                      <div class="col-target">
                        <div class="target-label">
                          <span class="target-label__name">instruction</span>
                          <span class="target-label__required">必填</span>
                        </div>
                        <div class="target-desc">任务说明</div>
                      </div>
                    </div>

                    <!-- input 行（可选） -->
                    <div class="field-map-table__row">
                      <div class="col-source">
                        <ElSelect
                          :model-value="inputSelectValue"
                          class="!w-full"
                          size="default"
                          clearable
                          placeholder="请选择"
                          @update:model-value="(v: string) => handleInputSelect(v)"
                        >
                          <ElOption label="无" value="__NONE__" />
                          <ElOption
                            v-for="f in sourceHeaders"
                            :key="f"
                            :label="f"
                            :value="f"
                          />
                        </ElSelect>
                      </div>
                      <div class="col-arrow">
                        <span class="ri:arrow-right-line text-g-400 text-lg"></span>
                      </div>
                      <div class="col-target">
                        <div class="target-label">
                          <span class="target-label__name">input</span>
                          <span class="target-label__optional">可选</span>
                        </div>
                        <div class="target-desc">已知条件/补充材料</div>
                      </div>
                    </div>

                    <!-- output 行（必填） -->
                    <div class="field-map-table__row">
                      <div class="col-source">
                        <ElSelect
                          :model-value="config.fieldMapping.output"
                          class="!w-full"
                          size="default"
                          clearable
                          placeholder="请选择"
                          @update:model-value="(v: string) => updateField('output', v)"
                        >
                          <ElOption
                            v-for="f in sourceHeaders"
                            :key="f"
                            :label="f"
                            :value="f"
                          />
                        </ElSelect>
                      </div>
                      <div class="col-arrow">
                        <span class="ri:arrow-right-line text-g-400 text-lg"></span>
                      </div>
                      <div class="col-target">
                        <div class="target-label">
                          <span class="target-label__name">output</span>
                          <span class="target-label__required">必填</span>
                        </div>
                        <div class="target-desc">输出答案</div>
                      </div>
                    </div>
                  </div>

                  <!-- 非结构化文本提示 -->
                  <div v-if="isUnstructuredText" class="unstructured-notice">
                    <span class="ri:information-line mr-1.5"></span>
                    检测到非结构化文本文件，源字段统一为「文件原始内容」，映射为 text（预训练纯文本）
                  </div>
                </div>
              </ElCollapseItem>

              <!-- 2. 基础过滤 -->
              <ElCollapseItem title="2. 基础过滤" name="filters">
                <div class="operator-content">
                  <div class="toggle-item" :class="{ active: config.filters.dropEmpty }">
                    <div class="flex items-center justify-between">
                      <div class="flex items-center gap-2">
                        <span :class="config.filters.dropEmpty ? 'ri:toggle-line text-success' : 'ri:toggle-line text-g-400'" class="text-xl toggle-icon"></span>
                        <span class="text-sm">剔除空白行 / 缺失值</span>
                      </div>
                      <ElSwitch
                        :model-value="config.filters.dropEmpty"
                        size="small"
                        @update:model-value="(v) => updateFilters('dropEmpty', v)"
                      />
                    </div>
                  </div>
                  <div class="toggle-item" :class="{ active: config.filters.dropShortText }">
                    <div class="flex items-center justify-between">
                      <div class="flex items-center gap-2">
                        <span :class="config.filters.dropShortText ? 'ri:toggle-line text-success' : 'ri:toggle-line text-g-400'" class="text-xl toggle-icon"></span>
                        <span class="text-sm">过滤短文本 (长度 &lt;</span>
                        <ElInputNumber
                          :model-value="config.filters.minLength"
                          size="small"
                          :min="1"
                          :max="999"
                          :controls="false"
                          class="inline-number-input"
                          @update:model-value="(v) => updateFilters('minLength', Number(v) || 10)"
                        />
                        <span class="text-sm">字符)</span>
                      </div>
                      <ElSwitch
                        :model-value="config.filters.dropShortText"
                        size="small"
                        @update:model-value="(v) => updateFilters('dropShortText', v)"
                      />
                    </div>
                  </div>
                </div>
              </ElCollapseItem>

              <!-- 3. 文本格式化 -->
              <ElCollapseItem title="3. 文本格式化" name="formatters">
                <div class="operator-content">
                  <div class="toggle-item" :class="{ active: config.formatters.stripHtml }">
                    <div class="flex items-center justify-between">
                      <div class="flex items-center gap-2">
                        <span :class="config.formatters.stripHtml ? 'ri:toggle-line text-success' : 'ri:toggle-line text-g-400'" class="text-xl toggle-icon"></span>
                        <span class="text-sm">移除 HTML/XML 标签</span>
                      </div>
                      <ElSwitch
                        :model-value="config.formatters.stripHtml"
                        size="small"
                        @update:model-value="(v) => updateFormatters('stripHtml', v)"
                      />
                    </div>
                  </div>
                  <div class="toggle-item" :class="{ active: config.formatters.unifyPunctuation }">
                    <div class="flex items-center justify-between">
                      <div class="flex items-center gap-2">
                        <span :class="config.formatters.unifyPunctuation ? 'ri:toggle-line text-success' : 'ri:toggle-line text-g-400'" class="text-xl toggle-icon"></span>
                        <span class="text-sm">统一全角转半角</span>
                      </div>
                      <ElSwitch
                        :model-value="config.formatters.unifyPunctuation"
                        size="small"
                        @update:model-value="(v) => updateFormatters('unifyPunctuation', v)"
                      />
                    </div>
                  </div>
                </div>
              </ElCollapseItem>

              <!-- 4. 隐私脱敏 -->
              <ElCollapseItem title="4. 隐私脱敏" name="piiMaskers">
                <div class="operator-content">
                  <div class="masker-grid">
                    <ElCheckbox
                      :model-value="config.piiMaskers.phone"
                      size="small"
                      @update:model-value="(v) => updatePiiMaskers('phone', v)"
                    >
                      手机号码
                    </ElCheckbox>
                    <ElCheckbox
                      :model-value="config.piiMaskers.idCard"
                      size="small"
                      @update:model-value="(v) => updatePiiMaskers('idCard', v)"
                    >
                      身份证号
                    </ElCheckbox>
                    <ElCheckbox
                      :model-value="config.piiMaskers.email"
                      size="small"
                      @update:model-value="(v) => updatePiiMaskers('email', v)"
                    >
                      电子邮箱
                    </ElCheckbox>
                    <ElCheckbox
                      :model-value="config.piiMaskers.bankCard"
                      size="small"
                      @update:model-value="(v) => updatePiiMaskers('bankCard', v)"
                    >
                      银行卡号
                    </ElCheckbox>
                  </div>
                </div>
              </ElCollapseItem>

              <!-- 5. 语料去重 -->
              <ElCollapseItem title="5. 语料去重" name="deduplication">
                <div class="operator-content">
                  <div class="toggle-item" :class="{ active: config.deduplication.enabled }">
                    <div class="flex items-center justify-between mb-3">
                      <div class="flex items-center gap-2">
                        <span :class="config.deduplication.enabled ? 'ri:toggle-line text-success' : 'ri:toggle-line text-g-400'" class="text-xl toggle-icon"></span>
                        <span class="text-sm">MinHash 模糊去重</span>
                      </div>
                      <ElSwitch
                        :model-value="config.deduplication.enabled"
                        size="small"
                        @update:model-value="(v) => updateDedup('enabled', v)"
                      />
                    </div>
                    <div v-if="config.deduplication.enabled" class="dedup-slider">
                      <div class="dedup-slider__header">
                        <span class="text-g-600">相似度阈值</span>
                        <span class="dedup-slider__value">{{ config.deduplication.threshold.toFixed(2) }}</span>
                      </div>
                      <ElSlider
                        :model-value="config.deduplication.threshold"
                        :min="0.50"
                        :max="0.99"
                        :step="0.01"
                        :show-tooltip="false"
                        class="dedup-slider__bar"
                        @update:model-value="(v) => updateDedup('threshold', Number(v))"
                      />
                      <div class="dedup-slider__marks">
                        <span class="text-g-600">0.50（宽松）</span>
                        <span class="text-g-600">0.99（严格）</span>
                      </div>
                    </div>
                  </div>
                  <div v-if="config.deduplication.enabled" class="dedup-note">
                    <span class="ri:information-line text-xs text-warning mr-1"></span>
                    <span class="text-xs text-g-500">全局去重效果将在完整任务执行后体现</span>
                  </div>
                </div>
              </ElCollapseItem>
            </ElCollapse>
          </div>
        </ElScrollbar>
      </div>

      <!-- ========== 右侧：实时对比沙盒 (60%) ========== -->
      <div class="right-panel">
        <div class="right-panel__header">
          <h3 class="panel-title">
            <span class="ri:eye-line mr-2"></span>预览控制台
          </h3>
          <div class="flex items-center gap-3">
            <ElButton size="small" @click="refreshSamples">
              <span class="ri:refresh-line mr-1"></span>随机换 5 条样本
            </ElButton>
            <ElRadioGroup v-model="viewMode" size="small">
              <ElRadioButton value="compare">左右对比</ElRadioButton>
              <ElRadioButton value="result">仅看结果</ElRadioButton>
            </ElRadioGroup>
          </div>
        </div>

        <ElScrollbar class="right-panel__body">
          <!-- 样本列表 -->
          <div v-if="samples.length > 0" class="sample-list">
            <div
              v-for="(sample, si) in samples"
              :key="sample.id"
              class="sample-item"
            >
              <!-- 丢弃警告 -->
              <div v-if="sample.discarded" class="sample-discard-alert">
                <span class="ri:error-warning-line mr-1"></span>
                该条数据因触发 [{{ sample.discardReason }}] 已被丢弃。
              </div>

              <template v-else>
                <!-- 字段对比 -->
                <div v-for="field in displayFields" :key="field.key" class="sample-field" :class="{ 'has-diff': sample.diffFields.includes(field.key) }">
                  <div class="sample-field__label">{{ field.label }}</div>

                  <!-- 左右对比模式 -->
                  <template v-if="viewMode === 'compare'">
                    <div class="sample-compare">
                      <!-- 原始数据 -->
                      <div class="sample-compare__raw" v-if="sample.raw[field.key]">
                        <span class="sample-compare__tag raw">🔴 原始数据</span>
                        <div class="sample-compare__text" v-html="highlightDiff(sample.raw[field.key], sample.processed[field.key], 'raw')"></div>
                      </div>
                      <!-- 清洗后 -->
                      <div class="sample-compare__processed">
                        <span class="sample-compare__tag processed">🟢 清洗后</span>
                        <div class="sample-compare__text" v-html="highlightDiff(sample.processed[field.key], sample.raw[field.key], 'processed')"></div>
                      </div>
                    </div>
                  </template>

                  <!-- 仅看结果模式 -->
                  <template v-else>
                    <div class="sample-compare">
                      <div class="sample-compare__processed">
                        <span class="sample-compare__tag processed">结果</span>
                        <div class="sample-compare__text" v-html="highlightDiff(sample.processed[field.key], sample.raw[field.key], 'processed')"></div>
                      </div>
                    </div>
                  </template>
                </div>
              </template>
            </div>
          </div>

          <!-- 空状态 -->
          <div v-else class="sample-empty">
            <ArtSvgIcon icon="ri:file-search-line" class="text-5xl text-g-400 mb-3" />
            <p class="text-g-500">尚未选择数据集</p>
            <p class="text-xs text-g-400 mt-1">返回上一步选择源数据以开始预览</p>
          </div>
        </ElScrollbar>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
import { fetchGetCleaningSamplesMock, fetchRefreshCleaningSamplesMock } from '@/api/data-manage'
import type { DatasetItem } from '@/mock/temp/formData'

defineOptions({ name: 'Step2Mapping' })

const props = defineProps<{
  dataset: DatasetItem | null
  config: Api.DataManage.DataProcessing.CleaningConfig
}>()

const emit = defineEmits<{
  'update:config': [config: Api.DataManage.DataProcessing.CleaningConfig]
  'refreshSamples': []
}>()

const activeOperators = ref(['fieldMapping', 'filters', 'formatters', 'piiMaskers', 'deduplication'])
const viewMode = ref<'compare' | 'result'>('compare')
const samples = ref<Api.DataManage.DataProcessing.CleaningSample[]>([])

const sourceHeaders = computed(() => {
  if (!props.dataset) return []
  return extractHeadersFromDataset(props.dataset)
})

const isUnstructuredText = computed(() => {
  return props.dataset?.format === 'TXT'
})

const inputSelectValue = computed(() => {
  return props.config.fieldMapping.input || ''
})

const displayFields = [
  { key: 'instruction', label: 'instruction' },
  { key: 'input', label: 'input' },
  { key: 'output', label: 'output' }
]

function extractHeadersFromDataset(dataset: DatasetItem): string[] {
  if (!dataset.samples?.length) return []
  const format = dataset.format?.toUpperCase()

  if (format === 'TXT') {
    return ['文件原始内容']
  }

  if (format === 'CSV') {
    const headers: string[] = []
    for (const sample of dataset.samples) {
      const lines = sample.split('\n').filter((l) => l.trim())
      if (lines.length > 0) {
        const firstLine = lines[0].replace(/^\uFEFF/, '')
        const cols = firstLine.split(',').map((c) => c.trim()).filter((c) => c.length > 0)
        if (cols.length > 0) {
          headers.push(...cols)
          break
        }
      }
    }
    return [...new Set(headers)]
  }

  if (format === 'JSON') {
    const keys = new Set<string>()
    for (const sample of dataset.samples) {
      try {
        const obj = JSON.parse(sample)
        Object.keys(obj).forEach((k) => keys.add(k))
      } catch {
        // 非 JSON 对象格式（如对话格式）：尝试提取常见字段
        const match = sample.match(/"([a-zA-Z_]\w*)"\s*:/g)
        if (match) {
          match.forEach((m) => keys.add(m.replace(/["\s:]/g, '')))
        }
      }
    }
    if (keys.size > 0) return [...keys]
  }

  return ['无表头数据']
}

function updateField(field: string, value: string) {
  const mapping = { ...props.config.fieldMapping, [field]: value }
  emit('update:config', { ...props.config, fieldMapping: mapping })
}

function handleInputSelect(value: string) {
  updateField('input', value || '')
}

function updateFilters(key: string, value: string | number | boolean) {
  const filters = { ...props.config.filters, [key]: value }
  emit('update:config', { ...props.config, filters })
}

function updateFormatters(key: string, value: string | number | boolean) {
  const formatters = { ...props.config.formatters, [key]: value }
  emit('update:config', { ...props.config, formatters })
}

function updatePiiMaskers(key: string, value: string | number | boolean) {
  const piiMaskers = { ...props.config.piiMaskers, [key]: value }
  emit('update:config', { ...props.config, piiMaskers })
}

function updateDedup(key: string, value: string | number | boolean) {
  const deduplication = { ...props.config.deduplication, [key]: value }
  emit('update:config', { ...props.config, deduplication })
}

async function refreshSamples() {
  try {
    samples.value = await fetchRefreshCleaningSamplesMock()
    emit('refreshSamples')
  } catch { }
}

function formatSize(sizeMB: number): string {
  if (sizeMB >= 1024) return `${(sizeMB / 1024).toFixed(1)} GB`
  return `${sizeMB.toFixed(1)} MB`
}

function highlightDiff(text: string, compareText: string, mode: 'raw' | 'processed'): string {
  if (!text) return ''
  if (!compareText) return escapeHtml(text)

  if (mode === 'processed') {
    let result = escapeHtml(text)
    result = result.replace(/\[MASK_PHONE\]/g, '<span class="diff-highlight diff-insert">[MASK_PHONE]</span>')
    result = result.replace(/\[MASK_EMAIL\]/g, '<span class="diff-highlight diff-insert">[MASK_EMAIL]</span>')
    result = result.replace(/\[MASK_IDCARD\]/g, '<span class="diff-highlight diff-insert">[MASK_IDCARD]</span>')
    return result
  }

  if (mode === 'raw') {
    let result = escapeHtml(text)
    result = result.replace(/(<[^>]+>)/g, '<span class="diff-highlight diff-delete">$1</span>')
    const phoneRegex = /1[3-9]\d{9}/g
    result = result.replace(phoneRegex, '<span class="diff-highlight diff-delete">$&</span>')
    const emailRegex = /[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}/g
    result = result.replace(emailRegex, '<span class="diff-highlight diff-delete">$&</span>')
    return result
  }

  return escapeHtml(text)
}

function escapeHtml(str: string): string {
  return str
    .replace(/&/g, '&amp;')
    .replace(/</g, '&lt;')
    .replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;')
}

onMounted(async () => {
  try {
    samples.value = await fetchGetCleaningSamplesMock()
  } catch { }
})

watch(() => props.dataset, () => {
  refreshSamples()
})
</script>

<style lang="scss" scoped>
.step2-mapping {
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

  &__body {
    flex: 1;
    min-height: 0;
    padding: 12px 16px;
  }
}

.panel-title {
  font-size: 15px;
  font-weight: 600;
  color: var(--art-gray-800);
  display: flex;
  align-items: center;
}

.dataset-info {
  padding: 12px 14px;
  margin-bottom: 12px;
  background: linear-gradient(135deg, rgba(var(--el-color-primary-rgb, 64, 158, 255), 0.04) 0%, #fff 100%);
  border: 1px solid rgba(var(--el-color-primary-rgb, 64, 158, 255), 0.1);
}

// 算子折叠面板
.operator-accordion {
  :deep(.el-collapse-item__header) {
    font-size: 15px;
    font-weight: 500;
    color: var(--art-gray-700);
    padding: 12px 0;
    border-bottom-color: var(--art-gray-100);
  }
  :deep(.el-collapse-item__wrap) {
    border-bottom-color: var(--art-gray-100);
  }
  :deep(.el-collapse-item__content) {
    padding-bottom: 12px;
  }
}

.operator-content {
  padding: 0 4px;
}

.operator-desc {
  font-size: 12px;
  color: var(--art-gray-500);
  margin: 0 0 12px;
}

// 折叠面板标题
.collapse-header {
  display: flex;
  align-items: center;
  gap: 8px;

  &__badge {
    font-size: 11px;
    font-weight: 400;
    color: var(--art-gray-400);
    background: var(--art-gray-100);
    padding: 1px 6px;
    border-radius: 4px;
    text-transform: uppercase;
    letter-spacing: 0.3px;
  }
}

// 字段映射表格式布局
.field-map-table {
  border: 1px solid var(--art-gray-150);
  border-radius: calc(var(--custom-radius, 8px));
  overflow: hidden;

  &__header {
    display: grid;
    grid-template-columns: 1fr 40px 1fr;
    align-items: center;
    padding: 8px 12px;
    background: var(--art-gray-50);
    font-size: 14px;
    font-weight: 500;
    color: var(--art-gray-700);
    border-bottom: 1px solid var(--art-gray-150);
  }

  &__row {
    display: grid;
    grid-template-columns: 1fr 40px 1fr;
    align-items: center;
    padding: 10px 12px;

    &:last-child {
      border-bottom: none;
    }
  }
}

.col-source {
  display: flex;
  align-items: center;
}

.col-arrow {
  display: flex;
  align-items: center;
  justify-content: center;
}

.col-target {
  display: flex;
  flex-direction: column;
  gap: 4px;
}

.target-label {
  display: flex;
  align-items: center;
  justify-content: space-between;
  gap: 6px;
  margin-right: 40px;

  &__name {
    font-size: 14px;
    font-weight: 600;
    color: var(--art-gray-700);
    font-family: 'Cascadia Code', 'Fira Code', 'JetBrains Mono', monospace;
  }

  &__required {
    font-size: 10px;
    font-weight: 600;
    color: #fff;
    background: #f56c6c;
    padding: 1px 6px;
    border-radius: 3px;
    line-height: 1.4;
  }

  &__optional {
    font-size: 10px;
    font-weight: 600;
    color: #fff;
    background: #67C23A;
    padding: 1px 6px;
    border-radius: 3px;
    line-height: 1.4;
  }
}

.target-desc {
  font-size: 11px;
  color: var(--art-gray-600);
  padding-left: 2px;
}

// 非结构化文本提示
.unstructured-notice {
  display: flex;
  align-items: center;
  margin-top: 10px;
  padding: 8px 10px;
  font-size: 12px;
  color: var(--el-color-primary);
  background: rgba(var(--el-color-primary-rgb, 64, 158, 255), 0.06);
  border: 1px solid rgba(var(--el-color-primary-rgb, 64, 158, 255), 0.15);
  border-radius: 6px;
}

.toggle-item {
  padding: 8px 10px;
  border-radius: 6px;
  margin-bottom: 6px;
  transition: all 0.2s;

  &.active {
    background: rgba(var(--el-color-primary-rgb, 64, 158, 255), 0.04);
  }
}

.toggle-icon {
  transition: color 0.2s;
}

// 内联数字输入框
.inline-number-input {
  width: 64px;

  :deep(.el-input__wrapper) {
    padding: 0 4px;
    background: #fff;
    box-shadow: 0 0 0 1px var(--el-border-color) inset;
    border-radius: 4px;

    &:hover {
      box-shadow: 0 0 0 1px var(--el-border-color-dark) inset;
    }

    &.is-focus {
      box-shadow: 0 0 0 1px var(--el-color-primary) inset;
    }
  }

  :deep(.el-input__inner) {
    text-align: center;
    font-size: 12px;
    font-weight: 600;
    color: var(--art-gray-700);
  }
}

// 去重滑块
.dedup-slider {
  &__header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-bottom: 6px;
  }

  &__value {
    font-size: 14px;
    font-weight: 700;
    color: var(--el-color-primary);
    font-family: 'Cascadia Code', 'Fira Code', monospace;
  }

  &__bar {
    padding: 0 4px;

    :deep(.el-slider__runway) {
      height: 4px;
    }

    :deep(.el-slider__bar) {
      height: 4px;
      background: var(--el-color-primary);
    }

    :deep(.el-slider__button) {
      width: 14px;
      height: 14px;
      border-color: var(--el-color-primary);
      background: #fff;
      box-shadow: 0 1px 3px rgba(0, 0, 0, 0.12);
    }
  }

  &__marks {
    display: flex;
    align-items: center;
    justify-content: space-between;
    margin-top: 2px;
  }
}

.masker-grid {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 8px;
  padding: 4px 0;
}

.dedup-note {
  display: flex;
  align-items: center;
  margin-top: 8px;
  padding: 8px 10px;
  background: rgba(230, 162, 60, 0.06);
  border-radius: 6px;
  border: 1px solid rgba(230, 162, 60, 0.15);
}

// 样本列表
.sample-list {
  display: flex;
  flex-direction: column;
  gap: 16px;
}

.sample-item {
  border: 1px solid var(--art-gray-200);
  border-radius: calc(var(--custom-radius, 8px) + 2px);
  overflow: hidden;
  box-shadow: 0 1px 4px rgba(0, 0, 0, 0.04);
}

.sample-discard-alert {
  display: flex;
  align-items: center;
  padding: 10px 14px;
  font-size: 12px;
  color: #e6a23c;
  background: rgba(230, 162, 60, 0.06);
}

.sample-field {
  padding: 14px 16px;
  border-bottom: 1px solid var(--art-gray-150);

  &:last-child { border-bottom: none; }

  &__label {
    font-size: 13px;
    font-weight: 700;
    color: var(--art-gray-600);
    text-transform: uppercase;
    letter-spacing: 0.8px;
    margin-bottom: 10px;
    display: flex;
    align-items: center;
    gap: 6px;

    &::after {
      content: '';
      flex: 1;
      height: 1px;
      background: var(--art-gray-200);
    }
  }
}

.sample-compare {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 12px;

  &__raw, &__processed {
    min-width: 0;
  }

  &__tag {
    display: inline-flex;
    align-items: center;
    font-size: 12px;
    font-weight: 700;
    margin-bottom: 8px;
    &.raw { color: #f56c6c; }
    &.processed { color: #67c23a; }
  }

  &__text {
    font-size: 13px;
    color: var(--art-gray-800);
    line-height: 1.6;
    word-break: break-all;
    padding: 10px 12px;
    background: var(--art-gray-50);
    border-radius: 6px;
    white-space: pre-wrap;
    min-height: 40px;
  }
}

// Diff高亮
:deep(.diff-highlight) {
  padding: 1px 2px;
  border-radius: 2px;
  font-weight: 600;

  &.diff-delete {
    background: rgba(245, 108, 108, 0.15);
    color: #f56c6c;
    text-decoration: line-through;
  }

  &.diff-insert {
    background: rgba(103, 194, 58, 0.15);
    color: #67c23a;
  }
}

.sample-empty {
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  height: 300px;
}
</style>
