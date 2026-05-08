<template>
  <div class="loss-chart">
    <div ref="chartRef" class="chart-container"></div>
  </div>
</template>

<script setup lang="ts">
  import * as echarts from 'echarts'
  import { onMounted, onUnmounted, ref, watch } from 'vue'
  import { lossChartMockData } from '@/mock/modules/task-dispatch'

  defineOptions({ name: 'LossChart' })

  interface Props {
    data?: Array<{ step: number; trainLoss: number; evalLoss: number }>
  }

  const props = withDefaults(defineProps<Props>(), {
    data: () => lossChartMockData
  })

  const chartRef = ref<HTMLElement>()
  let chartInstance: echarts.ECharts | null = null

  const initChart = () => {
    if (!chartRef.value) return

    chartInstance = echarts.init(chartRef.value)

    const option: echarts.EChartsOption = {
      backgroundColor: 'transparent',
      grid: {
        top: 40,
        right: 20,
        bottom: 60,
        left: 60
      },
      legend: {
        data: ['Train Loss', 'Eval Loss'],
        top: 10,
        textStyle: {
          color: '#666',
          fontSize: 12
        }
      },
      tooltip: {
        trigger: 'axis',
        backgroundColor: 'rgba(255,255,255,0.9)',
        borderColor: '#ddd',
        textStyle: {
          color: '#333'
        },
        formatter: (params: any) => {
          const data = params[0]
          const evalData = params[1]
          let result = `<strong>Step ${data.data[0]}</strong><br/>`
          result += `Train Loss: <strong>${data.data[1].toFixed(4)}</strong><br/>`
          if (evalData) {
            result += `Eval Loss: <strong>${evalData.data[1].toFixed(4)}</strong>`
          }
          return result
        }
      },
      xAxis: {
        type: 'value',
        name: 'Steps',
        nameLocation: 'center',
        nameGap: 40,
        nameTextStyle: {
          color: '#666',
          fontSize: 12
        },
        axisLine: {
          lineStyle: {
            color: '#ddd'
          }
        },
        axisLabel: {
          color: '#999'
        },
        splitLine: {
          lineStyle: {
            color: '#f0f0f0'
          }
        }
      },
      yAxis: {
        type: 'value',
        name: 'Loss',
        nameLocation: 'center',
        nameGap: 45,
        nameTextStyle: {
          color: '#666',
          fontSize: 12
        },
        axisLine: {
          lineStyle: {
            color: '#ddd'
          }
        },
        axisLabel: {
          color: '#999',
          formatter: (val: number) => val.toFixed(1)
        },
        splitLine: {
          lineStyle: {
            color: '#f0f0f0'
          }
        },
        min: 0
      },
      series: [
        {
          name: 'Train Loss',
          type: 'line',
          smooth: true,
          symbol: 'circle',
          symbolSize: 6,
          lineStyle: {
            width: 2,
            color: '#409EFF'
          },
          itemStyle: {
            color: '#409EFF'
          },
          areaStyle: {
            color: new echarts.graphic.LinearGradient(0, 0, 0, 1, [
              { offset: 0, color: 'rgba(64,158,255,0.3)' },
              { offset: 1, color: 'rgba(64,158,255,0.05)' }
            ])
          },
          data: props.data.map((d) => [d.step, d.trainLoss])
        },
        {
          name: 'Eval Loss',
          type: 'line',
          smooth: true,
          symbol: 'circle',
          symbolSize: 6,
          lineStyle: {
            width: 2,
            color: '#67C23A'
          },
          itemStyle: {
            color: '#67C23A'
          },
          data: props.data.map((d) => [d.step, d.evalLoss])
        }
      ]
    }

    chartInstance.setOption(option)
  }

  const updateChart = () => {
    if (!chartInstance) return

    chartInstance.setOption({
      series: [
        {
          data: props.data.map((d) => [d.step, d.trainLoss])
        },
        {
          data: props.data.map((d) => [d.step, d.evalLoss])
        }
      ]
    })
  }

  const handleResize = () => {
    chartInstance?.resize()
  }

  onMounted(() => {
    initChart()
    window.addEventListener('resize', handleResize)
  })

  onUnmounted(() => {
    window.removeEventListener('resize', handleResize)
    chartInstance?.dispose()
  })

  watch(
    () => props.data,
    () => updateChart(),
    { deep: true }
  )
</script>

<style lang="scss" scoped>
  .loss-chart {
    width: 100%;
    height: 100%;
    min-height: 280px;

    .chart-container {
      width: 100%;
      height: 100%;
    }
  }
</style>
