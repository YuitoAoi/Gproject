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
                {{ dataset.format }} · {{ formatSize(dataset.file_size) }}
              </div>
            </div>

            <ElCollapse v-model="activeOperators" class="operator-accordion">
              <!-- 1. LLM 配置 -->
              <ElCollapseItem title="1. LLM 配置" name="llmConfig">
                <div class="operator-content">
                  <div class="form-item">
                    <label class="form-label">API Key</label>
                    <ElInput
                      :model-value="config.api_key"
                      type="password"
                      placeholder="请输入 API Key"
                      show-password
                      @update:model-value="(v) => updateConfig('api_key', v)"
                    />
                  </div>
                  <div class="form-item">
                    <label class="form-label">服务地址</label>
                    <ElInput
                      :model-value="config.synthesizer_url"
                      placeholder="请输入服务地址"
                      @update:model-value="(v) => updateConfig('synthesizer_url', v)"
                    />
                  </div>
                  <div class="form-item">
                    <label class="form-label">模型名称</label>
                    <ElInput
                      :model-value="config.synthesizer_model"
                      placeholder="请输入模型名称"
                      @update:model-value="(v) => updateConfig('synthesizer_model', v)"
                    />
                  </div>
                </div>
              </ElCollapseItem>

              <!-- 2. 生成模式 -->
              <ElCollapseItem title="2. 生成模式" name="generationMode">
                <div class="operator-content">
                  <div class="form-item">
                    <label class="form-label">Mode</label>
                    <ElSelect
                      :model-value="config.mode"
                      class="!w-full"
                      @update:model-value="(v) => updateConfig('mode', v)"
                    >
                      <ElOption label="原子级问答 (atomic)" value="atomic" />
                      <ElOption label="多跳问答 (multi_hop)" value="multi_hop" />
                      <ElOption label="聚合问答 (aggregated)" value="aggregated" />
                      <ElOption label="思维链 (CoT)" value="CoT" />
                      <ElOption label="多选问答 (multi_choice)" value="multi_choice" />
                      <ElOption label="多答案问答 (multi_answer)" value="multi_answer" />
                      <ElOption label="填空问答 (fill_in_blank)" value="fill_in_blank" />
                      <ElOption label="判断题 (true_false)" value="true_false" />
                    </ElSelect>
                  </div>
                  <div class="form-item">
                    <label class="form-label">输出格式</label>
                    <ElSelect
                      :model-value="config.data_format"
                      class="!w-full"
                      @update:model-value="(v) => updateConfig('data_format', v)"
                    >
                      <ElOption label="Alpaca" value="Alpaca" />
                      <ElOption label="Sharegpt" value="Sharegpt" />
                      <ElOption label="ChatML" value="ChatML" />
                    </ElSelect>
                  </div>
                </div>
              </ElCollapseItem>

              <!-- 3. 高级设置 -->
              <ElCollapseItem title="3. 高级设置" name="advancedSettings">
                <div class="operator-content">
                  <div class="form-item">
                    <label class="form-label">分词器</label>
                    <ElInput
                      :model-value="config.tokenizer"
                      placeholder="cl100k_base"
                      @update:model-value="(v) => updateConfig('tokenizer', v)"
                    />
                  </div>
                  <div class="form-row">
                    <div class="form-item">
                      <label class="form-label">块大小</label>
                      <ElInputNumber
                        :model-value="config.chunk_size"
                        :min="1"
                        :max="10000"
                        class="!w-full"
                        @update:model-value="(v) => updateConfig('chunk_size', Number(v))"
                      />
                    </div>
                    <div class="form-item">
                      <label class="form-label">块重叠</label>
                      <ElInputNumber
                        :model-value="config.chunk_overlap"
                        :min="0"
                        :max="1000"
                        class="!w-full"
                        @update:model-value="(v) => updateConfig('chunk_overlap', Number(v))"
                      />
                    </div>
                  </div>
                  <div class="form-item">
                    <label class="form-label">每单元问答数</label>
                    <ElInputNumber
                      :model-value="config.quiz_samples"
                      :min="1"
                      :max="10"
                      class="!w-full"
                      @update:model-value="(v) => updateConfig('quiz_samples', Number(v))"
                    />
                  </div>
                  <div class="form-item">
                    <label class="form-label">分区算法</label>
                    <ElSelect
                      :model-value="config.partition_method"
                      class="!w-full"
                      @update:model-value="(v) => updateConfig('partition_method', v)"
                    >
                      <ElOption label="ECE (默认)" value="ece" />
                      <ElOption label="DFS" value="dfs" />
                      <ElOption label="BFS" value="bfs" />
                      <ElOption label="Leiden" value="leiden" />
                    </ElSelect>
                  </div>
                  <div class="form-row">
                    <div class="form-item">
                      <label class="form-label">RPM</label>
                      <ElInputNumber
                        :model-value="config.rpm"
                        :min="1"
                        :max="10000"
                        class="!w-full"
                        @update:model-value="(v) => updateConfig('rpm', Number(v))"
                      />
                    </div>
                    <div class="form-item">
                      <label class="form-label">TPM</label>
                      <ElInputNumber
                        :model-value="config.tpm"
                        :min="1"
                        :max="100000"
                        class="!w-full"
                        @update:model-value="(v) => updateConfig('tpm', Number(v))"
                      />
                    </div>
                  </div>
                </div>
              </ElCollapseItem>
            </ElCollapse>
          </div>
        </ElScrollbar>
      </div>

      <!-- ========== 右侧：配置说明 (60%) ========== -->
      <div class="right-panel">
        <div class="right-panel__header">
          <h3 class="panel-title"> <span class="ri:information-line mr-2"></span>配置说明 </h3>
        </div>

        <ElScrollbar class="right-panel__body">
          <div class="info-content">
            <div class="info-section">
              <h4>LLM 配置说明</h4>
              <ul>
                <li><strong>API Key</strong>：用于调用 LLM API 的密钥</li>
                <li><strong>服务地址</strong>：LLM API 的 endpoint 地址</li>
                <li><strong>模型名称</strong>：使用的模型标识符</li>
              </ul>
            </div>
            <div class="info-section">
              <h4>生成模式说明</h4>
              <ul>
                <li><strong>atomic</strong>：原子级问答对生成</li>
                <li><strong>multi_hop</strong>：多跳问答生成</li>
                <li><strong>CoT</strong>：思维链问答生成</li>
                <li><strong>multi_choice</strong>：多选问答生成</li>
              </ul>
            </div>
            <div class="info-section">
              <h4>输出格式说明</h4>
              <ul>
                <li><strong>Alpaca</strong>：Alpaca 格式</li>
                <li><strong>Sharegpt</strong>：ShareGPT 格式</li>
                <li><strong>ChatML</strong>：ChatML 格式</li>
              </ul>
            </div>
            <div class="info-section">
              <h4>分区算法说明</h4>
              <ul>
                <li><strong>ece</strong>（默认）：ECE 图分区算法</li>
                <li><strong>dfs</strong>：深度优先搜索</li>
                <li><strong>bfs</strong>：广度优先搜索</li>
                <li><strong>leiden</strong>：Leiden 图聚类算法</li>
              </ul>
            </div>
          </div>
        </ElScrollbar>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
  import type { DatasetItemDTO } from '@/api/dataset'

  defineOptions({ name: 'Step2Mapping' })

  const props = defineProps<{
    dataset: DatasetItemDTO | null
    config: Api.DataManage.DataProcessing.ProcessConfig
  }>()

  const emit = defineEmits<{
    'update:config': [config: Api.DataManage.DataProcessing.ProcessConfig]
  }>()

  const activeOperators = ref(['llmConfig', 'generationMode', 'advancedSettings'])

  function updateConfig(key: keyof Api.DataManage.DataProcessing.ProcessConfig, value: unknown) {
    emit('update:config', { ...props.config, [key]: value })
  }

  function formatSize(sizeMB: number): string {
    if (sizeMB >= 1024) return `${(sizeMB / 1024).toFixed(1)} GB`
    return `${sizeMB.toFixed(1)} MB`
  }

  watch(
    () => props.dataset,
    () => {
      // Dataset changed, could refresh samples here if needed
    }
  )
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
    background: linear-gradient(
      135deg,
      rgba(var(--el-color-primary-rgb, 64, 158, 255), 0.04) 0%,
      #fff 100%
    );
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
      background: #67c23a;
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

    &:last-child {
      border-bottom: none;
    }

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

    &__raw,
    &__processed {
      min-width: 0;
    }

    &__tag {
      display: inline-flex;
      align-items: center;
      font-size: 12px;
      font-weight: 700;
      margin-bottom: 8px;
      &.raw {
        color: #f56c6c;
      }
      &.processed {
        color: #67c23a;
      }
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
