<!-- 柱状图卡片 -->
<template>
  <div
    class="art-card overflow-hidden flex flex-col"
    :style="{ height: flex ? '100%' : `${height}rem` }"
  >
    <div class="mb-2.5 flex-b items-start p-5 flex-shrink-0">
      <div>
        <p class="text-2xl font-medium leading-none">
          {{ value }}
        </p>
        <p class="mt-1 text-sm text-g-500">{{ label }}</p>
      </div>
      <div class="text-sm font-medium" :class="percentage > 0 ? 'text-success' : 'text-danger'">
        {{ percentage > 0 ? '+' : '' }}{{ percentage }}%
      </div>
    </div>
    <div class="flex-1 min-h-0 p-5 pt-0">
      <ArtBarChart
        class="h-full"
        :data="chartData"
        :xAxisData="xAxisData"
        :barWidth="barWidth"
        :borderRadius="4"
      />
    </div>
  </div>
</template>

<script setup lang="ts">
  defineOptions({ name: 'ArtBarChartCard' })

  interface Props {
    value: number
    label: string
    percentage: number
    height?: number
    flex?: boolean
    chartData: number[]
    xAxisData?: string[]
    barWidth?: string
  }

  const props = withDefaults(defineProps<Props>(), {
    height: 11,
    flex: false,
    xAxisData: () => ['周一', '周二', '周三', '周四', '周五', '周六', '周日'],
    barWidth: '26%'
  })
</script>
