# GProject API v1

**Base URL**: `/api/v1`

所有认证端点需携带 `Authorization: Bearer <access_token>`。

---

## 通用约定

| 状态码 | 含义 |
|--------|------|
| `200` | 成功 |
| `201` | 创建成功 |
| `400` | 请求参数校验失败 / 业务规则冲突 |
| `401` | 未认证（token 缺失/无效/过期） |
| `404` | 资源不存在或无权访问（统一不泄露存在性） |

成功和失败响应均包含 `success: bool` 字段，失败时附带 `error: string`。

---

## 认证

### `POST /auth/login`

登录获取 token。无需认证。

**请求体** (`application/json`):

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `email` | `string` | 是 | 邮箱 |
| `password` | `string` | 是 | 密码 |
| `login_ip` | `string` | 否 | 登录 IP |

**响应** `200`:

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | `bool` | 是否成功 |
| `user_id` | `int` | 用户 ID |
| `access_token` | `string` | 访问令牌 |
| `refresh_token` | `string` | 刷新令牌 |
| `expires_in` | `int` | 过期时间（秒） |
| `error` | `string` | 错误信息 |

**错误**: `401` — 邮箱或密码错误。

---

## 用户

### `POST /user`

注册新用户。无需认证。

**请求体** (`application/json`):

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | `string` | 是 | 用户名 |
| `email` | `string` | 是 | 邮箱 |
| `password` | `string` | 是 | 密码 |

**响应** `201`:

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | `bool` | 是否成功 |
| `user_id` | `int` | 新用户 ID |
| `name` | `string` | 用户名 |
| `email` | `string` | 邮箱 |
| `error` | `string` | 错误信息 |

**错误**: `400` — 用户名/邮箱已存在或格式无效。

---

### `GET /user`

获取当前用户信息。**[认证]**

**响应** `200`:

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | `int` | 用户 ID |
| `name` | `string` | 用户名 |
| `email` | `string` | 邮箱 |
| `is_admin` | `bool` | 是否管理员 |
| `is_active` | `bool` | 是否激活 |
| `created_at` | `datetime` | 创建时间 |
| `last_login` | `datetime` | 最后登录时间 |
| `error` | `string` | 错误信息 |

**错误**: `404` — 用户不存在。

---

### `PATCH /user`

更新当前用户信息。**[认证]**

**请求体** (`application/json`):

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `name` | `string` | 否 | 新用户名 |
| `email` | `string` | 否 | 新邮箱 |
| `old_password` | `string` | 否 | 原密码（修改密码时必填） |
| `password` | `string` | 否 | 新密码 |

**响应** `200`:

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | `bool` | 是否成功 |
| `error` | `string` | 错误信息 |

**错误**: `400` — 旧密码错误 / 邮箱已被使用。

---

## 数据集

所有 `dataset_id` 均在请求体中传递，不暴露在 URL。

### `GET /datasets`

获取当前用户的全部数据集。**[认证]**

**响应** `200**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `items` | `Dataset[]` | 数据集列表 |
| `total` | `int` | 总数 |
| `error` | `string` | 错误信息 |

**Dataset** 对象:

| 字段 | 类型 | 说明 |
|------|------|------|
| `id` | `int` | 数据集 ID |
| `owner_id` | `int` | 所属用户 ID |
| `name` | `string` | 名称 |
| `desc` | `string` | 描述 |
| `meta` | `DatasetMeta` | 元信息（format, file_path, file_size） |
| `status` | `int` | 状态码（0=未处理） |
| `tag_ids` | `int[]` | 关联标签 ID |
| `created_at` | `datetime` | 创建时间 |
| `updated_at` | `datetime` | 更新时间 |

---

### `POST /dataset/get`

获取单个数据集详情。**[认证]**

**请求体** (`application/json`):

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `dataset_id` | `int` | 是 | 数据集 ID |

**响应** `200`:

| 字段 | 类型 | 说明 |
|------|------|------|
| `dataset` | `Dataset` | 数据集对象 |
| `error` | `string` | 错误信息 |

**错误**: `404` — 数据集不存在或无权访问。

---

### `POST /dataset/import`

从本地已有文件创建数据集记录。**[认证]**

**请求体** (`application/json`):

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `name` | `string` | 是 | - | 数据集名称 |
| `file_path` | `string` | 是 | - | 文件路径 |
| `desc` | `string` | 否 | `null` | 描述（最长 500） |
| `tag_ids` | `int[]` | 否 | `[]` | 标签 ID 列表 |

**响应** `201`:

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | `bool` | 是否成功 |
| `dataset_id` | `int` | 新数据集 ID |
| `filename` | `string` | 文件名 |
| `file_path` | `string` | 文件路径 |
| `file_size` | `int` | 文件大小（字节） |
| `format` | `string` | 文件格式 |
| `sha256` | `string` | 文件 SHA-256 校验码 |
| `error` | `string` | 错误信息 |

**错误**: `400` — 文件不存在 / 格式不支持。

---

### `PATCH /dataset`

更新数据集信息。`meta`/`owner_id`/`status`/时间戳不可编辑。**[认证]**

**请求体** (`application/json`):

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `dataset_id` | `int` | 是 | 数据集 ID |
| `name` | `string` | 否 | 新名称 |
| `desc` | `string` | 否 | 新描述 |
| `tag_ids` | `int[]` | 否 | 新标签 ID 列表 |

**响应** `200**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | `bool` | 是否成功 |
| `error` | `string` | 错误信息 |

**错误**: `404` — 数据集不存在或无权访问。

---

### `DELETE /datasets`

批量删除数据集（含磁盘文件）。**[认证]**

**请求体** (`application/json`):

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `dataset_ids` | `int[]` | 是 | 要删除的数据集 ID 列表 |

**响应** `200**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | `bool` | 全部成功则为 `true` |
| `deleted` | `int[]` | 成功删除的 ID 列表 |
| `errors` | `string[]` | 失败原因列表 |

**错误**: `404` — 全部失败时。

---

### `POST /dataset/sample`

获取数据集前 N 条样本及表头。**[认证]**

**请求体** (`application/json`):

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `dataset_id` | `int` | 是 | - | 数据集 ID |
| `limit` | `int` | 否 | `100` | 返回行数（1-200） |

**响应** `200**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `columns` | `string[]` | 表头列名 |
| `rows` | `object[]` | 样本数据行 |
| `total_rows` | `int` | 文件总行数 |
| `error` | `string` | 错误信息 |

**错误**: `404` — 数据集不存在或无权访问。

---

### `POST /dataset/process`

提交图生成任务到 GraphGen。仅 `status=0` 的数据集可处理。**[认证]**

**请求体** (`application/json`):

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `dataset_id` | `int` | 是 | - | 数据集 ID |
| `api_key` | `string` | 是 | - | LLM API Key |
| `synthesizer_url` | `string` | 是 | - | 合成模型 API 地址 |
| `synthesizer_model` | `string` | 是 | - | 合成模型名称 |
| `mode` | `string` | 是 | - | 生成模式：`atomic`/`multi_hop`/`aggregated`/`CoT`/`multi_choice`/`multi_answer`/`fill_in_blank`/`true_false` |
| `data_format` | `string` | 是 | - | 输出格式：`Alpaca`/`Sharegpt`/`ChatML` |
| `tokenizer` | `string` | 否 | `cl100k_base` | 分词器 |
| `trainee_model` | `string` | 否 | `null` | 训练目标模型 |
| `trainee_url` | `string` | 否 | `null` | 训练目标 API 地址 |
| `trainee_api_key` | `string` | 否 | `null` | 训练目标 API Key |
| `chunk_size` | `int` | 否 | `1024` | 分块大小 |
| `chunk_overlap` | `int` | 否 | `100` | 分块重叠 |
| `quiz_samples` | `int` | 否 | `2` | Quiz 采样数 |
| `partition_method` | `string` | 否 | `ece` | 图分区算法：`dfs`/`bfs`/`leiden`/`ece` |
| `rpm` | `int` | 否 | `1000` | 每分钟请求数限制 |
| `tpm` | `int` | 否 | `50000` | 每分钟 Token 数限制 |

分区参数：`dfs_max_units`(5)、`bfs_max_units`(5)、`leiden_max_size`(20)、`leiden_use_lcc`(false)、`leiden_random_seed`(42)、`ece_max_units`(20)、`ece_min_units`(3)、`ece_max_tokens`(10240)、`ece_unit_sampling`(random)。

**响应** `200**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `job_id` | `string` | 任务 ID |
| `status` | `string` | `pending`/`running`/`done`/`failed`/`cancelled` |
| `created_at` | `string` | 创建时间 |
| `started_at` | `string` | 开始时间 |
| `finished_at` | `string` | 完成时间 |
| `progress` | `float` | 进度 0.0-1.0 |
| `error` | `string` | 错误信息 |
| `output_path` | `string` | 输出文件路径 |

**错误**: `404` — 数据集不存在或无权访问 / status != 0。

---

### `POST /dataset/download`

生成数据集下载令牌。**[认证]**

**请求体** (`application/json`):

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `dataset_id` | `int` | 是 | 数据集 ID |

**响应** `200**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `download_token` | `string` | 临时下载令牌 |
| `filename` | `string` | 文件名 |
| `file_size` | `int` | 文件大小（字节） |
| `format` | `string` | 文件格式 |
| `sha256` | `string` | 文件 SHA-256 校验码 |
| `error` | `string` | 错误信息 |

**错误**: `404` — 数据集不存在或无权访问 / 文件缺失。

---

### `GET /down_dataset/{token}`

凭下载令牌获取文件流（二进制响应）。无需 Bearer 认证。

**错误**: `401` — 令牌无效或过期。`404` — 数据集或文件不存在。

---

### 分块上传

#### `POST /dataset/upload/initiate`

初始化分块上传。**[认证]**

**请求体** (`application/json`):

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `filename` | `string` | 是 | - | 原始文件名 |
| `file_size` | `int` | 是 | - | 文件总大小（字节） |
| `file_hash` | `string` | 是 | - | 客户端计算的 SHA-256 |
| `chunk_size` | `int` | 否 | `5242880` | 分片大小（1-10 MB） |

**响应** `200**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `upload_id` | `string` | 上传会话 ID |
| `chunk_size` | `int` | 实际分片大小 |
| `total_chunks` | `int` | 总分片数 |
| `uploaded_chunks` | `int[]` | 已上传分片序号 |
| `is_instant_complete` | `bool` | 是否秒传 |

---

#### `POST /dataset/upload/chunk`

上传单个分片。**[认证]**

`multipart/form-data`:

| 字段 | 类型 | 说明 |
|------|------|------|
| `upload_id` | `string` | 上传会话 ID |
| `chunk_index` | `int` | 分片序号（从 0 开始） |
| `file` | `binary` | 分片数据 |

**响应** `200**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `upload_id` | `string` | 上传会话 ID |
| `chunk_index` | `int` | 分片序号 |
| `received` | `bool` | 是否接收成功 |
| `error` | `string` | 错误信息 |

**错误**: `400` — 未知 upload_id。

---

#### `POST /dataset/upload/status`

查询上传进度。**[认证]**

`multipart/form-data`:

| 字段 | 类型 | 说明 |
|------|------|------|
| `upload_id` | `string` | 上传会话 ID |

**响应** `200**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `upload_id` | `string` | 上传会话 ID |
| `uploaded_chunks` | `int[]` | 已上传分片序号 |
| `total_chunks` | `int` | 总分片数 |
| `is_complete` | `bool` | 是否全部上传完成 |

---

#### `POST /dataset/upload/complete`

合并分片、校验哈希、创建数据集记录、建索引。任意步骤失败则回滚。**[认证]**

**请求体** (`application/json`):

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `upload_id` | `string` | 是 | 上传会话 ID |
| `name` | `string` | 是 | 数据集名称 |
| `desc` | `string` | 否 | 描述 |
| `tag_ids` | `int[]` | 否 | 标签 ID 列表 |

**响应** `200**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | `bool` | 是否成功 |
| `dataset_id` | `int` | 新数据集 ID |
| `file_path` | `string` | 最终文件路径 |
| `error` | `string` | 错误信息 |

**错误**: `400` — 未知 upload_id / 分片未收齐 / 哈希不匹配 / 创建失败。

---

## 标签

所有 `tag_id` 均在请求体中传递。

### `GET /tags`

获取当前用户的所有标签。**[认证]**

**响应** `200**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | `bool` | 是否成功 |
| `tags` | `TagInfo[]` | 标签列表 |
| `error` | `string` | 错误信息 |

**TagInfo** 对象:

| 字段 | 类型 | 说明 |
|------|------|------|
| `tag_id` | `int` | 标签 ID |
| `tag_name` | `string` | 标签名称 |
| `tag_color` | `string` | 标签颜色（hex） |
| `tag_desc` | `string` | 标签描述 |
| `tag_created_at` | `string` | 创建时间（ISO 8601） |

---

### `POST /tag/get`

获取单个标签详情。**[认证]**

**请求体** (`application/json`):

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `tag_id` | `int` | 是 | 标签 ID |

**响应** `200**（成功时返回 `TagInfo` 对象）。

**错误**: `404` — 标签不存在或不属于当前用户。

---

### `POST /tag`

创建标签。**[认证]**

**请求体** (`application/json`):

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `name` | `string` | 是 | - | 标签名称 |
| `color` | `string` | 否 | `#808080` | 标签颜色（hex） |
| `desc` | `string` | 否 | `""` | 标签描述 |

**响应** `201`:

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | `bool` | 是否成功 |
| `error` | `string` | 错误信息 |

**错误**: `400` — 同用户下标签名已存在。

---

### `PATCH /tag`

更新标签。仅传要修改的字段。**[认证]**

**请求体** (`application/json`):

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `tag_id` | `int` | 是 | 标签 ID |
| `tag_name` | `string` | 否 | 新名称 |
| `tag_color` | `string` | 否 | 新颜色 |
| `tag_desc` | `string` | 否 | 新描述 |

**响应** `200**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | `bool` | 是否成功 |
| `error` | `string` | 错误信息 |

**错误**: `404` — 标签不存在或无权访问。

---

### `DELETE /tag`

删除标签。**[认证]**

**请求体** (`application/json`):

| 字段 | 类型 | 必填 | 默认值 | 说明 |
|------|------|------|--------|------|
| `tag_id` | `int` | 是 | - | 标签 ID |
| `force` | `bool` | 否 | `false` | 强制删除，同时移除关联数据集中的该 tag |

**响应** `200**:

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | `bool` | 是否成功 |
| `error` | `string` | 错误信息 |

**错误**: `400` — `force=false` 且标签被数据集引用。`404` — 标签不存在或无权访问。

**行为**: `force=false` 且被引用时返回引用列表不删除；`force=true` 遍历数据集移除 `tag_id` 后删除标签。
