<template>
  <div class="config-snapshot">
    <h4 class="config-title">
      <ArtSvgIcon icon="ri:file-settings-line" class="text-base text-primary mr-2" />
      参数快照
    </h4>
    <div class="config-list">
      <div v-for="(item, index) in configItems" :key="index" class="config-item">
        <span class="config-label">{{ item.label }}</span>
        <span class="config-value">{{ item.value }}</span>
      </div>
    </div>
    <div class="config-actions">
      <ElButton type="primary" size="small" @click="handleClone">
        <ArtSvgIcon icon="ri:file-copy-line" class="mr-1" />
        复制参数并新建任务
      </ElButton>
    </div>
  </div>
</template>

<script setup lang="ts">
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import { ElMessage } from 'element-plus'
  import { taskDetailMockData } from '@/mock/modules/task-dispatch'

  defineOptions({ name: 'ConfigSnapshot' })

  interface ConfigItem {
    label: string
    value: string
  }

  interface Props {
    config?: typeof taskDetailMockData
  }

  const props = withDefaults(defineProps<Props>(), {
    config: () => taskDetailMockData
  })

  const configItems = computed<ConfigItem[]>(() => [
    { label: '基础模型', value: props.config.baseModel },
    { label: '训练阶段', value: props.config.trainStage },
    { label: '微调算法', value: props.config.finetuneAlgorithm },
    {
      label: '批处理量',
      value: `${props.config.batchSize} (Grad_Accumulation: ${props.config.gradAccumulation})`
    },
    { label: '学习率', value: `${props.config.learningRate} (${props.config.lrScheduler})` }
  ])

  const handleClone = () => {
    ElMessage.success('已复制参数，正在跳转至新建任务页面...')
  }
</script>

<style lang="scss" scoped>
  .config-snapshot {
    display: flex;
    flex-direction: column;
    height: 100%;
    padding: 16px;
    background: var(--el-fill-color-lighter);
    border-radius: var(--custom-radius, 8px);
    border: 1px solid var(--art-gray-200);

    .config-title {
      display: flex;
      align-items: center;
      margin: 0 0 16px;
      font-size: 14px;
      font-weight: 600;
      color: var(--art-gray-800);
    }

    .config-list {
      flex: 1;
      display: flex;
      flex-direction: column;
      gap: 12px;
      overflow-y: auto;
    }

    .config-item {
      display: flex;
      justify-content: space-between;
      align-items: center;
      padding: 8px 12px;
      background: var(--el-bg-color);
      border-radius: 6px;
      border: 1px solid var(--art-gray-200);

      .config-label {
        font-size: 13px;
        color: var(--art-gray-600);
      }

      .config-value {
        font-size: 13px;
        font-weight: 500;
        color: var(--art-gray-800);
        font-family: 'Consolas', 'Monaco', monospace;
      }
    }

    .config-actions {
      margin-top: 16px;
      padding-top: 16px;
      border-top: 1px solid var(--art-gray-200);

      .el-button {
        width: 100%;
      }
    }
  }
</style>
