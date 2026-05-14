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
  import { useRouter } from 'vue-router'
  import { submitExport, type ExportSubmitRequest } from '@/api/llamafactory'

  defineOptions({ name: 'CheckpointTable' })

  interface CheckpointItem {
    name: string
    path: string
    step: number
    has_adapter: boolean
    evalLoss?: number
    isBest?: boolean
  }

  interface Props {
    checkpoints?: CheckpointItem[]
    baseModel?: string
    trainingTaskId?: number
  }

  const props = withDefaults(defineProps<Props>(), {
    checkpoints: () => [],
    baseModel: '',
    trainingTaskId: 0,
  })

  const router = useRouter()

  const handleExportGGUF = async (row: CheckpointItem) => {
    if (!props.baseModel) {
      ElMessage.warning('请先在训练配置中指定基础模型')
      return
    }
    try {
      const data: ExportSubmitRequest = {
        task_name: `导出-${row.name}`,
        base_model: props.baseModel,
        adapter_path: row.path,
        params: {
          export_format: 'gguf',
          quantization_method: 'q4_k_m',
        },
      }
      const resp = await submitExport(data)
      if (resp.success && resp.task_id) {
        ElMessage.success(`导出任务已提交 (ID: ${resp.task_id})`)
        router.push(`/workbench/export-monitoring/${resp.task_id}`)
      } else {
        ElMessage.error(resp.error || '导出提交失败')
      }
    } catch {
      ElMessage.error('导出请求失败，请重试')
    }
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
    border: 1px solid var(--lfp-gray-200);

    .checkpoint-title {
      display: flex;
      align-items: center;
      margin: 0 0 16px;
      font-size: 14px;
      font-weight: 600;
      color: var(--lfp-gray-800);
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
