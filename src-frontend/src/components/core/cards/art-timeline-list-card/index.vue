<!-- 时间轴列表卡片 -->
<template>
  <div class="art-card p-5 flex flex-col overflow-hidden">
    <div class="pb-3.5 flex-shrink-0">
      <p class="text-lg font-medium">{{ title }}</p>
      <p class="text-sm text-g-600">{{ subtitle }}</p>
    </div>
    <ElScrollbar class="flex-1 min-h-0">
      <ElTimeline class="!pl-0.5">
        <ElTimelineItem
          v-for="item in list"
          :key="item.time"
          :timestamp="item.time"
          :placement="TIMELINE_PLACEMENT"
          :color="item.status"
          :center="true"
        >
          <div class="flex-c gap-3">
            <div class="flex-c gap-2">
              <span class="text-sm">{{ item.content }}</span>
              <span v-if="item.code" class="text-sm text-theme"> #{{ item.code }} </span>
            </div>
          </div>
        </ElTimelineItem>
      </ElTimeline>
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
  defineOptions({ name: 'ArtTimelineListCard' })

  // 常量配置
  const ITEM_HEIGHT = 65
  const TIMELINE_PLACEMENT = 'top'
  const DEFAULT_MAX_COUNT = 5

  interface TimelineItem {
    /** 时间 */
    time: string
    /** 状态颜色 */
    status: string
    /** 内容 */
    content: string
    /** 代码标识 */
    code?: string
  }

  interface Props {
    /** 时间轴列表数据 */
    list: TimelineItem[]
    /** 标题 */
    title: string
    /** 副标题 */
    subtitle?: string
    /** 最大显示数量 */
    maxCount?: number
    /** 是否显示更多按钮 */
    showMoreButton?: boolean
  }

  // Props 定义和验证
  const props = withDefaults(defineProps<Props>(), {
    title: '',
    subtitle: '',
    maxCount: DEFAULT_MAX_COUNT,
    showMoreButton: false
  })

  const maxHeight = computed(() => `${ITEM_HEIGHT * props.maxCount}px`)

  const emit = defineEmits<{
    /** 点击更多按钮事件 */
    (e: 'more'): void
  }>()

  const handleMore = () => emit('more')
</script>
