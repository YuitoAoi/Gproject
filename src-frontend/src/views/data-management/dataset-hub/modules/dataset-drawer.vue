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
      <!-- Tab 1: 数据集信息（元数据 + 数据血缘） -->
      <ElTabPane label="数据集信息" name="meta">
        <div class="p-2">
          <div class="metadata-grid">
            <div class="meta-item">
              <span class="meta-label">数据集名称</span>
              <span class="meta-value">{{ dataset?.name }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">文件格式</span>
              <ElTag size="small" :type="formatTagType">{{ dataset?.format }}</ElTag>
            </div>
            <div class="meta-item">
              <span class="meta-label">文件大小</span>
              <span class="meta-value">{{ formatSize(dataset?.size || 0) }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">记录总数</span>
              <span class="meta-value">{{ formatRecords(dataset?.records || 0) }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">存储路径</span>
              <span class="meta-value text-xs font-mono">{{ dataset?.storagePath }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">创建者</span>
              <span class="meta-value">{{ dataset?.creator }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">上传时间</span>
              <span class="meta-value">{{ dataset?.uploadTime }}</span>
            </div>
            <div class="meta-item">
              <span class="meta-label">最后修改</span>
              <span class="meta-value">{{ dataset?.updateTime }}</span>
            </div>
          </div>

          <!-- 数据血缘（放在数据集信息下方） -->
          <div class="mt-6 pt-5 border-t border-g-100">
            <h4 class="text-sm font-medium text-g-700 mb-4">数据血缘</h4>
            <template v-if="dataset?.lineage">
              <div class="lineage-flow">
                <div class="lineage-node">
                  <div class="node-icon bg-amber-100">
                    <span class="ri:database-2-line text-amber-600"></span>
                  </div>
                  <div class="node-content">
                    <div class="text-sm font-medium">{{ dataset.lineage.sourceName }}</div>
                    <div class="text-xs text-g-400">原始数据源</div>
                  </div>
                </div>
                <div class="lineage-arrow">
                  <div class="arrow-line"></div>
                  <div class="arrow-rules">
                    <ElTag
                      v-for="rule in dataset.lineage.rules"
                      :key="rule"
                      size="small"
                      type="info"
                      effect="plain"
                      class="mr-1"
                    >
                      {{ rule }}
                    </ElTag>
                  </div>
                  <div class="arrow-line"></div>
                </div>
                <div class="lineage-node">
                  <div class="node-icon bg-primary-light">
                    <span class="ri:file-text-line text-primary"></span>
                  </div>
                  <div class="node-content">
                    <div class="text-sm font-medium">{{ dataset.name }}</div>
                    <div class="text-xs text-g-400">当前数据集</div>
                  </div>
                </div>
              </div>
            </template>
            <template v-else>
              <div class="text-center py-6 text-g-400">
                <span class="ri:git-branch-line text-3xl block mb-2"></span>
                <p class="text-sm">该数据集无血缘关系</p>
                <p class="text-xs mt-1">直接导入的原始数据集不会有衍生链路</p>
              </div>
            </template>
          </div>
        </div>
      </ElTabPane>

      <!-- Tab 2: 编辑数据集 -->
      <ElTabPane label="编辑数据集" name="edit">
        <div class="p-2">
          <ElForm label-width="80px" label-position="top">
            <ElFormItem label="数据集名称">
              <ElInput :model-value="dataset?.name" placeholder="数据集名称" />
            </ElFormItem>
            <ElFormItem label="标签">
              <div class="tag-editor">
                <ElTag
                  v-for="tag in dataset?.tags || []"
                  :key="tag.label"
                  closable
                  size="default"
                  :color="tag.color"
                  class="mr-1 mb-1"
                  effect="dark"
                >
                  {{ tag.label }}
                </ElTag>
                <span class="tag-add-btn" @click="tagDialogVisible = true">
                  <ArtSvgIcon icon="ri:add-line" class="tag-add-icon" />
                </span>
              </div>
            </ElFormItem>
            <ElFormItem label="状态">
              <ElSelect :model-value="dataset?.status" style="width: 200px">
                <ElOption label="已就绪" value="ready" />
                <ElOption label="处理中" value="processing" />
                <ElOption label="已禁用" value="disabled" />
                <ElOption label="异常" value="error" />
              </ElSelect>
            </ElFormItem>
            <ElFormItem label="描述">
              <ElInput
                :model-value="dataset?.description"
                type="textarea"
                :rows="3"
                placeholder="数据集描述"
              />
            </ElFormItem>
            <ElFormItem>
              <ElButton type="primary">保存修改</ElButton>
              <ElButton class="ml-2">重置</ElButton>
            </ElFormItem>
          </ElForm>
        </div>
      </ElTabPane>

      <!-- Tab 3: 数据预览 -->
      <ElTabPane label="数据预览" name="samples">
        <div class="p-2">
          <div class="text-xs text-g-400 mb-3">前 20 条数据预览</div>
          <div class="sample-list">
            <div
              v-for="(sample, idx) in (dataset?.samples || [])"
              :key="idx"
              class="sample-item"
            >
              <div class="sample-index">{{ idx + 1 }}</div>
              <pre class="sample-content">{{ sample }}</pre>
            </div>
          </div>
        </div>
      </ElTabPane>

      <!-- Tab 4: 操作日志 -->
      <ElTabPane label="操作日志" name="logs">
        <div class="p-2">
          <ElTimeline>
            <ElTimelineItem
              v-for="(log, idx) in dataset?.logs || []"
              :key="idx"
              :timestamp="log.time"
              placement="top"
              size="normal"
            >
              <div class="text-sm font-medium">{{ log.action }}</div>
              <div class="text-xs text-g-500 mt-1">{{ log.detail }}</div>
            </ElTimelineItem>
          </ElTimeline>
        </div>
      </ElTabPane>
    </ElTabs>

    <!-- 底部操作按钮 -->
    <template #footer>
      <div class="flex justify-end gap-3">
        <ElButton>
          <span class="ri:download-2-line mr-1"></span>下载文件
        </ElButton>
        <ElButton type="primary">
          <span class="ri:brush-line mr-1"></span>去清洗
        </ElButton>
      </div>
    </template>

    <!-- 新建标签弹窗 -->
    <ElDialog v-model="tagDialogVisible" title="新建标签" width="420px" :close-on-click-modal="false">
      <div class="tag-dialog-content">
        <div class="mb-4">
          <div class="text-sm text-g-500 mb-3">已有标签</div>
          <div class="tag-list-wrap">
            <ElTag
              v-for="tag in allTags"
              :key="tag.label"
              size="small"
              :color="tag.color"
              effect="dark"
              class="mr-1 mb-1 cursor-pointer"
              :class="{ 'tag-selected': newTagForm.label === tag.label }"
              @click="selectExistingTag(tag)"
            >
              {{ tag.label }}
            </ElTag>
            <span v-if="allTags.length === 0" class="text-xs text-g-400">暂无可用标签</span>
          </div>
        </div>
        <div class="tag-form">
          <div class="text-sm text-g-500 mb-3">新建标签</div>
          <ElInput v-model="newTagForm.label" placeholder="请输入标签名称" class="mb-3" />
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
              {{ newTagForm.label || '标签预览' }}
            </ElTag>
          </div>
        </div>
      </div>
      <template #footer>
        <ElButton @click="tagDialogVisible = false">取消</ElButton>
        <ElButton type="primary" @click="handleAddTag">确定</ElButton>
      </template>
    </ElDialog>
  </ElDrawer>
</template>

<script setup lang="ts">
  import type { DatasetItem } from '@/mock/temp/formData'
  import { DATASET_TABLE_DATA } from '@/mock/temp/formData'
  import ArtSvgIcon from '@/components/core/base/art-svg-icon/index.vue'

  interface Props {
    visible: boolean
    dataset: DatasetItem | null
  }

  interface Emits {
    (e: 'update:visible', value: boolean): void
    (e: 'add-tag', tag: { label: string; color: string }): void
  }

  const props = defineProps<Props>()
  const emit = defineEmits<Emits>()

  const activeTab = ref('meta')

  const drawerVisible = computed({
    get: () => props.visible,
    set: (value) => emit('update:visible', value)
  })

  const drawerTitle = computed(() => props.dataset?.name || '数据集详情')

  const formatTagType = computed(() => {
    const fmt = props.dataset?.format
    if (fmt === 'JSON') return 'primary' as const
    if (fmt === 'CSV') return 'warning' as const
    if (fmt === 'TXT') return 'info' as const
    return 'info' as const
  })

  const formatSize = (size: number): string => {
    if (size >= 1024) return `${(size / 1024).toFixed(2)} GB`
    return `${size.toFixed(1)} MB`
  }

  const formatRecords = (records: number): string => {
    if (records >= 10000) return `${(records / 10000).toFixed(1)} 万`
    return records.toLocaleString()
  }

  const handleBeforeClose = () => {
    drawerVisible.value = false
  }

  const setActiveTab = (tab: string) => {
    activeTab.value = tab
  }

  // 标签弹窗
  const tagDialogVisible = ref(false)
  const colorPresets = ['#67C23A', '#409EFF', '#E6A23C', '#F56C6C', '#909399', '#1D84FF', '#5D87FF']
  const newTagForm = reactive({
    label: '',
    color: '#67C23A'
  })

  const allTags = computed(() => {
    const existing = DATASET_TABLE_DATA.flatMap((d) => d.tags || [])
    return existing.filter((tag, idx, arr) => arr.findIndex((t) => t.label === tag.label) === idx)
  })

  const selectExistingTag = (tag: { label: string; color: string }) => {
    newTagForm.label = tag.label
    newTagForm.color = tag.color
  }

  const handleAddTag = () => {
    if (!newTagForm.label.trim()) return
    emit('add-tag', { label: newTagForm.label, color: newTagForm.color })
    newTagForm.label = ''
    newTagForm.color = '#67C23A'
    tagDialogVisible.value = false
  }

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
  .lineage-flow {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 8px;
    padding: 24px 0;
  }
  .lineage-node {
    display: flex;
    align-items: center;
    gap: 12px;
    background: var(--el-fill-color-light);
    border-radius: 8px;
    padding: 12px 20px;
    width: 100%;
    max-width: 360px;
  }
  .node-icon {
    width: 40px;
    height: 40px;
    border-radius: 8px;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 20px;
    flex-shrink: 0;
  }
  .bg-primary-light {
    background: rgba(var(--el-color-primary-rgb), 0.1);
  }
  .lineage-arrow {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 6px;
  }
  .arrow-line {
    width: 2px;
    height: 16px;
    background: var(--el-border-color);
  }
  .arrow-rules {
    display: flex;
    flex-wrap: wrap;
    gap: 4px;
    justify-content: center;
  }
  .sample-list {
    display: flex;
    flex-direction: column;
    gap: 8px;
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

  // 新建标签按钮
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

  // 标签弹窗内容区
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

  // 颜色选择器
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
