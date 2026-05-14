<template>
  <div class="overview-page">
    <!-- 模块一：全局状态概览 -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-5 mb-6">
      <LfpStatsCard
        title="运行中 / 排队中"
        :count="activeTaskCount"
        description="当前活动任务数"
        icon="ri:timer-line"
        iconStyle="bg-blue-500"
      />
      <LfpStatsCard
        title="已纳管数据集"
        :count="datasetCount"
        :description="`总容量 ${storageTotalLabel}`"
        icon="ri:database-2-line"
        iconStyle="bg-green-500"
      />
      <LfpStatsCard
        title="已微调模型"
        :count="finetunedModelCount"
        description="可用模型数量"
        icon="ri:robot-3-line"
        iconStyle="bg-purple-500"
      />
      <LfpStatsCard
        title="已完成任务"
        :count="computeTaskCount"
        description="历史累计完成"
        icon="ri:cpu-line"
        iconStyle="bg-orange-500"
      />
    </div>

    <!-- 模块二：快捷操作区 -->
    <div class="grid grid-cols-1 lg:grid-cols-12 gap-5 mb-6 items-stretch">
      <!-- 左侧 25%：全局健康枢纽 -->
      <div class="lg:col-span-3 flex">
        <LfpDataListCard
          class="flex-1"
          title="全局健康枢纽"
          subtitle="系统守护进程状态"
          :list="serviceHealthList"
          :maxCount="4"
          :showMoreButton="false"
        />
      </div>
      <!-- 中间 50%：算力负载池 -->
      <div class="lg:col-span-6 h-[360px] overflow-hidden">
        <div class="lfp-card p-5 h-full flex flex-col">
          <h3 class="text-lg font-medium mb-4 flex-shrink-0">
            <LfpSvgIcon icon="ri:hard-drive-3-line" class="mr-2 text-blue-500 inline-block" />
            算力负载池
          </h3>
          <ElScrollbar class="flex-1">
            <div class="grid grid-cols-2 gap-7">
              <div
                v-for="gpu in gpuData"
                :key="gpu.name"
                class="lfp-card h-28 flex flex-col justify-center px-4"
              >
                <div class="flex flex-col mb-2">
                  <span class="text-lg font-semibold" :class="getGpuUsageClass(gpu.usage)"
                    >{{ gpu.usage }}%</span
                  >
                  <span class="text-xs text-g-500">{{ gpu.name }}</span>
                </div>
                <ElProgress
                  :percentage="gpu.usage"
                  :color="getGpuProgressColor(gpu.usage)"
                  :stroke-width="8"
                  :show-text="false"
                />
              </div>
            </div>
          </ElScrollbar>
        </div>
      </div>
      <!-- 右侧 25%：存储水位 -->
      <div class="lg:col-span-3 flex">
        <LfpDonutChartCard
          v-if="storageInfo"
          class="flex-1"
          title="存储水位"
          :value="storageInfo.used_gb"
          :percentage="storageInfo.percentage"
          :data="[storageInfo.used_gb, storageInfo.free_gb]"
          :currentValue="`已用 ${storageInfo.used_gb}GB`"
          :previousValue="`剩余 ${storageInfo.free_gb}GB`"
          flex
        />
        <div v-else class="flex-1 lfp-card p-5 flex items-center justify-center text-g-500 text-sm">
          存储信息不可用
        </div>
      </div>
    </div>

    <!-- 模块三：日志溯源与趋势分析 -->
    <div class="grid grid-cols-1 lg:grid-cols-10 gap-5 mb-6">
      <!-- 左侧 40%：系统吞吐量趋势 -->
      <div class="lg:col-span-4 h-[450px]">
        <LfpBarChartCard
          class="h-full"
          :value="totalDoneCount"
          label="过去7天完成任务"
          :percentage="doneTrendPercentage"
          :chartData="dailyDoneChartData"
          :xAxisData="dailyDoneXAxis"
          flex
        />
      </div>
      <!-- 中间 30%：任务简报 -->
      <div class="lg:col-span-3 h-[450px] overflow-hidden">
        <LfpTaskListCard
          class="h-full"
          title="任务简报"
          :list="taskProgressList"
          :maxCount="10"
          :showMoreButton="true"
        />
      </div>
      <!-- 右侧 30%：审计追踪 -->
      <div class="lg:col-span-3 h-[450px] overflow-hidden">
        <LfpTimelineListCard
          class="h-full"
          title="审计追踪"
          :list="auditTrailList"
          :maxCount="10"
          :showMoreButton="true"
        />
      </div>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { getDashboard, type DashboardResponse, type ServiceHealthItem } from '@/api/dashboard'

  defineOptions({ name: 'DashboardPage' })

  const dashboardData = ref<DashboardResponse | null>(null)

  // ── 统计卡片 ──────────────────────────────────────────

  const activeTaskCount = computed(() => dashboardData.value?.active_task_count ?? 0)
  const datasetCount = computed(() => dashboardData.value?.dataset_count ?? 0)
  const finetunedModelCount = computed(() => dashboardData.value?.finetuned_model_count ?? 0)
  const computeTaskCount = computed(() => dashboardData.value?.compute_task_count ?? 0)

  // ── 服务健康枢纽 ──────────────────────────────────────

  const serviceHealthList = computed(() => {
    const raw = dashboardData.value?.service_health ?? []
    return raw.map((item: ServiceHealthItem) => ({
      title: item.title,
      status: item.status,
      time: item.time,
      class: item.class_,
      icon: item.icon,
    }))
  })

  // ── GPU 数据（暂为静态） ──────────────────────────────

  const gpuData = ref([
    { name: 'GPU 0: RTX 4090', usage: 0 },
    { name: 'GPU 1: RTX 4090', usage: 0 },
    { name: 'GPU 2: RTX 4090', usage: 0 },
    { name: 'GPU 3: RTX 4090', usage: 0 },
    { name: 'GPU 4: RTX 4090', usage: 0 },
    { name: 'GPU 5: RTX 4090', usage: 0 },
    { name: 'GPU 6: RTX 4090', usage: 0 },
    { name: 'GPU 7: RTX 4090', usage: 0 },
  ])

  // ── 存储水位 ──────────────────────────────────────────

  const storageInfo = computed(() => dashboardData.value?.storage ?? null)
  const storageTotalLabel = computed(() => {
    const s = storageInfo.value
    return s ? `${s.total_gb} GB` : '—'
  })

  // ── 7 天完成任务趋势 ──────────────────────────────────

  const dailyDoneChartData = computed(() => {
    const raw = dashboardData.value?.daily_done ?? []
    return raw.map((d) => d.count)
  })

  const dailyDoneXAxis = computed(() => {
    const raw = dashboardData.value?.daily_done ?? []
    return raw.map((d) => d.date)
  })

  const totalDoneCount = computed(() => {
    return (dashboardData.value?.daily_done ?? []).reduce((sum, d) => sum + d.count, 0)
  })

  const doneTrendPercentage = computed(() => {
    const counts = dashboardData.value?.daily_done ?? []
    if (counts.length < 2) return 0
    const firstHalf = counts.slice(0, Math.floor(counts.length / 2)).reduce((s, d) => s + d.count, 0)
    const secondHalf = counts.slice(Math.floor(counts.length / 2)).reduce((s, d) => s + d.count, 0)
    if (firstHalf === 0) return secondHalf > 0 ? 100 : 0
    return Math.round(((secondHalf - firstHalf) / firstHalf) * 100)
  })

  // ── 任务简报 ──────────────────────────────────────────

  const taskProgressList = computed(() => {
    return (dashboardData.value?.task_briefing ?? []).map((t) => ({
      taskName: t.taskName,
      phase: t.phase,
      progress: t.progress,
    }))
  })

  // ── 审计追踪 ──────────────────────────────────────────

  const auditTrailList = computed(() => {
    return (dashboardData.value?.audit_trail ?? []).map((a) => ({
      time: a.time,
      status: a.status,
      content: a.content,
    }))
  })

  // ── GPU 辅助 ──────────────────────────────────────────

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

  // ── 数据加载 ──────────────────────────────────────────

  onMounted(async () => {
    const result = await getDashboard()
    if (result) {
      dashboardData.value = result
    }
  })
</script>

<style lang="scss" scoped>
  .overview-page {
    padding: 0;
  }
</style>
