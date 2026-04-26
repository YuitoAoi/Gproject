<!-- 任务列表卡片 -->
<template>
  <div class="art-card p-5 flex flex-col overflow-hidden">
    <div class="pb-3.5 flex-shrink-0">
      <p class="text-lg font-medium">{{ title }}</p>
      <p class="text-sm text-g-600">{{ subtitle }}</p>
    </div>
    <ElScrollbar class="flex-1 min-h-0">
      <div v-for="(item, index) in list" :key="index" class="py-3">
        <div class="flex justify-between text-sm mb-1">
          <span class="truncate">{{ item.taskName }}</span>
          <span>{{ item.progress }}%</span>
        </div>
        <div class="text-xs text-g-500 mb-1">{{ item.phase }}</div>
        <ElProgress
          :percentage="item.progress"
          :color="getProgressColor(item.progress)"
          :stroke-width="6"
          :show-text="false"
        />
      </div>
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
    /** 任务名称 */
    taskName: string
    /** 当前阶段 */
    phase: string
    /** 进度百分比 */
    progress: number
  }

  interface Props {
    /** 任务列表 */
    list: TaskItem[]
    /** 标题 */
    title: string
    /** 副标题 */
    subtitle?: string
    /** 最大显示数量 */
    maxCount?: number
    /** 是否显示更多按钮 */
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