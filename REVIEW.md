# 数据集管理模块深度代码审查报告

**审查时间:** 2026-05-05  
**审查深度:** Deep  
**审查文件数:** 13  
**状态:** issues_found

---

## 审查范围

本次审查覆盖了前端数据集管理相关的所有核心模块：

| 文件 | 说明 |
|------|------|
| `src/api/dataset.ts` | 数据集 API 调用模块 |
| `src/api/data-manage.ts` | 数据管理 API (Mock) |
| `src/views/data-management/index.vue` | 数据管理入口页 |
| `src/views/data-management/dataset-hub/index.vue` | 数据集中心主页面 |
| `src/views/data-management/dataset-hub/modules/dataset-upload.vue` | 上传组件 |
| `src/views/data-management/dataset-hub/modules/dataset-drawer.vue` | 数据集详情抽屉 |
| `src/views/data-management/data-processing/index.vue` | 数据处理向导页 |
| `src/views/data-management/data-processing/modules/step1-datasource.vue` | 数据源选择步骤 |
| `src/views/data-management/data-processing/modules/step2-mapping.vue` | 字段映射步骤 |
| `src/views/data-management/data-processing/modules/step3-execution.vue` | 执行监控步骤 |
| `src/mock/temp/formData.ts` | Mock 数据定义 |
| `src/hooks/core/useTable.ts` | 通用表格 Hook |
| `src/hooks/core/useWebSocketTask.ts` | WebSocket 任务 Hook |

---

## 摘要

数据集管理模块整体架构清晰，采用组合式 API 设计，UI 交互体验良好。但发现 **5 个严重问题 (Critical)**、**8 个警告 (Warning)** 和 **6 个信息性问题 (Info)**。最关键的问题是 **API 路径不一致** 和 **多处功能 Mock 未实现**，必须在上线前修复。

---

## 严重问题 (Critical)

### CR-01: API 端点路径严重不一致

**文件:** `src/api/dataset.ts`

**问题:** 多个 API 函数使用不同的 URL 前缀规则，导致后端无法正确匹配路由。

```typescript
// 第 189-191 行 - 使用 /datasets (无前缀)
export async function getDatasets() {
  const response = await request.get<DatasetListResponse>({
    url: '/datasets'  // ❌ 缺少 /api/v1 前缀
  })

// 第 210-212 行 - 使用 /dataset/:id (无前缀)
export async function deleteDataset(id: number): Promise<void> {
  return request.del({
    url: `/dataset/${id}`  // ❌ 缺少 /api/v1 前缀
  })

// 第 219-222 行 - 使用 /dataset/:id/process (无前缀)
export async function processDataset(...) {
  return request.post<ProcessResponse>({
    url: `/dataset/${datasetId}/process`,  // ❌ 缺少 /api/v1 前缀
  })
}
```

**对比:** `initiateUpload` 等其他函数正确使用了 `/api/v1/dataset/...` 前缀。

**影响:** `getDatasets`、`deleteDataset`、`processDataset` 三个核心函数会 100% 调用失败，导致列表为空、删除无效、无法发起处理任务。

**修复建议:**
```typescript
// 统一使用 /api/v1 前缀
export async function getDatasets() {
  const response = await request.get<DatasetListResponse>({
    url: '/api/v1/datasets'  // ✅ 修正
  })

export async function deleteDataset(id: number): Promise<void> {
  return request.del({
    url: `/api/v1/dataset/${id}`  // ✅ 修正
  })
}

export async function processDataset(datasetId: number, requestParams: ProcessRequest) {
  return request.post<ProcessResponse>({
    url: `/api/v1/dataset/${datasetId}/process`,  // ✅ 修正
    data: requestParams
  })
}
```

---

### CR-02: 状态值映射不一致导致 UI 显示错误

**文件:** `src/views/data-management/dataset-hub/modules/dataset-drawer.vue:95`

**问题:** 状态选项值与实际业务逻辑不匹配。

```vue
<!-- 第 92-96 行 -->
<ElSelect v-model="editForm.status" style="width: 200px">
  <ElOption label="待清洗" :value="0" />
  <ElOption label="清洗中" :value="1" />
  <ElOption label="已就绪" :value="3" />  <!-- ❌ value=3 -->
</ElSelect>
```

**对比:** `dataset-hub/index.vue` 第 404-409 行的 `getStatusConfig` 函数：

```typescript
const getStatusConfig = (status: number) => {
  if (status === 2) return { type: 'success' as const, text: '已就绪', dot: '#67C23A' }  // ✅ 期望 2
  if (status === 1) return { type: 'warning' as const, text: '清洗中', dot: '#409EFF' }
  if (status === -1) return { type: 'danger' as const, text: '异常', dot: '#F56C6C' }
  return { type: 'info' as const, text: '待清洗', dot: '#E6A23C' }
}
```

**影响:** 用户在抽屉中编辑状态时选择"已就绪"(值=3)，但列表页认为 2 才是已就绪状态，导致状态显示混乱。

**修复建议:** 统一状态值定义
```vue
<ElSelect v-model="editForm.status" style="width: 200px">
  <ElOption label="待清洗" :value="0" />
  <ElOption label="清洗中" :value="1" />
  <ElOption label="已就绪" :value="2" />  <!-- ✅ 修正为 2 -->
</ElSelect>
```

---

### CR-03: 批量删除功能仅为 Mock，无实际删除逻辑

**文件:** `src/views/data-management/dataset-hub/index.vue:867-881`

**问题:** `handleBatchDelete` 函数只显示成功消息，未调用任何删除 API。

```typescript
const handleBatchDelete = () => {
  if (selectedRows.value.length === 0) return
  ElMessageBox.confirm(
    `确定要删除选中的 ${selectedRows.value.length} 个数据集吗？删除后不可恢复。`,
    '批量删除',
    { confirmButtonText: '确定删除', cancelButtonText: '取消', type: 'warning' }
  ).then(() => {
    ElMessage.success(`已删除 ${selectedRows.value.length} 个数据集`)  // ❌ 仅提示
    selectedRows.value = []  // 仅清空选中，未调用后端
  })
}
```

**影响:** 用户执行批量删除后，数据集仍然存在于后端，造成数据一致性问题。

**修复建议:**
```typescript
const handleBatchDelete = async () => {
  if (selectedRows.value.length === 0) return
  
  try {
    await ElMessageBox.confirm(
      `确定要删除选中的 ${selectedRows.value.length} 个数据集吗？删除后不可恢复。`,
      '批量删除',
      { confirmButtonText: '确定删除', cancelButtonText: '取消', type: 'warning' }
    )
    
    // 实际调用删除 API
    await Promise.all(selectedRows.value.map(row => apiDeleteDataset(row.id)))
    
    ElMessage.success(`已删除 ${selectedRows.value.length} 个数据集`)
    selectedRows.value = []
    refreshData()  // 刷新列表
  } catch (err: any) {
    if (err !== 'cancel') {
      ElMessage.error('批量删除失败: ' + (err.message || '未知错误'))
    }
  }
}
```

---

### CR-04: 数据集保存功能未实现

**文件:** `src/views/data-management/dataset-hub/modules/dataset-drawer.vue:312-314`

**问题:** `handleSave` 函数仅为占位代码。

```typescript
const handleSave = async () => {
  ElMessage.info('更新 API 暂未上线，保存功能待后端对接后启用')  // ❌ 空实现
}
```

**影响:** 用户在数据集详情抽屉中修改名称、标签、描述后点击保存不会有任何效果。

**修复建议:** 实现实际的更新 API 调用或移除保存按钮避免误导用户。

---

### CR-05: WebSocket 连接和定时器未正确清理

**文件:** `src/views/data-management/dataset-hub/index.vue:694-763`

**问题:** WebSocket 连接和 `setTimeout` 定时器未在任务完成或组件卸载时正确清理。

```typescript
// 第 757-762 行 - setTimeout 未被清除
setTimeout(() => {
  const currentTask = uploadTasks.value.find((t) => t.id === uiTaskId)
  if (currentTask && currentTask.status === 'uploading') {
    pollTaskStatus(celTaskId, uiTaskId)
  }
}, 30000)

// ws.onclose 仅关闭连接，未清除定时器
ws.onclose = () => {
  console.log('[WS] 连接已关闭:', celTaskId)
}
```

**影响:**
1. 多个任务完成后，定时器仍在运行，可能访问已卸载的组件状态
2. WebSocket 重连定时器可能泄漏

**修复建议:**
```typescript
let pollingTimer: ReturnType<typeof setTimeout> | null = null

const handleTrackCeleryProgress = (uiTaskId: number, celTaskId: string) => {
  const wsUrl = `${import.meta.env.VITE_WS_URL || 'ws://localhost:8000'}/ws/progress`
  const ws = new WebSocket(`${wsUrl}?task_id=${celTaskId}`)

  // 清理函数
  const cleanup = () => {
    if (pollingTimer) {
      clearTimeout(pollingTimer)
      pollingTimer = null
    }
    if (ws.readyState === WebSocket.OPEN) {
      ws.close()
    }
  }

  ws.onmessage = (event) => {
    // ... 处理消息
    if (data.status === 'success' || data.status === 'failure') {
      cleanup()  // ✅ 任务结束时清理
    }
  }

  pollingTimer = setTimeout(() => {  // ✅ 保存定时器引用
    const currentTask = uploadTasks.value.find((t) => t.id === uiTaskId)
    if (currentTask && currentTask.status === 'uploading') {
      pollTaskStatus(celTaskId, uiTaskId)
    }
  }, 30000)
}
```

---

## 警告 (Warning)

### WR-01: 暂停/恢复上传功能仅修改 UI 状态，未实现实际逻辑

**文件:** `src/views/data-management/dataset-hub/index.vue:796-853`

**问题:** `pauseTask` 和 `resumeTask` 函数只修改了本地任务状态，未调用后端暂停接口或中断上传请求。

```typescript
const pauseTask = (task: UploadTaskItem) => {
  task.status = 'paused'  // ❌ 仅修改状态，未暂停实际上传
  // ...
}

const resumeTask = (task: UploadTaskItem) => {
  // ...
  if (task.status === 'error' && task.file) {
    // 重新发起上传，但原始的上传请求可能仍在后台运行
    uploadDataset(task.file, (percent, phase) => { /* ... */ })
  }
}
```

**建议:** 需要后端支持暂停/恢复接口，或使用 `AbortController` 中断上传请求。

---

### WR-02: 多处空实现的函数

| 文件 | 行号 | 函数 | 问题 |
|------|------|------|------|
| `step1-datasource.vue` | 159 | `handleSearch` | 搜索功能无实际逻辑 |
| `data-processing/index.vue` | 147 | `handleRefreshSamples` | 空函数 |
| `data-processing/index.vue` | 138-141 | `handleTempUpload` | 仅提示，功能未实现 |

**建议:** 实现实际功能或移除相关 UI 元素。

---

### WR-03: 类型安全问题

**文件:** `dataset-hub/index.vue:668,829`

**问题:** 使用 `any` 类型绕过 TypeScript 类型检查。

```typescript
// 第 668 行
.then((response: any) => {  // ❌ any 类型
  const celTaskId = response?.task_id

// 第 829 行
.then((response: any) => {  // ❌ any 类型
  const celTaskId = response?.task_id
```

**建议:** 使用正确的响应类型 `UploadCompleteResponse`。

---

### WR-04: getTaskStatus 函数始终返回 rejected Promise

**文件:** `src/api/dataset.ts:225-227`

```typescript
export async function getTaskStatus(taskId: string): Promise<TaskStatusResponse> {
  return Promise.reject(new Error('Task status is provided via WebSocket, not HTTP polling'))
}
```

**问题:** 该函数从未被调用，且返回始终失败的 Promise，可能被误用导致未捕获的 Promise  rejection。

**建议:** 如果确认不需要该函数，应删除；如果需要，应实现 HTTP 轮询版本。

---

### WR-05: 硬编码的 WebSocket URL Fallback

**文件:** `dataset-hub/index.vue:695`

```typescript
const wsUrl = `${import.meta.env.VITE_WS_URL || 'ws://localhost:8000'}/ws/progress`
```

**问题:** 开发环境 fallback 不应在生产代码中硬编码，可能导致生产环境连接到错误的 WebSocket 服务器。

**建议:** 仅在 `.env.development` 中设置默认值，或在连接失败时提示用户配置。

---

### WR-06: Mock 数据与真实数据接口混用

**文件:** `src/views/data-management/data-processing/index.vue`

**问题:** 页面导入 `DatasetItem` 类型来自 mock 文件，但这是用于开发阶段的 mock 类型。

```typescript
import type { DatasetItem } from '@/mock/temp/formData'
```

**影响:** 后端 API 就绪后需要大量重构接口。

**建议:** 在 `src/types/api/` 中定义真实的 `DatasetItem` 类型，从 mock 文件中导出用于开发。

---

### WR-07: handleInputSelect 中 __NONE__ 魔法值

**文件:** `src/views/data-management/data-processing/modules/step2-mapping.vue:457-459`

```typescript
function handleInputSelect(value: string) {
  updateField('input', value || '')  // 当 value 为 '__NONE__' 时会怎样？
}
```

**问题:** 第 73 行使用 `__NONE__` 作为"无"的选项值，但在 `handleInputSelect` 和 `handleSubmitTask` 中处理不一致。

```typescript
// 第 73 行
<ElOption label="无" value="__NONE__" />

// 第 165-167 行 - data-processing/index.vue
if (configToSend.fieldMapping.input === '__NONE__') {
  configToSend.fieldMapping.input = ''
}
```

**建议:** 定义常量 `const NONE_FIELD_VALUE = '__NONE__'` 统一使用。

---

### WR-08: 表格筛选后端/前端职责不清

**文件:** `src/views/data-management/dataset-hub/index.vue:588`

```typescript
transform: {
  dataTransformer: (records: Dataset[]) => applyLocalFilters(records)  // 前端过滤
}
```

**问题:** `applyLocalFilters` 在前端过滤数据，但后端 API 可能支持服务端分页和筛选。混合使用会导致分页错误（只显示过滤后的第一页，而非全部）。

**建议:** 明确分工：搜索参数 → 后端 API → 后端返回分页数据 → 前端仅用于展示缓存。

---

## 信息 (Info)

### IN-01: 代码重复 - formatSize 函数

| 文件 | 行号 |
|------|------|
| `dataset-hub/index.vue` | 451-454 |
| `dataset-drawer.vue` | 268-271 |
| `step1-datasource.vue` | 170-173 |
| `step2-mapping.vue` | 488-491 |

**建议:** 提取到 `src/utils/format.ts` 公共模块。

---

### IN-02: 魔数 (Magic Numbers)

| 位置 | 值 | 说明 |
|------|-----|------|
| `dataset.ts:90` | `5 * 1024 * 1024` | 分块大小 5MB |
| `dataset.ts:170` | `batchSize = 3` | 并发上传数 |
| `dataset-hub/index.vue:281` | `margin-right: 200px` | 硬编码样式值 |
| `step2-mapping.vue:699` | `margin-right: 40px` | 硬编码样式值 |

**建议:** 使用命名常量替代。

---

### IN-03: UploadTaskItem.id 使用 Date.now() 可能冲突

**文件:** `dataset-hub/index.vue:636`

```typescript
const task: UploadTaskItem = {
  id: Date.now(),  // ⚠️ 如果快速连续上传两个文件，ID 会相同
```

**建议:** 使用自增 ID 或 `crypto.randomUUID()`。

---

### IN-04: WebSocket 重连逻辑与任务进度追踪混用

**文件:** `useWebSocketTask.ts` 与 `dataset-hub/index.vue` 有重复的 WebSocket 连接管理逻辑。

**建议:** 统一使用 `useWebSocketTask` Hook 或抽取公共 WebSocket 管理逻辑。

---

### IN-05: Mock API 与真实 API 路径混用

**文件:** `data-manage.ts`

```typescript
// 第 7 行 - 真实 API 路径
url: '/api/dataset/list'
// 第 22 行 - 真实 API 路径
url: `/api/dataset/delete/${id}`
```

**问题:** 这些路径与 `dataset.ts` 中的路径不一致。

**建议:** 统一使用 `dataset.ts` 中定义的 API 函数，删除 `data-manage.ts` 中的重复实现。

---

### IN-06: 抽屉关闭时未保存编辑状态

**文件:** `dataset-drawer.vue:283-285`

```typescript
const handleBeforeClose = () => {
  drawerVisible.value = false  // ❌ 直接关闭，未提示保存
}
```

**建议:** 增加"是否保存修改"确认对话框。

---

## UI/UX 一致性问题

| 问题 | 位置 | 说明 |
|------|------|------|
| 状态筛选选项不一致 | `dataset-hub/index.vue:269-273` vs `step1-datasource.vue:22-25` | 前者用 `ready/processing/pending/error`，后者用 `ready/processing` |
| 标签选择 UI 不一致 | `dataset-drawer.vue` vs `step2-mapping.vue` | 标签编辑交互不同 |
| 格式化函数显示不一致 | 多处 | 大小显示有的用 MB/GB，有的用数值 |

---

## 潜在 Bug

1. **并发上传冲突:** 快速点击上传按钮可能创建相同 ID 的任务
2. **状态同步问题:** WebSocket 推送状态与轮询状态可能冲突
3. **组件卸载时 WebSocket 未断开:** 可能访问已卸载组件的响应式状态

---

## 修复优先级建议

### P0 (必须修复，上线前)
1. CR-01: API 端点路径不一致
2. CR-03: 批量删除无实际逻辑
3. CR-04: 保存功能未实现

### P1 (强烈建议修复)
4. CR-02: 状态值映射不一致
5. CR-05: WebSocket 和定时器泄漏
6. WR-01: 暂停/恢复功能未实现
7. WR-08: 前后端筛选职责不清

### P2 (建议优化)
8. WR-02: 空实现函数
9. WR-03: 类型安全
10. IN-01: 代码重复

---

## 总体评价

| 维度 | 评分 | 说明 |
|------|------|------|
| 功能完整性 | 6/10 | 核心功能框架完整，但多处为 Mock 或空实现 |
| 代码质量 | 7/10 | 结构清晰，命名规范，但存在类型安全和重复代码 |
| 错误处理 | 6/10 | 有基本的错误处理，但不一致，且缺少边界情况处理 |
| UI/UX | 8/10 | 界面美观，交互流畅，状态反馈良好 |
| 可维护性 | 7/10 | 组件拆分合理，但类型定义分散，API 边界不清 |

**综合评分: 6.8/10**

数据集管理模块有良好的架构基础和 UI 设计，但在实际功能实现和代码健壮性方面仍有较大提升空间。建议在正式上线前修复所有 P0 和 P1 问题。

---

_审查完成时间: 2026-05-05_  
_审查工具: GSD Code Review Agent_
