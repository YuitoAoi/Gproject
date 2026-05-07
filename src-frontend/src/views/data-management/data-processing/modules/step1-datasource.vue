<template>
  <div class="step1-datasource">
    <!-- 搜索与筛选栏 -->
    <div class="flex items-center justify-between gap-4 mb-5">
      <div class="flex items-center gap-3 flex-1">
        <ElInput
          v-model="searchKeyword"
          placeholder="输入数据集名称..."
          class="!w-72"
          clearable
          @keyup.enter="handleSearch"
        >
          <template #prefix>
            <span class="ri:search-line text-g-400"></span>
          </template>
        </ElInput>
        <ElSelect v-model="filterFormat" placeholder="格式：全部" class="!w-32" clearable>
          <ElOption label="JSON" value="JSON" />
          <ElOption label="CSV" value="CSV" />
          <ElOption label="TXT" value="TXT" />
        </ElSelect>
        <ElSelect v-model="filterStatus" placeholder="状态：全部" class="!w-32" clearable>
          <ElOption label="待清洗" value="processing" />
          <ElOption label="已就绪" value="ready" />
        </ElSelect>
        <ElButton type="primary" @click="handleSearch">
          <span class="ri:search-line mr-1"></span>查询
        </ElButton>
      </div>
      <ElButton @click="handleTempUpload">
        <span class="ri:cloud-upload-line mr-1"></span>临时导入新文件
      </ElButton>
    </div>

    <!-- 标题 -->
    <div class="section-title mb-4">
      <ArtSvgIcon icon="ri:database-2-line" class="text-xl text-theme mr-2" />
      <span>请从下方资产池中选择一个要清洗的数据集：</span>
    </div>

    <!-- 数据集卡片网格 -->
    <div v-if="filteredDatasets.length > 0" class="dataset-grid">
      <div
        v-for="ds in filteredDatasets"
        :key="ds.id"
        class="dataset-card art-card"
        :class="{
          'is-selected': selectedId === ds.id,
          'is-disabled': ds.status === -1
        }"
        @click="handleSelect(ds)"
      >
        <!-- 选中状态指示器 -->
        <div class="dataset-card__radio">
          <span
            :class="
              selectedId === ds.id
                ? 'ri:radio-button-line text-xl'
                : 'ri:checkbox-blank-circle-line text-xl'
            "
            :style="{
              color: selectedId === ds.id ? 'var(--el-color-primary)' : 'var(--art-gray-300)'
            }"
          ></span>
        </div>

        <!-- 内容 -->
        <div class="dataset-card__body">
          <div class="flex items-center gap-2 mb-2">
            <span class="dataset-card__name truncate">{{ ds.name }}</span>
          </div>
          <div class="flex items-center gap-2 text-xs text-g-500 mb-3">
            <span>大小: {{ formatSize(ds.file_size) }}</span>
            <span class="text-g-300">|</span>
            <span>格式: {{ ds.format.toUpperCase() }}</span>
            <span class="text-g-300">|</span>
            <span>状态: </span>
            <ElTag :type="statusType(ds.status)" size="small" effect="plain">{{
              statusLabel(ds.status)
            }}</ElTag>
          </div>
        </div>
      </div>
    </div>

    <!-- 空状态 -->
    <div v-else class="art-card p-12 text-center">
      <ArtSvgIcon icon="ri:inbox-line" class="text-5xl text-g-400 mb-3" />
      <p class="text-g-500">未找到匹配的数据集</p>
      <p class="text-xs text-g-400 mt-1">尝试调整筛选条件或上传新数据集</p>
    </div>

    <!-- 加载状态 -->
    <div v-if="loading" class="dataset-grid">
      <div v-for="i in 6" :key="i" class="dataset-card art-card skeleton-card">
        <div class="skeleton-line w-3/4 mb-3"></div>
        <div class="skeleton-line w-1/2 mb-3"></div>
        <div class="flex gap-2">
          <div class="skeleton-tag w-12"></div>
          <div class="skeleton-tag w-16"></div>
        </div>
      </div>
    </div>

    <!-- 上传弹窗 -->
    <DatasetUpload v-model:visible="uploadVisible" @confirm="handleUploadConfirm" />
  </div>
</template>

<script setup lang="ts">
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import type { DatasetItemDTO } from '@/api/dataset'
  import DatasetUpload from '../../dataset-hub/modules/dataset-upload.vue'

  defineOptions({ name: 'Step1DataSource' })

  const props = defineProps<{
    datasets: DatasetItemDTO[]
    loading: boolean
    selectedId: number | null
  }>()

  const emit = defineEmits<{
    select: [id: number]
    upload: []
  }>()

  const searchKeyword = ref('')
  const filterFormat = ref('')
  const filterStatus = ref('')
  const uploadVisible = ref(false)

  const filteredDatasets = computed(() => {
    let list = props.datasets
    if (searchKeyword.value) {
      const kw = searchKeyword.value.toLowerCase()
      list = list.filter(
        (d) => d.name.toLowerCase().includes(kw) || (d.desc && d.desc.toLowerCase().includes(kw))
      )
    }
    if (filterFormat.value) {
      list = list.filter((d) => d.format.toUpperCase() === filterFormat.value.toUpperCase())
    }
    if (filterStatus.value) {
      const statusMap: Record<string, number> = { ready: 2, processing: 1, pending: 0, error: -1 }
      const targetStatus = statusMap[filterStatus.value]
      if (targetStatus !== undefined) {
        list = list.filter((d) => d.status === targetStatus)
      }
    }
    return list
  })

  function handleSelect(ds: DatasetItemDTO) {
    emit('select', ds.id)
  }

  function handleSearch() {}

  function handleTempUpload() {
    uploadVisible.value = true
  }

  function handleUploadConfirm() {
    uploadVisible.value = false
    emit('upload')
  }

  function formatSize(sizeMB: number): string {
    if (sizeMB >= 1024) return `${(sizeMB / 1024).toFixed(1)} GB`
    return `${sizeMB.toFixed(1)} MB`
  }

  function statusType(status: number): 'primary' | 'success' | 'info' | 'warning' | 'danger' {
    const map: Record<number, 'primary' | 'success' | 'info' | 'warning' | 'danger'> = {
      0: 'info',
      1: 'warning',
      2: 'success',
      '-1': 'danger'
    }
    return map[status] || 'info'
  }

  function statusLabel(status: number): string {
    const map: Record<number, string> = { 0: '待清洗', 1: '清洗中', 2: '已就绪', '-1': '异常' }
    return map[status] || String(status)
  }
</script>

<style lang="scss" scoped>
  .step1-datasource {
    padding: 0;
  }

  .section-title {
    display: flex;
    align-items: center;
    font-size: 14px;
    font-weight: 500;
    color: var(--art-gray-700);
  }

  .dataset-grid {
    display: grid;
    grid-template-columns: repeat(auto-fill, minmax(320px, 1fr));
    gap: 16px;
  }

  .dataset-card {
    position: relative;
    display: flex;
    padding: 20px;
    cursor: pointer;
    transition: all 0.2s ease;
    border: 2px solid transparent;
    background: #fff;

    &:not(.is-disabled):hover {
      border: solid var(--el-color-primary-light-5);
      box-shadow: 0 4px 12px rgba(var(--el-color-primary-rgb, 64, 158, 255), 0.1);
      transform: translateY(-2px);
    }

    &.is-selected {
      border: 1px solid var(--el-color-primary) !important;
      box-shadow: 0 0 0 3px rgba(var(--el-color-primary-rgb, 64, 158, 255), 0.12);
      background: linear-gradient(
        135deg,
        rgba(var(--el-color-primary-rgb, 64, 158, 255), 0.03) 0%,
        #fff 100%
      );
    }

    &.is-disabled {
      opacity: 0.5;
      cursor: not-allowed;
      background: var(--art-gray-50);
    }

    &__radio {
      display: flex;
      align-items: flex-start;
      padding-top: 2px;
      margin-right: 14px;
      flex-shrink: 0;
    }

    &__body {
      flex: 1;
      min-width: 0;
    }

    &__name {
      font-size: 14px;
      font-weight: 600;
      color: var(--art-gray-800);
    }

    &__tag {
      display: inline-flex;
      align-items: center;
      padding: 1px 8px;
      font-size: 11px;
      font-weight: 500;
      border-radius: 4px;
      border: 1px solid transparent;
      line-height: 1.5;
    }
  }

  // 骨架屏
  .skeleton-card {
    cursor: default;
    pointer-events: none;
    &:hover {
      border-color: transparent;
      box-shadow: none;
      transform: none;
    }
  }

  .skeleton-line {
    height: 14px;
    background: var(--art-gray-200);
    border-radius: 4px;
    animation: shimmer 1.5s ease-in-out infinite;
  }

  .skeleton-tag {
    height: 20px;
    background: var(--art-gray-200);
    border-radius: 4px;
    animation: shimmer 1.5s ease-in-out infinite;
  }

  @keyframes shimmer {
    0% {
      opacity: 1;
    }
    50% {
      opacity: 0.4;
    }
    100% {
      opacity: 1;
    }
  }
</style>
