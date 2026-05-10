<template>
  <ElDrawer
    v-model="drawerVisible"
    :title="drawerTitle"
    size="30%"
    direction="rtl"
    destroy-on-close
    :before-close="handleBeforeClose"
  >
    <template #header>
      <div class="flex items-center justify-between w-full">
        <div class="flex items-center gap-2">
          <span class="ri:file-text-line text-xl text-primary"></span>
          <span class="text-base font-semibold">{{ dataset?.name }}</span>
        </div>
        <ElButton text @click="drawerVisible = false">
          <span class="ri:close-line text-lg"></span>
        </ElButton>
      </div>
    </template>

    <ElTabs v-model="activeTab" class="drawer-tabs">
      <ElTabPane label="数据集信息" name="meta">
        <div class="p-2">
          <div class="metadata-grid">
            <div class="meta-item">
              <span class="meta-label">数据集名称</span>
              <span class="meta-value">{{ dataset?.name }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">文件格式</span>
              <ElTag size="small" :type="formatTagType">{{ dataset?.format?.toUpperCase() }}</ElTag>
            </div>
            <div class="meta-item">
              <span class="meta-label">文件大小</span>
              <span class="meta-value">{{ formatSize(dataset?.file_size || 0) }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">创建时间</span>
              <span class="meta-value">{{ formatDate(dataset?.created_at) }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">最后修改</span>
              <span class="meta-value">{{ formatDate(dataset?.updated_at) }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">状态</span>
              <span class="meta-value">{{ statusText }}</span>
            </div>
          </div>
          <div class="mt-5 pt-4 border-t border-g-100">
            <h4 class="text-sm font-medium text-g-700 mb-3">数据血缘</h4>
            <div class="text-center py-6 text-g-400">
              <span class="ri:git-branch-line text-3xl block mb-2"></span>
              <p class="text-sm">该数据集无血缘关系</p>
              <p class="text-xs mt-1">直接导入的原始数据集不会有衍生链路</p>
            </div>
          </div>
        </div>
      </ElTabPane>

      <ElTabPane label="编辑数据集" name="edit">
        <div class="p-2">
          <ElForm label-width="80px" label-position="top">
            <ElFormItem label="数据集名称">
              <ElInput v-model="editForm.name" placeholder="数据集名称" />
            </ElFormItem>
            <ElFormItem label="标签">
              <div class="tag-editor">
                <ElTag
                  v-for="tag in resolvedTags"
                  :key="tag.tag_id"
                  closable
                  size="default"
                  :style="{ backgroundColor: tag.tag_color, borderColor: tag.tag_color }"
                  class="mr-1 mb-1"
                  effect="dark"
                  @close="removeTag(tag.tag_id)"
                >
                  {{ tag.tag_name }}
                </ElTag>
                <span class="tag-add-btn" @click="tagDialogVisible = true">
                  <ArtSvgIcon icon="ri:add-line" class="tag-add-icon" />
                </span>
              </div>
            </ElFormItem>
            <ElFormItem label="描述">
              <ElInput v-model="editForm.desc" type="textarea" :rows="3" placeholder="数据集描述" />
            </ElFormItem>
            <ElFormItem>
              <ElButton type="primary" :loading="saveLoading" @click="handleSave"
                >保存修改</ElButton
              >
              <ElButton class="ml-2" @click="handleReset">重置</ElButton>
            </ElFormItem>
          </ElForm>
        </div>
      </ElTabPane>

      <ElTabPane label="样本预览" name="samples">
        <div class="p-2">
          <div v-if="sampleLoading" class="flex items-center justify-center py-10">
            <span class="ri:loader-4-line text-2xl text-g-400 animate-spin"></span>
          </div>
          <div v-else>
            <div
              v-if="sampleError"
              class="text-center py-4 text-danger bg-danger-light rounded mb-3"
            >
              <span class="ri:error-warning-line text-lg block mb-1"></span>
              <p class="text-xs">{{ sampleError }}</p>
            </div>
            <div v-if="samples.length === 0 && !sampleError" class="text-center py-10 text-g-400">
              <span class="ri:file-list-3-line text-3xl block mb-2"></span>
              <p class="text-sm">暂无预览数据</p>
            </div>
            <div v-if="samples.length > 0" class="sample-preview">
              <div v-if="!isRawTextMode" class="sample-preview-header">
                <span class="text-xs text-g-500">
                  当前预览前 <strong class="text-g-700">{{ samples.length }}</strong> 条
                </span>
              </div>
              <div v-if="isRawTextMode" class="raw-text-area">
                <pre class="raw-text-code">{{ rawTextContent }}</pre>
              </div>
              <div v-else class="sample-table-wrapper">
                <ElTable
                  :data="samples"
                  border
                  stripe
                  size="small"
                  max-height="620px"
                  style="width: 100%"
                >
                  <ElTableColumn type="index" label="#" width="50" align="center" />
                  <ElTableColumn
                    v-for="col in sampleColumns"
                    :key="col"
                    :prop="col"
                    :label="col"
                    :min-width="140"
                  >
                    <template #default="{ row }">
                      {{ formatCellValue(row[col]) }}
                    </template>
                  </ElTableColumn>
                </ElTable>
              </div>
              <div class="sample-preview-footer">
                <ElButton type="primary" size="small" @click="openFullPreview">
                  <span class="ri:fullscreen-line mr-1"></span>完整预览
                </ElButton>
              </div>
            </div>
          </div>
        </div>
      </ElTabPane>

      <ElTabPane label="操作日志" name="logs">
        <div class="p-2">
          <div class="text-center py-10 text-g-400">
            <span class="ri:time-line text-3xl block mb-2"></span>
            <p class="text-sm">暂无操作日志</p>
          </div>
        </div>
      </ElTabPane>
    </ElTabs>

    <template #footer>
      <div class="flex justify-end gap-3">
        <ElButton @click="handleDownload">
          <span class="ri:download-2-line mr-1"></span>下载文件
        </ElButton>
        <ElButton type="primary" @click="handleClean">
          <span class="ri:brush-line mr-1"></span>去清洗
        </ElButton>
      </div>
    </template>

    <ElDialog
      v-model="tagDialogVisible"
      title="编辑标签"
      width="420px"
      :close-on-click-modal="false"
    >
      <div class="tag-dialog-content">
        <div class="mb-4">
          <div class="text-sm text-g-500 mb-3">已有标签（点击选择）</div>
          <div class="tag-list-wrap">
            <div
              v-for="tag in tagStore.tags"
              :key="tag.tag_id"
              class="tag-item-wrap"
              @mouseenter="hoveredTagId = tag.tag_id"
              @mouseleave="hoveredTagId = null"
            >
              <ElTag
                size="small"
                :style="{ backgroundColor: tag.tag_color, borderColor: tag.tag_color }"
                effect="dark"
                class="mr-1 mb-1 cursor-pointer"
                :class="{ 'tag-selected': newTagForm.tag_id === tag.tag_id }"
                @click="selectExistingTag(tag)"
              >
                {{ tag.tag_name }}
              </ElTag>
              <span
                v-show="hoveredTagId === tag.tag_id"
                class="tag-delete-btn"
                @click.stop="handleDeleteTag(tag)"
              >
                <ArtSvgIcon icon="ri-close-line" />
              </span>
            </div>
            <span v-if="tagStore.tags.length === 0" class="text-xs text-g-400">暂无可用标签</span>
          </div>
        </div>
        <div class="tag-form">
          <div class="text-sm text-g-500 mb-3">新建标签</div>
          <ElInput v-model="newTagForm.name" placeholder="请输入标签名称" class="mb-3" />
          <div class="flex items-center gap-2">
            <span class="text-sm text-g-500">选择颜色</span>
            <div class="color-picker">
              <span
                v-for="color in colorPresets"
                :key="color"
                class="color-dot"
                :class="{ active: newTagForm.color === color }"
                :style="{ backgroundColor: color }"
                @click="newTagForm.color = color"
              ></span>
            </div>
          </div>
          <div class="mt-3">
            <ElTag :color="newTagForm.color || '#67C23A'" effect="dark">
              {{ newTagForm.name || '标签预览' }}
            </ElTag>
          </div>
        </div>
      </div>
      <template #footer>
        <ElButton @click="tagDialogVisible = false">取消</ElButton>
        <ElButton type="primary" :loading="tagLoading" @click="handleAddTag">确定</ElButton>
      </template>
    </ElDialog>

    <ElDialog
      v-model="fullPreviewVisible"
      :title="`完整预览 — ${dataset?.name || ''}`"
      width="85%"
      top="3vh"
      destroy-on-close
      :close-on-click-modal="false"
    >
      <div v-if="fullPreviewLoading" class="flex items-center justify-center py-16">
        <span class="ri:loader-4-line text-3xl text-g-400 animate-spin"></span>
      </div>
      <div v-else-if="fullPreviewError" class="text-center py-10 text-danger">
        <span class="ri:error-warning-line text-3xl block mb-2"></span>
        <p class="text-sm">{{ fullPreviewError }}</p>
      </div>
      <div v-else-if="fullPreviewData.length === 0" class="text-center py-10 text-g-400">
        <span class="ri:file-list-3-line text-3xl block mb-2"></span>
        <p class="text-sm">暂无预览数据</p>
      </div>
      <div v-else class="full-preview-body">
        <div v-if="!isFullRawTextMode" class="sample-preview-header mb-3">
          <span class="text-xs text-g-500">
            当前预览前 <strong class="text-g-700">{{ fullPreviewData.length }}</strong> 条
          </span>
        </div>
        <div v-if="isFullRawTextMode" class="raw-text-area">
          <pre class="raw-text-code">{{ fullRawTextContent }}</pre>
        </div>
        <ElTable
          v-else
          :data="fullPreviewData"
          border
          stripe
          size="small"
          max-height="70vh"
          style="width: 100%"
          class="full-preview-table"
        >
          <ElTableColumn type="index" label="#" width="50" align="center" />
          <ElTableColumn
            v-for="col in fullPreviewColumns"
            :key="col"
            :prop="col"
            :label="col"
            :min-width="140"
          >
            <template #default="{ row }">
              {{ formatCellValue(row[col]) }}
            </template>
          </ElTableColumn>
        </ElTable>
      </div>
      <template #footer>
        <ElButton @click="fullPreviewVisible = false">关闭</ElButton>
      </template>
    </ElDialog>
  </ElDrawer>
</template>

<script setup lang="ts">
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import { useRouter } from 'vue-router'
  import { ElMessage } from 'element-plus'
  import {
    getDatasetSample,
    getDatasetTimes,
    requestDownloadToken,
    updateDataset,
    type Dataset,
    type DatasetItemDTO
  } from '@/api/dataset'
  import { useTagStore, type TagInfo } from '@/store/modules/tag'

  interface Props {
    visible: boolean
    dataset: DatasetItemDTO | null
  }

  interface Emits {
    (e: 'update:visible', value: boolean): void
    (e: 'refresh'): void
  }

  const props = defineProps<Props>()
  const emit = defineEmits<Emits>()
  const router = useRouter()

  const activeTab = ref('meta')
  const drawerVisible = computed({
    get: () => props.visible,
    set: (value) => emit('update:visible', value)
  })
  const drawerTitle = computed(() => props.dataset?.name || '数据集详情')

  const editForm = reactive({
    name: '',
    desc: '',
    tag_ids: [] as number[]
  })

  const tagStore = useTagStore()
  const samples = ref<Record<string, any>[]>([])
  const sampleColumns = ref<string[]>([])
  const sampleTotal = ref(0)
  const sampleLoading = ref(false)
  const sampleError = ref<string | null>(null)
  const fullPreviewVisible = ref(false)
  const fullPreviewLoading = ref(false)
  const fullPreviewError = ref<string | null>(null)
  const fullPreviewData = ref<Record<string, any>[]>([])
  const fullPreviewColumns = ref<string[]>([])
  const saveLoading = ref(false)
  const tagLoading = ref(false)
  const hoveredTagId = ref<number | null>(null)

  const formatTagType = computed(() => {
    const fmt = props.dataset?.format
    if (fmt === 'json') return 'primary' as const
    if (fmt === 'csv') return 'warning' as const
    return 'info' as const
  })

  const statusText = computed(() => {
    if (props.dataset?.status === 2) return '已就绪'
    if (props.dataset?.status === 1) return '清洗中'
    if (props.dataset?.status === -1) return '异常'
    return '待清洗'
  })

  const isRawTextMode = computed(() => {
    return sampleColumns.value.length === 1 && sampleColumns.value[0] === 'content'
  })

  const isFullRawTextMode = computed(() => {
    return fullPreviewColumns.value.length === 1 && fullPreviewColumns.value[0] === 'content'
  })

  const rawTextContent = computed(() => {
    return samples.value.map((s) => s.content).join('\n')
  })

  const fullRawTextContent = computed(() => {
    return fullPreviewData.value.map((s) => s.content).join('\n')
  })

  const formatSize = (size: number): string => {
    if (size >= 1024 * 1024 * 1024) return `${(size / (1024 * 1024 * 1024)).toFixed(2)} GB`
    if (size >= 1024 * 1024) return `${(size / (1024 * 1024)).toFixed(1)} MB`
    if (size >= 1024) return `${(size / 1024).toFixed(1)} KB`
    return `${size} B`
  }

  const formatDate = (dateStr: string | undefined): string => {
    if (!dateStr) return '—'
    const date = new Date(dateStr)
    return date.toLocaleDateString('zh-CN', {
      year: 'numeric',
      month: '2-digit',
      day: '2-digit',
      hour: '2-digit',
      minute: '2-digit'
    })
  }

  const resolvedTags = computed(() => {
    return tagStore.tags.filter((t) => (editForm.tag_ids || []).includes(t.tag_id))
  })

  watch(
    () => props.dataset,
    (dataset) => {
      if (dataset) {
        editForm.name = dataset.name || ''
        editForm.desc = dataset.desc || ''
        editForm.tag_ids = [...(dataset.tag_ids || [])]
      }
    },
    { immediate: true }
  )

  const handleBeforeClose = () => {
    drawerVisible.value = false
  }

  watch(activeTab, (tab) => {
    if (tab === 'samples' && props.dataset?.id) {
      loadSamples(props.dataset.id)
    }
  })

  const setActiveTab = (tab: string) => {
    activeTab.value = tab
  }

  const loadSamples = async (datasetId: number) => {
    sampleLoading.value = true
    samples.value = []
    sampleColumns.value = []
    sampleTotal.value = 0
    sampleError.value = null
    const res = await getDatasetSample(datasetId)
    if (res.rows && res.rows.length > 0) {
      samples.value = res.rows
      sampleColumns.value =
        res.columns && res.columns.length > 0 ? res.columns : Object.keys(res.rows[0])
      sampleTotal.value = res.total_rows || 0
    } else if (res.error) {
      sampleError.value = res.error
    }
    sampleLoading.value = false
  }

  const formatCellValue = (value: any): string => {
    if (value === null || value === undefined) return '—'
    if (typeof value === 'object') return JSON.stringify(value)
    return String(value)
  }

  const openFullPreview = async () => {
    fullPreviewVisible.value = true
    fullPreviewLoading.value = true
    fullPreviewData.value = []
    fullPreviewColumns.value = []
    fullPreviewError.value = null
    const res = await getDatasetSample(props.dataset!.id, 200)
    if (res.rows && res.rows.length > 0) {
      fullPreviewData.value = res.rows
      fullPreviewColumns.value =
        res.columns && res.columns.length > 0 ? res.columns : Object.keys(res.rows[0])
    } else if (res.error) {
      fullPreviewError.value = res.error
    }
    fullPreviewLoading.value = false
  }

  const handleReset = () => {
    if (!props.dataset) return
    editForm.name = props.dataset.name || ''
    editForm.desc = props.dataset.desc || ''
    editForm.tag_ids = [...(props.dataset.tag_ids || [])]
  }

  const handleSave = async () => {
    saveLoading.value = true
    const res = await updateDataset({
      dataset_id: props.dataset!.id,
      ...(editForm.name.trim() ? { name: editForm.name.trim() } : {}),
      desc: editForm.desc,
      tag_ids: editForm.tag_ids
    })
    saveLoading.value = false
    if (res.success) {
      ElMessage.success('保存成功')
      await fetchTimes()
      emit('refresh')
      drawerVisible.value = false
    } else {
      ElMessage.error(res.error || '保存失败')
    }
  }

  const fetchTimes = async () => {
    try {
      await getDatasetTimes()
    } catch {
      // ignore
    }
  }

  const removeTag = (tagId: number) => {
    editForm.tag_ids = editForm.tag_ids.filter((id) => id !== tagId)
  }

  const handleDownload = async () => {
    if (!props.dataset?.id) return
    const res = await requestDownloadToken(props.dataset.id)
    if (res?.download_token) {
      window.open(`/down_dataset/${res.download_token}`, '_blank')
    } else {
      ElMessage.error('获取下载链接失败')
    }
  }

  const handleClean = () => {
    if (!props.dataset?.id) return
    router.push({
      path: '/data-management/data-processing',
      query: { datasetId: String(props.dataset.id), step: '2' }
    })
  }

  const tagDialogVisible = ref(false)
  const colorPresets = ['#67C23A', '#409EFF', '#E6A23C', '#F56C6C', '#909399', '#1D84FF', '#5D87FF']
  const newTagForm = reactive({
    tag_id: null as number | null,
    name: '',
    color: '#67C23A'
  })

  const selectExistingTag = (tag: TagInfo) => {
    newTagForm.tag_id = tag.tag_id
    newTagForm.name = tag.tag_name
    newTagForm.color = tag.tag_color
  }

  const handleDeleteTag = async (tag: TagInfo) => {
    try {
      await ElMessageBox.confirm(
        `确定要删除标签「${tag.tag_name}」吗？删除后不可恢复。`,
        '删除标签',
        { confirmButtonText: '确定删除', cancelButtonText: '取消', type: 'warning' }
      )
      const res = await tagStore.removeTag(tag.tag_id)
      if (res.success) {
        ElMessage.success('标签已删除')
        if (newTagForm.tag_id === tag.tag_id) {
          newTagForm.tag_id = null
          newTagForm.name = ''
          newTagForm.color = '#67C23A'
        }
      } else {
        ElMessage.error(res.error || '删除标签失败')
      }
    } catch {
      // user cancelled
    }
  }

  const handleAddTag = async () => {
    if (!newTagForm.name.trim()) {
      ElMessage.warning('请输入标签名称')
      return
    }
    if (newTagForm.tag_id && !editForm.tag_ids.includes(newTagForm.tag_id)) {
      editForm.tag_ids.push(newTagForm.tag_id)
      ElMessage.success('标签已添加')
      tagDialogVisible.value = false
      newTagForm.tag_id = null
      newTagForm.name = ''
      newTagForm.color = '#67C23A'
      return
    }
    tagLoading.value = true
    const res = await tagStore.addTag(newTagForm.name, newTagForm.color)
    tagLoading.value = false
    if (res.success) {
      ElMessage.success('标签创建成功')
      const created = tagStore.tags.find((t) => t.tag_name === newTagForm.name)
      if (created && !editForm.tag_ids.includes(created.tag_id)) {
        editForm.tag_ids.push(created.tag_id)
      }
      tagDialogVisible.value = false
      newTagForm.tag_id = null
      newTagForm.name = ''
      newTagForm.color = '#67C23A'
    } else {
      ElMessage.error(res.error || '创建标签失败')
    }
  }

  onMounted(() => {
    tagStore.fetchTags()
  })

  defineExpose({ setActiveTab })
</script>

<style lang="scss" scoped>
  .drawer-tabs {
    height: 100%;
  }
  .drawer-tabs :deep(.el-tabs__content) {
    height: calc(100% - 40px);
    overflow-y: auto;
  }
  .metadata-grid {
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 16px;
  }
  .meta-item {
    display: flex;
    flex-direction: column;
    gap: 4px;
  }
  .meta-label {
    font-size: 12px;
    color: var(--el-text-color-secondary);
  }
  .meta-value {
    font-size: 14px;
    color: var(--el-text-color-primary);
    font-weight: 500;
  }
  .tag-editor {
    display: flex;
    flex-wrap: wrap;
    align-items: center;

    .el-tag {
      border-color: transparent;
    }
  }
  .sample-preview {
    display: flex;
    flex-direction: column;
    gap: 8px;
  }
  .sample-preview-header {
    display: flex;
    align-items: center;
    justify-content: space-between;
    padding: 0 4px;
  }
  .sample-table-wrapper {
    border-radius: 6px;
    overflow: hidden;

    :deep(.el-table) {
      font-size: 12px;
    }
    :deep(.el-table th) {
      background-color: var(--el-fill-color-light);
      font-weight: 600;
    }
    :deep(.el-table__cell) {
      padding: 6px 8px;
    }
    :deep(.el-table__cell .cell) {
      overflow: hidden;
      text-overflow: ellipsis;
      white-space: nowrap;
    }
  }
  .sample-preview-footer {
    display: flex;
    justify-content: flex-end;
    padding: 0 4px;
  }
  .raw-text-area {
    max-height: 620px;
    overflow-y: auto;
  }
  .raw-text-code {
    font-size: 12px;
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    color: var(--el-text-color-regular);
    white-space: pre-wrap;
    word-break: break-all;
    margin: 0;
    padding: 12px;
    background: var(--el-fill-color-lighter);
    border-radius: 6px;
    line-height: 1.5;
  }
  .full-preview-body {
    max-height: 75vh;
    overflow: hidden;
  }
  .full-preview-table :deep(.el-table__cell) {
    white-space: normal;
    word-break: break-word;
  }
  .bg-danger-light {
    background-color: var(--el-color-danger-light-9);
  }
  .text-danger {
    color: var(--el-color-danger);
  }

  .tag-add-btn {
    display: inline-flex;
    align-items: center;
    justify-content: center;
    min-width: 26px;
    height: 26px;
    border: 1px dashed #c0c4cc;
    border-radius: 4px;
    cursor: pointer;
    background-color: #f4f4f5;
    transition: border-color 0.2s ease;
    vertical-align: middle;
    margin-bottom: 4px;

    .tag-add-icon {
      color: #c0c4cc;
      font-size: 14px;
      transition: color 0.2s ease;
    }

    &:hover {
      border-color: var(--el-color-primary);

      .tag-add-icon {
        color: var(--el-color-primary);
      }
    }
  }

  .tag-dialog-content {
    background: var(--el-fill-color-lighter);
    border-radius: 8px;
    padding: 16px;
  }

  .tag-list-wrap {
    display: flex;
    flex-wrap: wrap;
    align-items: center;
    min-height: 32px;
  }

  .tag-item-wrap {
    position: relative;
    display: inline-block;

    .tag-delete-btn {
      position: absolute;
      top: -6px;
      right: -4px;
      width: 14px;
      height: 14px;
      background: var(--el-color-info);
      color: #fff;
      border-radius: 50%;
      display: flex;
      align-items: center;
      justify-content: center;
      font-size: 10px;
      cursor: pointer;
      z-index: 1;

      &:hover {
        background: var(--el-color-danger);
      }
    }
  }

  .tag-selected {
    outline: 2px solid var(--el-color-primary);
    outline-offset: 1px;
  }

  .tag-form {
    padding-top: 12px;
    border-top: 1px solid var(--el-border-color-lighter);
  }

  .color-picker {
    display: flex;
    gap: 8px;
  }

  .color-dot {
    width: 20px;
    height: 20px;
    border-radius: 50%;
    cursor: pointer;
    transition: all 0.2s ease;
    border: 2px solid transparent;

    &:hover {
      transform: scale(1.15);
    }

    &.active {
      border-color: var(--el-color-primary);
      box-shadow: 0 0 0 2px rgba(64, 158, 255, 0.2);
    }
  }
</style>
