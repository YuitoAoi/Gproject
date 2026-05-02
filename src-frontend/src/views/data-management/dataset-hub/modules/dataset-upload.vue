<template>
  <ElDialog
    v-model="dialogVisible"
    title="导入数据集"
    width="560px"
    align-center
    destroy-on-close
    :close-on-click-modal="false"
  >
    <div class="upload-dialog-body">
      <div class="upload-area-container">
        <ElUpload
          ref="uploadRef"
          class="upload-area"
          drag
          :auto-upload="false"
          :limit="1"
          :on-exceed="handleExceed"
          :on-change="handleFileChange"
          :on-remove="handleFileRemove"
          accept=".csv,.xlsx,.json"
        >
          <div class="flex-c flex-col py-6">
            <span class="ri:upload-cloud-2-line text-5xl text-g-300 mb-4"></span>
            <div class="text-sm text-g-600 mb-1">将文件拖拽到此处，或 <em class="text-primary not-italic cursor-pointer">点击浏览本地文件</em></div>
            <div class="text-xs text-g-400 mt-3">支持 .csv, .xlsx, .json 格式。单文件最大限制 100MB</div>
          </div>
        </ElUpload>

        <div v-if="selectedFile" class="selected-file-info">
          <el-icon class="text-xl text-primary"><document /></el-icon>
          <span class="filename">{{ selectedFile.name }}</span>
          <span class="filesize">{{ formatSize(selectedFile.size || 0) }}</span>
        </div>
      </div>
    </div>
    <template #footer>
      <div class="dialog-footer">
        <ElButton @click="handleCancel">取消</ElButton>
        <ElButton type="primary" :disabled="!selectedFile" @click="handleUpload">
          开始上传
        </ElButton>
      </div>
    </template>
  </ElDialog>
</template>

<script setup lang="ts">
  import { ElMessage } from 'element-plus'
  import { Document } from '@element-plus/icons-vue'
  import type { UploadFile } from 'element-plus'

  interface Props {
    visible: boolean
  }

  interface Emits {
    (e: 'update:visible', value: boolean): void
    (e: 'upload-start', file: { name: string; size: number; raw: File }): void
  }

  const props = defineProps<Props>()
  const emit = defineEmits<Emits>()

  const uploadRef = ref()
  const selectedFile = ref<UploadFile | null>(null)

  const dialogVisible = computed({
    get: () => props.visible,
    set: (value) => emit('update:visible', value)
  })

  const formatSize = (bytes: number): string => {
    if (bytes < 1024) return bytes + ' B'
    if (bytes < 1024 * 1024) return (bytes / 1024).toFixed(1) + ' KB'
    return (bytes / (1024 * 1024)).toFixed(1) + ' MB'
  }

  const handleFileChange = (file: any, _files: any[]) => {
    const ext = file.name.split('.').pop()?.toLowerCase()
    if (!['csv', 'xlsx', 'json'].includes(ext || '')) {
      ElMessage.error('仅支持 CSV、XLSX、JSON 格式文件')
      uploadRef.value?.clearFiles()
      return
    }
    if (file.size > 100 * 1024 * 1024) {
      ElMessage.error('文件大小不能超过 100MB')
      uploadRef.value?.clearFiles()
      return
    }
    selectedFile.value = file
  }

  const handleFileRemove = () => {
    selectedFile.value = null
  }

  const handleExceed = () => {
    ElMessage.warning('最多只能上传一个文件，请先移除已选文件')
  }

  const handleCancel = () => {
    dialogVisible.value = false
    resetState()
  }

  const resetState = () => {
    selectedFile.value = null
    uploadRef.value?.clearFiles()
  }

const handleUpload = () => {
    if (!selectedFile.value) return

    const file = selectedFile.value
    const fileRaw = file.raw as File

    if (!fileRaw) {
      ElMessage.error('无法读取文件内容')
      return
    }

    // 立即关闭弹窗，将文件信息传递给父组件进行后台上传
    dialogVisible.value = false
    emit('upload-start', {
      name: file.name,
      size: file.size || 0,
      raw: fileRaw
    })

    // 重置状态
    resetState()
  }
</script>

<style scoped>
  .upload-dialog-body {
    padding: 8px 0;
    min-height: 200px;
  }

  .upload-area-container {
    display: flex;
    flex-direction: column;
    gap: 16px;
  }

  .upload-area :deep(.el-upload-dragger) {
    border: 2px dashed var(--el-border-color);
    border-radius: 8px;
    transition: border-color 0.3s;
    background: var(--el-fill-color-lighter);
  }

  .upload-area :deep(.el-upload-dragger:hover) {
    border-color: var(--el-color-primary);
  }

  .selected-file-info {
    display: flex;
    align-items: center;
    gap: 8px;
    padding: 12px;
    background: var(--el-fill-color-lighter);
    border-radius: 8px;
  }

  .selected-file-info .filename {
    font-weight: 500;
    color: var(--el-text-color-regular);
  }

  .selected-file-info .filesize {
    color: var(--el-text-color-secondary);
    font-size: 12px;
  }

  .upload-progress-container {
    padding: 16px;
  }

  .progress-header {
    display: flex;
    justify-content: space-between;
    margin-bottom: 12px;
  }

  .progress-phases {
    display: flex;
    justify-content: space-between;
    margin-top: 16px;
    padding: 0 8px;
  }

  .phase-item {
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 4px;
  }

  .phase-icon {
    font-size: 16px;
  }

  .phase-label {
    font-size: 11px;
    color: var(--el-text-color-secondary);
  }

  .phase-active .phase-label {
    color: var(--el-color-primary);
  }

  .phase-done .phase-label {
    color: var(--el-color-success);
  }

  .upload-result {
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 40px 0;
    gap: 8px;
  }

  .result-icon {
    margin-bottom: 8px;
  }

  .result-text {
    font-size: 16px;
    font-weight: 500;
  }

  .current-file-name {
    text-align: center;
    overflow: hidden;
    text-overflow: ellipsis;
    white-space: nowrap;
  }

  @keyframes spin {
    from { transform: rotate(0deg); }
    to { transform: rotate(360deg); }
  }

  .animate-spin {
    animation: spin 1s linear infinite;
  }
</style>