<!-- 任务列表卡片 -->
<template>
  <div class="art-card p-5 flex flex-col overflow-hidden">
    <div class="pb-3.5 flex-shrink-0">
      <p class="text-lg font-medium">{{ title }}</p>
    </div>
    <ElScrollbar class="flex-1 min-h-0">
      <ArtTable
        :data="list"
        style="margin-top: 0 !important"
        :border="false"
        :stripe="false"
        :header-cell-style="{ background: 'transparent' }"
        :cell-style="{ padding: '12px 8px' }"
      >
        <template #default>
          <ElTableColumn label="任务名称" min-width="140">
            <template #default="scope">
              <div class="flex flex-col py-1">
                <span class="text-sm truncate">{{ scope.row.taskName }}</span>
                <span class="text-xs text-g-500">{{ scope.row.phase }}</span>
              </div>
            </template>
          </ElTableColumn>
          <ElTableColumn label="实时进度">
            <template #default="scope">
              <div class="flex items-center gap-2 py-1">
                <ElProgress
                  :percentage="scope.row.progress"
                  :color="getProgressColor(scope.row.progress)"
                  :stroke-width="4"
                  :show-text="false"
                  class="flex-1"
                />
                <span class="text-sm text-g-600 w-10">{{ scope.row.progress }}%</span>
              </div>
            </template>
          </ElTableColumn>
        </template>
      </ArtTable>
    </ElScrollbar>
    <ElButton
      :class="['w-full text-center', { 'mt-[25px]': showMoreButton }]"
      v-if="showMoreButton"
      v-ripple
      @click="handleMore"
      >查看更多</ElButton
    >
  </div>
</template>

<script setup lang="ts">
  defineOptions({ name: 'ArtTaskListCard' })

  interface TaskItem {
    taskName: string
    phase: string
    progress: number
  }

  interface Props {
    list: TaskItem[]
    title: string
    subtitle?: string
    maxCount?: number
    showMoreButton?: boolean
  }

  const DEFAULT_MAX_COUNT = 5

  const props = withDefaults(defineProps<Props>(), {
    maxCount: DEFAULT_MAX_COUNT,
    showMoreButton: false
  })

  const getProgressColor = (progress: number) => {
    if (progress >= 90) return '#67c23a'
    if (progress >= 50) return '#e6a23c'
    return '#409eff'
  }

  const emit = defineEmits<{
    (e: 'more'): void
  }>()

  const handleMore = () => emit('more')
</script>
