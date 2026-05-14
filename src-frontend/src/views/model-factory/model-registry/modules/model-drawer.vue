<template>
  <ElDrawer
    :model-value="visible"
    @update:model-value="$emit('update:visible', $event)"
    title="模型详情"
    size="480px"
    :destroy-on-close="true"
  >
    <template v-if="model">
      <!-- 模型基本信息 -->
      <div class="detail-header mb-6">
        <div class="detail-header__icon" :class="model.isFineTuned ? 'bg-success/10' : 'bg-primary/10'">
          <LfpSvgIcon
            :icon="model.isFineTuned ? 'ri:flashlight-line' : 'ri:brain-line'"
            :class="model.isFineTuned ? 'text-success' : 'text-primary'"
            class="text-2xl"
          />
        </div>
        <div class="detail-header__info">
          <h3 class="text-base font-semibold text-g-800 mb-1">{{ model.displayName }}</h3>
          <span class="text-sm text-g-500">{{ model.id }}</span>
        </div>
      </div>

      <ElDescriptions :column="1" border class="mb-6">
        <ElDescriptionsItem label="模型ID">
          <code class="text-xs bg-gray-50 px-2 py-0.5 rounded">{{ model.id }}</code>
        </ElDescriptionsItem>
        <ElDescriptionsItem label="组织/来源">{{ model.org || '—' }}</ElDescriptionsItem>
        <ElDescriptionsItem label="参数规模">
          <ElTag v-if="model.paramSize" size="small" effect="plain" type="primary">{{ model.paramSize }}</ElTag>
          <span v-else class="text-g-400">未知</span>
        </ElDescriptionsItem>
        <ElDescriptionsItem label="模型类型">
          <ElTag :type="model.isFineTuned ? 'success' : 'primary'" size="small" effect="dark">
            {{ model.isFineTuned ? '微调产物' : '基础模型' }}
          </ElTag>
        </ElDescriptionsItem>
        <ElDescriptionsItem label="服务状态">
          <div class="flex items-center gap-1.5">
            <span class="status-dot" :class="model.online ? 'bg-success' : 'bg-gray-300'"></span>
            <span :class="model.online ? 'text-success' : 'text-g-400'">
              {{ model.online ? '在线运行中' : '离线' }}
            </span>
          </div>
        </ElDescriptionsItem>
      </ElDescriptions>

      <!-- 快捷操作 -->
      <div class="quick-actions">
        <h4 class="text-sm font-semibold text-g-700 mb-3">快捷操作</h4>
        <div class="flex flex-col gap-2">
          <ElButton type="primary" class="!w-full" @click="handleChat">
            <LfpSvgIcon icon="ri:chat-3-line" class="mr-2" />
            对话测试
          </ElButton>
          <ElButton class="!w-full" @click="handleCopyId">
            <LfpSvgIcon icon="ri:file-copy-line" class="mr-2" />
            复制模型 ID
          </ElButton>
        </div>
      </div>
    </template>

    <div v-else class="text-center text-g-400 py-20">
      暂无数据
    </div>
  </ElDrawer>
</template>

<script setup lang="ts">
  import { useRouter } from 'vue-router'
  import { ElMessage } from 'element-plus'
  import LfpSvgIcon from '@/components/core/base/lfp-svg-icon/index.vue'

  interface ModelItem {
    id: string
    displayName: string
    org: string
    paramSize: string
    isFineTuned: boolean
    online: boolean
  }

  const props = defineProps<{
    visible: boolean
    model: ModelItem | null
  }>()

  const emit = defineEmits<{
    'update:visible': [value: boolean]
  }>()

  const router = useRouter()

  function handleChat() {
    emit('update:visible', false)
    if (props.model) {
      router.push({ path: '/model-inference', query: { model: props.model.id } })
    }
  }

  async function handleCopyId() {
    if (!props.model) return
    try {
      await navigator.clipboard.writeText(props.model.id)
      ElMessage.success('模型 ID 已复制到剪贴板')
    } catch {
      ElMessage.error('复制失败')
    }
  }
</script>

<style lang="scss" scoped>
  .detail-header {
    display: flex;
    align-items: center;
    gap: 16px;

    &__icon {
      width: 52px;
      height: 52px;
      border-radius: 12px;
      display: flex;
      align-items: center;
      justify-content: center;
      flex-shrink: 0;
    }

    &__info {
      flex: 1;
      min-width: 0;
    }
  }

  .status-dot {
    display: inline-block;
    width: 8px;
    height: 8px;
    border-radius: 50%;
  }
</style>
