<template>
  <div class="overview-page">
    <!-- 模块一：全局状态概览 -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-6">
      <LfpStatsCard
        title="运行中 / 排队中"
        :count="3"
        description="当前活动任务数"
        icon="ri:timer-line"
        iconStyle="bg-blue-500"
      />
      <LfpStatsCard
        title="已纳管数据集"
        :count="12"
        description="总容量 4.5 GB"
        icon="ri:database-2-line"
        iconStyle="bg-green-500"
      />
      <LfpStatsCard
        title="已微调模型"
        :count="5"
        description="可用模型数量"
        icon="ri:robot-3-line"
        iconStyle="bg-purple-500"
      />
      <LfpStatsCard
        title="累计算力消耗"
        :count="128"
        description="本周新增: 12 小时"
        icon="ri:cpu-line"
        iconStyle="bg-orange-500"
      />
    </div>

    <!-- 模块二：快捷操作区 -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-5 mb-6">
      <!-- 左侧 25%：全局健康枢纽 -->
      <div class="lg:col-span-3">
        <LfpDataListCard
          title="全局健康枢纽"
          subtitle="系统守护进程状态"
          :list="serviceHealthList"
        />
      </div>
      <!-- 中间 50%：算力负载池 -->
      <div class="lg:col-span-6">
        <div class="art-card p-5">
          <h3 class="text-lg font-medium mb-4">
            <LfpSvgIcon icon="ri:hard-drive-3-line" class="mr-2 text-blue-500 inline-block" />
            算力负载池
          </h3>
          <div class="space-y-3">
            <div v-for="gpu in gpuData" :key="gpu.name" class="space-y-1">
              <div class="flex justify-between text-sm">
                <span>{{ gpu.name }}</span>
                <span :class="getGpuUsageClass(gpu.usage)">{{ gpu.usage }}%</span>
              </div>
              <ElProgress
                :percentage="gpu.usage"
                :color="getGpuProgressColor(gpu.usage)"
                :stroke-width="12"
              />
            </div>
          </div>
        </div>
      </div>
      <!-- 右侧 25%：存储水位 -->
      <div class="lg:col-span-3">
        <LfpDonutChartCard
          title="存储水位"
          :value="750"
          :percentage="75"
          :data="[750, 250]"
          currentValue="已用 750GB"
          previousValue="剩余 250GB"
        />
      </div>
    </div>

    <!-- 模块三：日志溯源与趋势分析 -->
    <div class="grid grid-cols-1 lg:grid-cols-24 gap-5">
      <!-- 左侧 70%：系统吞吐量趋势 -->
      <div class="lg:col-span-16">
        <LfpLineChartCard
          :value="7"
          label="过去7天完成任务"
          :percentage="12"
          date="本周"
          :chartData="[3, 5, 2, 8, 4, 7, 6]"
          :showAreaColor="true"
        />
      </div>
      <!-- 右侧 30%：审计追踪 -->
      <div class="lg:col-span-8">
        <LfpTimelineListCard title="审计追踪" :list="auditTrailList" />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
  defineOptions({ name: 'OverviewPage' })

  const serviceHealthList = ref([
    {
      title: 'Redis',
      status: '正常',
      time: '运行中',
      class: 'bg-green-100 text-green-600',
      icon: 'ri:database-2-line'
    },
    {
      title: 'Celery',
      status: '正常',
      time: '运行中',
      class: 'bg-green-100 text-green-600',
      icon: 'ri:timer-flash-line'
    },
    {
      title: 'WebSocket',
      status: '正常',
      time: '运行中',
      class: 'bg-green-100 text-green-600',
      icon: 'ri:wifi-line'
    },
    {
      title: 'GPU Driver',
      status: '正常',
      time: '就绪',
      class: 'bg-blue-100 text-blue-600',
      icon: 'ri:hard-drive-3-line'
    }
  ])

  const gpuData = ref([
    { name: 'GPU 0: RTX 4090', usage: 95 },
    { name: 'GPU 1: RTX 4090', usage: 80 },
    { name: 'GPU 2: RTX 4090', usage: 0 },
    { name: 'GPU 3: RTX 4090', usage: 0 }
  ])

  const auditTrailList = ref([
    { time: '10 分钟前', status: 'success', content: 'Admin 启动了 Llama3 微调任务' },
    { time: '1 小时前', status: 'success', content: '数据集 清洗完成，大小 1.2GB' },
    { time: '昨天', status: 'success', content: '导出模型 Qwen-7B-chat 完成' },
    { time: '2 天前', status: 'primary', content: '新建数据集 medical-zh 成功，共 5000 条' },
    { time: '3 天前', status: 'danger', content: '训练任务 fine-tune-batch-1 失败：OOM' }
  ])

  const getGpuUsageClass = (usage: number) => {
    if (usage > 80) return 'text-red-500'
    if (usage > 50) return 'text-yellow-500'
    return 'text-green-500'
  }

  const getGpuProgressColor = (usage: number) => {
    if (usage > 80) return '#f56c6c'
    if (usage > 50) return '#e6a23c'
    return '#67c23a'
  }
</script>

<style lang="scss" scoped>
  .overview-page {
    padding: 0;
  }
</style>
