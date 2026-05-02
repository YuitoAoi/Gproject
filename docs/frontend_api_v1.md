## 1. dataset.ts — 数据集核心 API（混用 axios + request）  

| 函数 | 方法 | 端点 | 请求示例 | 响应 |
|------|------|------|----------|------|
| initiateUpload | GET | /api/v1/datasets/initiate-upload | ?filename=test.json&file_size=1991&file_format=json | { upload_id, chunk_size, total_chunks } |
| uploadChunk | POST | /api/v1/datasets/upload-chunk | ?upload_id=xxx&chunk_number=0 + FormData{ file: Blob } | { upload_id, chunk_number, received, message } |
| completeUpload | POST | /api/v1/datasets/complete-upload | ?upload_id=xxx&filename=test.json&file_format=json&file_size=1991 | { upload_id, task_id, dataset_id, status, message } |
| uploadDataset | 组合 | 调用上面三个 | uploadDataset(file, onProgress) — 自动分块上传 | 同上 |
| getDatasets | GET | /api/v1/datasets | ?skip=0&limit=100 | Dataset[] — 返回 { records, current, size, total } |
| getDataset | GET | /api/v1/datasets/:id | — | Dataset 对象 |
| deleteDataset | DELETE | /api/v1/datasets/:id | — | void |
| processDataset | POST | /api/v1/datasets/:id/process | { process_type, convert_format?, remove_duplicates?, fill_missing?, missing_strategy? } | { task_id, status, message } |
| getTaskStatus | GET | /api/v1/datasets/tasks/:taskId | — | { task_id, status, result?, error? } |

// Dataset 实体
interface Dataset {
  id: number; name: string; description: string | null
  file_path: string; file_size: number; format: string
  total_records: number; status: 'pending'|'processing'|'converting'|'ready'|'error'
  created_at: string; updated_at: string
}

---

## 2. auth.ts — 认证 API

| 函数 | 方法 | 端点 | 请求示例 | 响应 |
|------|------|------|----------|------|
| fetchLogin | POST | /auth/login | { userName, password } | { userId, userName, token, refreshToken } |
| fetchGetUserInfo | GET | /user/info | — | { userId, userName, email, roles, buttons, avatar } |

---

## 3. data-manage.ts — 模拟数据管理（全部 Mock + 3条失效真实API）

| 函数 | 真实/Mock | 端点 |
|------|-----------|------|
| fetchGetDatasetList | 真实（但 /api/dataset/list 路径错误） | GET /api/dataset/list |
| fetchGetDatasetDetail | 真实（路径错误） | GET /api/dataset/detail/:id |
| fetchDeleteDataset | 真实（路径错误） | DELETE /api/dataset/delete/:id |
| fetchGetDatasetListMock | Mock（300ms延迟） | — |
| fetchGetCleaningSamplesMock | Mock（200ms） | — |
| fetchRefreshCleaningSamplesMock | Mock（150ms） | — |
| fetchSubmitCleaningTaskMock | Mock（500ms） | — |
| fetchGetProcessingTaskMock | Mock（200ms） | — |
| fetchGetProcessingLogsMock | Mock（300ms） | — |
| fetchGetDefaultCleaningConfigMock | Mock（100ms） | — |

> 问题: 三个"真实"API (fetchGetDatasetList/Detail/Delete) 路径为 /api/dataset/** 而非 /api/v1/datasets/**，与后端路由不匹配。

---

## 4. system-manage.ts — 系统管理 API

| 函数 | 方法 | 端点 | 请求 |
|------|------|------|------|
| fetchGetUserList | GET | /api/user/list | params: UserSearchParams |
| fetchGetRoleList | GET | /api/role/list | params: RoleSearchParams |
| fetchGetMenuList | GET | /api/v3/system/menus | — |

---

## 5. utils/http/index.ts — HTTP 客户端封装

// 两种调用方式在代码中共存：
// 方式A — axios 直调（dataset.ts 第1行导入）
axios.get('/api/v1/datasets', { params: { skip, limit } })
// 方式B — request 封装（自动 Token 注入 + 错误处理）
request.get<Dataset>({ url: `/datasets/${id}` })
request.post<ProcessResponse>({ url: `/datasets/${id}/process`, data: body })
request.del({ url: `/datasets/${id}` })

关键行为:
- baseURL: VITE_API_URL（Vite 环境变量）
- timeout: 15s；MAX_RETRIES: 0（不重试）
- POST/PUT 自动转换: 当只传 params 不给 data 时，params 自动转为 POST body
- 请求拦截器: 自动注入 Authorization header（从 useUserStore().accessToken）
- 响应拦截器: code === 200 放行；401 自动登出（3秒防抖）
- 返回值: res.data.data（自动解包 BaseResponse<T> 的 data 字段）