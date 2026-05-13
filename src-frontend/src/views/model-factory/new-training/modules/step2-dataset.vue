<template>
  <div class="step2-dataset">
    <!-- 搜索栏 -->
    <div class="flex items-center gap-3 mb-5">
      <ElInput v-model="searchKeyword" placeholder="搜索数据集名称..." class="!w-72" clearable>
        <template #prefix>
          <LfpSvgIcon icon="ri:search-line" class="text-g-400" />
        </template>
      </ElInput>
      <span class="text-sm text-g-500">共 <span class="font-medium text-g-700">{{ filteredDatasets.length }}</span> 个数据集</span>
    </div>

    <!-- 加载骨架屏 -->
    <div v-if="loading" class="dataset-grid">
      <div v-for="i in 6" :key="i" class="dataset-card lfp-card skeleton-card">
        <div class="skeleton-line w-3/5 mb-3"></div>
        <div class="skeleton-line w-2/5 mb-4"></div>
        <div class="flex gap-2"><div class="skeleton-tag w-10"></div><div class="skeleton-tag w-14"></div></div>
      </div>
    </div>

    <!-- 数据集卡片网格 -->
    <div v-else-if="filteredDatasets.length > 0" class="dataset-grid">
      <ElTooltip v-for="ds in filteredDatasets" :key="ds.id"
        :content="ds.status !== 2 ? '数据集未就绪' : ''"
        :disabled="ds.status === 2" placement="top">
        <div class="dataset-card lfp-card"
          :class="{ 'is-selected': props.modelValue.datasetId === ds.id, 'is-disabled': ds.status !== 2 }"
          @click="handleSelect(ds)">
          <!-- 选中勾选图标 -->
          <div v-if="props.modelValue.datasetId === ds.id" class="check-overlay">
            <LfpSvgIcon icon="ri:check-line" class="text-white text-base" />
          </div>
          <!-- 卡片头部：名称 + 格式标签 -->
          <div class="flex items-start justify-between gap-2 mb-3">
            <span class="dataset-card__name truncate flex-1" :title="ds.name">{{ ds.name }}</span>
            <ElTag :type="formatTagType(ds.format)" size="small" effect="plain" class="flex-shrink-0">{{ ds.format.toUpperCase() }}</ElTag>
          </div>
          <!-- 卡片元信息：大小 + 更新时间 -->
          <div class="flex items-center gap-2 text-xs text-g-500 mb-3 flex-wrap">
            <div class="flex items-center gap-1"><LfpSvgIcon icon="ri:hard-drive-2-line" class="text-g-400" /><span>{{ formatSize(ds.file_size) }}</span></div>
            <span class="text-g-200">|</span>
            <div class="flex items-center gap-1"><LfpSvgIcon icon="ri:time-line" class="text-g-400" /><span>{{ formatDate(ds.updated_at) }}</span></div>
          </div>
          <!-- 状态行 -->
          <div class="flex items-center gap-1.5">
            <span class="status-dot" :style="{ backgroundColor: statusDot(ds.status) }"></span>
            <span class="text-xs" :style="{ color: statusDot(ds.status) }">{{ statusText(ds.status) }}</span>
          </div>
          <!-- 禁用遮罩层 -->
          <div v-if="ds.status !== 2" class="disabled-overlay"><LfpSvgIcon icon="ri:lock-line" class="text-g-400 text-lg" /></div>
        </div>
      </ElTooltip>
    </div>

    <!-- 空状态 -->
    <div v-else class="lfp-card p-14 text-center">
      <LfpSvgIcon icon="ri:inbox-line" class="text-5xl text-g-300 mb-4" />
      <p class="text-g-500 mb-1">{{ searchKeyword ? '未找到匹配的数据集' : '暂无可用数据集' }}</p>
      <p class="text-xs text-g-400 mt-2">
        <template v-if="searchKeyword">尝试修改搜索关键词</template>
        <template v-else>
          <router-link to="/data-management/dataset-hub" class="text-primary hover:underline cursor-pointer">请先到数据集中心导入数据</router-link>
        </template>
      </p>
    </div>

    <!-- 校验错误提示 -->
    <div v-if="validationError" class="flex items-center gap-1.5 mt-3">
      <LfpSvgIcon icon="ri:error-warning-line" class="text-danger text-sm" />
      <span class="text-xs text-danger">{{ validationError }}</span>
    </div>
  </div>
</template>

<script setup lang="ts">
  import { ref, computed, onMounted } from 'vue'
  import { ElInput, ElTag, ElTooltip } from 'element-plus'
  import LfpSvgIcon from '@/components/core/base/lfp-svg-icon/index.vue'
  import { getDatasets, type DatasetItemDTO } from '@/api/dataset'

  defineOptions({ name: 'Step2Dataset' })

  interface DatasetConfig {
    datasetId: number | null
    datasetName: string
  }

  const props = defineProps<{
    modelValue: DatasetConfig
  }>()

  const emit = defineEmits<{
    'update:modelValue': [value: DatasetConfig]
  }>()

  const datasets = ref<DatasetItemDTO[]>([])
  const loading = ref(false)
  const searchKeyword = ref('')
  const validationError = ref('')

  /** 按搜索关键词过滤，已就绪排前 */
  const filteredDatasets = computed(() => {
    let result = datasets.value
    if (searchKeyword.value.trim()) {
      const kw = searchKeyword.value.trim().toLowerCase()
      result = result.filter((ds) => ds.name.toLowerCase().includes(kw))
    }
    return [...result].sort((a, b) => (a.status === 2 ? -1 : 1) - (b.status === 2 ? -1 : 1))
  })

  onMounted(async () => { await fetchDatasets() })

  async function fetchDatasets() {
    loading.value = true
    try {
      const res = await getDatasets()
      datasets.value = res.records || []
    } catch (err) { console.error('[Step2Dataset] 获取数据集列表失败:', err); datasets.value = [] }
    finally { loading.value = false }
  }

  function handleSelect(ds: DatasetItemDTO) {
    if (ds.status !== 2) return
    validationError.value = ''
    emit('update:modelValue', { datasetId: ds.id, datasetName: ds.name })
  }

  const formatSize = (size: number): string => {
    if (size >= 1073741824) return (size / 1073741824).toFixed(2) + ' GB'
    if (size >= 1048576) return (size / 1048576).toFixed(1) + ' MB'
    if (size >= 1024) return (size / 1024).toFixed(1) + ' KB'
    return size + ' B'
  }

  function formatDate(dateStr: string): string {
    if (!dateStr) return '—'
    try {
      return new Date(dateStr).toLocaleDateString('zh-CN', { month: '2-digit', day: '2-digit', hour: '2-digit', minute: '2-digit' })
    } catch { return '—' }
  }

  function formatTagType(format: string): 'primary' | 'warning' | 'info' {
    const f = format.toLowerCase()
    if (f === 'json' || f === 'jsonl') return 'primary'
    if (f === 'csv') return 'warning'
    return 'info'
  }

  function statusDot(status: number): string {
    const map: Record<number, string> = { 2: '#67C23A', 1: '#409EFF', 0: '#E6A23C', [-1]: '#F56C6C' }
    return map[status] ?? '#909399'
  }

  function statusText(status: number): string {
    const map: Record<number, string> = { 2: '已就绪', 1: '清洗中', 0: '待清洗', [-1]: '异常' }
    return map[status] ?? String(status)
  }

  /** validate(): 校验是否已选择数据集，供父级步骤向导调用 */
  function validate(): boolean {
    if (!props.modelValue.datasetId) {
      validationError.value = '请选择一个数据集后再继续'
      return false
    }
    validationError.value = ''
    return true
  }

  defineExpose({ validate })
</script>

<style lang="scss" scoped>
  .step2-dataset { padding: 0; }

  .dataset-grid {
    display: grid;
    grid-template-columns: repeat(1, 1fr);
    gap: 16px;
    @media (min-width: 640px) { grid-template-columns: repeat(2, 1fr); }
    @media (min-width: 1024px) { grid-template-columns: repeat(3, 1fr); }
  }

  .dataset-card {
    position: relative;
    padding: 18px 20px;
    cursor: pointer;
    transition: border-color 0.2s ease, box-shadow 0.2s ease, transform 0.2s ease;
    border: 2px solid transparent;
    overflow: hidden;
    &:not(.is-disabled):hover {
      border-color: var(--el-color-primary-light-5);
      box-shadow: 0 4px 14px rgba(64, 158, 255, 0.12);
      transform: translateY(-2px);
    }
    &.is-selected {
      border-color: var(--el-color-primary) !important;
      box-shadow: 0 0 0 3px rgba(64, 158, 255, 0.14) !important;
      background: linear-gradient(135deg, rgba(64, 158, 255, 0.04) 0%, #fff 100%);
    }
    &.is-disabled {
      cursor: not-allowed;
      &:hover { transform: none; border-color: transparent; box-shadow: none; }
    }
    &__name {
      font-size: 14px;
      font-weight: 600;
      color: var(--lfp-gray-800, #2c3e50);
      line-height: 1.4;
      display: block;
    }
  }

  .check-overlay {
    position: absolute; top: 0; right: 0;
    width: 26px; height: 26px;
    background-color: var(--el-color-primary);
    border-radius: 0 calc(var(--custom-radius, 8px) + 2px) 0 8px;
    display: flex; align-items: center; justify-content: center;
    z-index: 2;
  }

  .disabled-overlay {
    position: absolute; inset: 0;
    background-color: rgba(255, 255, 255, 0.65);
    display: flex; align-items: center; justify-content: center;
    border-radius: inherit;
    backdrop-filter: blur(1px);
    z-index: 1;
  }

  .status-dot {
    display: inline-block;
    width: 7px; height: 7px;
    border-radius: 50%;
    flex-shrink: 0;
  }

  .skeleton-card {
    cursor: default; pointer-events: none;
    &:hover { transform: none; border-color: transparent; box-shadow: none; }
  }
  .skeleton-line {
    height: 13px; background: var(--lfp-gray-200, #ebeef5);
    border-radius: 4px; animation: shimmer 1.5s ease-in-out infinite;
  }
  .skeleton-tag {
    height: 20px; background: var(--lfp-gray-200, #ebeef5);
    border-radius: 4px; animation: shimmer 1.5s ease-in-out infinite;
  }
  @keyframes shimmer {
    0%   { opacity: 1; }
    50%  { opacity: 0.4; }
    100% { opacity: 1; }
  }
</style>
