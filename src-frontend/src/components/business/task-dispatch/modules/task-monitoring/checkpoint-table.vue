<template>
  <div class="checkpoint-table">
    <h4 class="checkpoint-title">
      <LfpSvgIcon icon="ri:archive-line" class="text-base text-primary mr-2" />
      产物与断点
    </h4>
    <div class="table-container">
      <ElTable :data="checkpoints" size="small" border>
        <ElTableColumn prop="name" label="检查点名称" min-width="140">
          <template #default="{ row }">
            <div class="checkpoint-name">
              <span>{{ row.name }}</span>
              <LfpSvgIcon v-if="row.isBest" icon="ri:award-fill" class="text-warning ml-1" />
            </div>
          </template>
        </ElTableColumn>
        <ElTableColumn prop="step" label="Step" width="80" align="center" />
        <ElTableColumn prop="evalLoss" label="验证Loss" width="100" align="center">
          <template #default="{ row }">
            <span :class="{ 'text-success': row.isBest }">{{ row.evalLoss.toFixed(2) }}</span>
          </template>
        </ElTableColumn>
        <ElTableColumn label="操作" width="100" align="center">
          <template #default="{ row }">
            <ElButton type="primary" size="small" text @click="handleExportGGUF(row)">
              导出GGUF
            </ElButton>
          </template>
        </ElTableColumn>
      </ElTable>
    </div>
  </div>
</template>

<script setup lang="ts">
  import LfpSvgIcon from '@/components/core/base/lfp-svg-icon/index.vue'
  import { ElMessage } from 'element-plus'
  import { checkpointListMockData, type CheckpointItem } from '@/mock/modules/task-dispatch'

  defineOptions({ name: 'CheckpointTable' })

  interface Props {
    checkpoints?: CheckpointItem[]
  }

  withDefaults(defineProps<Props>(), {
    checkpoints: () => checkpointListMockData
  })

  const handleExportGGUF = (row: CheckpointItem) => {
    ElMessage.success(`正在导出检查点 ${row.name} 为 GGUF 格式...`)
  }
</script>

<style lang="scss" scoped>
  .checkpoint-table {
    display: flex;
    flex-direction: column;
    height: 100%;
    padding: 16px;
    background: var(--el-fill-color-lighter);
    border-radius: var(--custom-radius, 8px);
    border: 1px solid var(--art-gray-200);

    .checkpoint-title {
      display: flex;
      align-items: center;
      margin: 0 0 16px;
      font-size: 14px;
      font-weight: 600;
      color: var(--art-gray-800);
    }

    .table-container {
      flex: 1;
      overflow-y: auto;

      .checkpoint-name {
        display: flex;
        align-items: center;
        font-family: 'Consolas', 'Monaco', monospace;
        font-size: 12px;
      }

      .text-success {
        color: var(--el-color-success);
        font-weight: 600;
      }
    }
  }
</style>
