<!-- 环型图卡片 -->
<template>
  <div
    class="art-card overflow-hidden"
    :class="flex ? 'flex flex-col' : ''"
    :style="flex ? {} : { height: `${height}rem` }"
  >
    <div class="flex box-border h-full p-5" :class="flex ? 'flex-1 min-h-0' : ''">
      <div class="flex w-full flex-col items-center">
        <p class="self-start text-lg font-medium leading-tight text-g-900 mb-3">
          {{ title }}
        </p>
        <div ref="chartRef" class="w-full flex-1"></div>
        <div class="flex gap-6 text-sm text-g-600">
          <div v-if="currentValue" class="flex items-center">
            <div class="size-2 bg-theme/100 rounded mr-2"></div>
            {{ currentValue }}
          </div>
          <div v-if="previousValue" class="flex items-center">
            <div class="size-2 bg-g-400 rounded mr-2"></div>
            {{ previousValue }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { type EChartsOption } from '@/plugins/echarts'
  import { useChartOps, useChartComponent } from '@/hooks/core/useChart'

  defineOptions({ name: 'ArtDonutChartCard' })

  interface Props {
    /** 数值 */
    value: number
    /** 标题 */
    title: string
    /** 百分比 */
    percentage: number
    /** 百分比标签 */
    percentageLabel?: string
    /** 当前年份 */
    currentValue?: string
    /** 去年年份 */
    previousValue?: string
    /** 高度 */
    height?: number
    /** 是否使用自适应高度（配合 flex 使用） */
    flex?: boolean
    /** 颜色 */
    color?: string
    /** 半径 */
    radius?: [string, string]
    /** 数据 */
    data: [number, number]
  }

  const props = withDefaults(defineProps<Props>(), {
    height: 9,
    flex: false,
    radius: () => ['60%', '75%'],
    data: () => [0, 0]
  })

  const formatNumber = (num: number) => {
    return num.toLocaleString()
  }

  // 使用新的图表组件抽象
  const chartHeight = computed(() => (props.flex ? '100%' : `${props.height}rem`))
  const { chartRef } = useChartComponent({
    props: {
      height: chartHeight.value,
      loading: false,
      isEmpty: props.data.every((val) => val === 0)
    },
    checkEmpty: () => props.data.every((val) => val === 0),
    watchSources: [
      () => props.data,
      () => props.color,
      () => props.radius,
      () => props.currentValue,
      () => props.previousValue
    ],
    generateOptions: (): EChartsOption => {
      const computedColor = props.color || useChartOps().themeColor

      return {
        series: [
          {
            type: 'pie',
            radius: props.radius,
            center: ['50%', '45%'],
            avoidLabelOverlap: false,
            label: {
              show: true,
              position: 'center',
              formatter: `{a|${props.percentage}%}`,
              rich: {
                a: {
                  fontSize: 20,
                  fontWeight: 'bold',
                  color: '#303133',
                  lineHeight: 26
                }
              }
            },
            data: [
              {
                value: props.data[0],
                name: props.currentValue,
                itemStyle: { color: computedColor }
              },
              {
                value: props.data[1],
                name: props.previousValue,
                itemStyle: { color: '#e6e8f7' }
              }
            ]
          }
        ]
      }
    }
  })
</script>
