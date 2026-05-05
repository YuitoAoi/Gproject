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
              <ElTag size="small" :type="formatTagType">{{ dataset?.meta?.format?.toUpperCase() }}</ElTag>
            </div>
            <div class="meta-item">
              <span class="meta-label">文件大小</span>
              <span class="meta-value">{{ formatSize(dataset?.meta?.file_size || 0) }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">存储路径</span>
              <span class="meta-value text-xs font-mono">{{ dataset?.meta?.file_path }}</span>
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
            <ElFormItem label="状态">
              <ElSelect v-model="editForm.status" style="width: 200px">
                <ElOption label="待清洗" :value="0" />
                <ElOption label="清洗中" :value="1" />
                <ElOption label="已就绪" :value="3" />
              </ElSelect>
            </ElFormItem>
            <ElFormItem label="描述">
              <ElInput
                v-model="editForm.desc"
                type="textarea"
                :rows="3"
                placeholder="数据集描述"
              />
            </ElFormItem>
            <ElFormItem>
              <ElButton type="primary" :loading="saveLoading" @click="handleSave">保存修改</ElButton>
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
          <div v-else-if="samples.length === 0" class="text-center py-10 text-g-400">
            <span class="ri:file-list-3-line text-3xl block mb-2"></span>
            <p class="text-sm">暂无预览数据</p>
          </div>
          <div v-else class="sample-list">
            <div
              v-for="(sample, idx) in samples"
              :key="idx"
              class="sample-item"
            >
              <div class="sample-index">{{ idx + 1 }}</div>
              <pre class="sample-content">{{ JSON.stringify(sample, null, 2) }}</pre>
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

    <ElDialog v-model="tagDialogVisible" title="编辑标签" width="420px" :close-on-click-modal="false">
      <div class="tag-dialog-content">
        <div class="mb-4">
          <div class="text-sm text-g-500 mb-3">已有标签（点击选择）</div>
          <div class="tag-list-wrap">
            <ElTag
              v-for="tag in allTags"
              :key="tag.tag_id"
              size="small"
              :style="{ backgroundColor: tag.tag_color, borderColor: tag.tag_color }"
              effect="dark"
              class="mr-1 mb-1 cursor-pointer"
              :class="{ 'tag-selected': newTagForm.tag_id === tag.tag_id }"
              @click="selectExistingTag(tag)"
            >
              {{ tag.tag_name }}
            </ElTag>
            <span v-if="allTags.length === 0" class="text-xs text-g-400">暂无可用标签</span>
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
  </ElDrawer>
</template>

<script setup lang="ts">
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'
  import { useRouter } from 'vue-router'
  import { ElMessage } from 'element-plus'
  import {
    getTags,
    createTag,
    getDatasetSample,
    requestDownloadToken,
    type Dataset,
    type TagInfo
  } from '@/api/dataset'

  interface Props {
    visible: boolean
    dataset: Dataset | null
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
    status: 0,
    tag_ids: [] as number[]
  })

  const allTags = ref<TagInfo[]>([])
  const samples = ref<Record<string, any>[]>([])
  const sampleLoading = ref(false)
  const saveLoading = ref(false)
  const tagLoading = ref(false)

  const formatTagType = computed(() => {
    const fmt = props.dataset?.meta?.format
    if (fmt === 'json') return 'primary' as const
    if (fmt === 'csv') return 'warning' as const
    return 'info' as const
  })

  const statusText = computed(() => {
    if (props.dataset?.status === 3) return '已就绪'
    if (props.dataset?.status === 1 || props.dataset?.status === 2) return '清洗中'
    return '待清洗'
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
    return date.toLocaleDateString('zh-CN', { year: 'numeric', month: '2-digit', day: '2-digit' })
  }

  const resolvedTags = computed(() => {
    return allTags.value.filter((t) => (editForm.tag_ids || []).includes(t.tag_id))
  })

  const handleBeforeClose = () => {
    drawerVisible.value = false
  }

  const setActiveTab = (tab: string) => {
    activeTab.value = tab
    if (tab === 'samples' && props.dataset?.id) {
      loadSamples(props.dataset.id)
    }
  }

  const loadSamples = async (datasetId: number) => {
    sampleLoading.value = true
    samples.value = []
    const res = await getDatasetSample(datasetId)
    if (res.samples.length > 0) {
      samples.value = res.samples
    }
    sampleLoading.value = false
  }

  const handleReset = () => {
    if (!props.dataset) return
    editForm.name = props.dataset.name || ''
    editForm.desc = props.dataset.desc || ''
    editForm.status = props.dataset.status
    editForm.tag_ids = [...(props.dataset.tag_ids || [])]
  }

  const handleSave = async () => {
    ElMessage.info('更新 API 暂未上线，保存功能待后端对接后启用')
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
    router.push({ path: '/data-management/data-processing', query: { datasetId: String(props.dataset.id) } })
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
    const res = await createTag(newTagForm.name, newTagForm.color)
    tagLoading.value = false
    if (res.success) {
      ElMessage.success('标签创建成功')
      const tagRes = await getTags()
      if (tagRes.success) {
        allTags.value = tagRes.tags
        const created = tagRes.tags.find((t) => t.tag_name === newTagForm.name)
        if (created && !editForm.tag_ids.includes(created.tag_id)) {
          editForm.tag_ids.push(created.tag_id)
        }
      }
      tagDialogVisible.value = false
      newTagForm.tag_id = null
      newTagForm.name = ''
      newTagForm.color = '#67C23A'
    } else {
      ElMessage.error(res.error || '创建标签失败')
    }
  }

  onMounted(async () => {
    const tagRes = await getTags()
    if (tagRes.success) {
      allTags.value = tagRes.tags
    }
    handleReset()
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
  .sample-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
    max-height: 400px;
    overflow-y: auto;
  }
  .sample-item {
    display: flex;
    gap: 10px;
    background: var(--el-fill-color-lighter);
    border-radius: 6px;
    padding: 8px 12px;
  }
  .sample-index {
    font-size: 12px;
    color: var(--el-text-color-placeholder);
    min-width: 20px;
    flex-shrink: 0;
    padding-top: 2px;
  }
  .sample-content {
    font-size: 12px;
    font-family: 'JetBrains Mono', 'Fira Code', monospace;
    color: var(--el-text-color-regular);
    white-space: pre-wrap;
    word-break: break-all;
    margin: 0;
    line-height: 1.5;
    flex: 1;
    overflow-x: auto;
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
