# GProject API v1

**Base URL**: `/api/v1`

所有需要认证的端点必须在请求头中携带 `Authorization: Bearer <access_token>`。

---

## 认证

### `POST /auth/login`

登录获取 token。

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

---

## 用户

### `POST /user`

注册新用户。

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

---

### `GET /user`

获取当前用户信息。 **[认证]**

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

---

### `PATCH /user`

更新当前用户信息。 **[认证]**

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

---

## 数据集

### `GET /dataset/`

获取当前用户的全部数据集。 **[认证]**

**响应** `200`:

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
| `status` | `int` | 状态码 |
| `tag_ids` | `int[]` | 关联标签 ID 列表 |
| `created_at` | `datetime` | 创建时间 |
| `updated_at` | `datetime` | 更新时间 |

---

### `GET /dataset/{dataset_id}`

获取单个数据集详情。 **[认证]**

**响应** `200`:

| 字段 | 类型 | 说明 |
|------|------|------|
| `dataset` | `Dataset` | 数据集对象 |
| `error` | `string` | 错误信息 |

---

### `DELETE /dataset/{dataset_id}`

删除数据集及其文件。 **[认证]**

**响应** `200`:

```json
{ "deleted": "1" }
```

---

### 分块上传

#### `POST /dataset/upload/initiate`

初始化分块上传。 **[认证]**

**请求体** (`application/json`):

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `filename` | `string` | 是 | 文件名 |
| `file_size` | `int` | 是 | 文件大小（字节） |
| `file_hash` | `string` | 是 | 客户端 SHA-256 |
| `chunk_size` | `int` | 否 | 分片大小（1-10 MB，默认 5 MB） |

---

#### `POST /dataset/upload/chunk`

上传单个分片 (`multipart/form-data`)。 **[认证]**

| 字段 | 类型 | 说明 |
|------|------|------|
| `upload_id` | `string` (form) | 上传会话 ID |
| `chunk_index` | `int` (form) | 分片序号（从 0 开始） |
| `file` | `file` (form) | 分片二进制数据 |

---

#### `GET /dataset/upload/{upload_id}/status`

查询上传进度（支持断点续传）。 **[认证]**

---

#### `POST /dataset/upload/complete`

合并分片、校验哈希、创建数据集记录。 **[认证]**

**请求体** (`application/json`):

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `upload_id` | `string` | 是 | 上传会话 ID |
| `name` | `string` | 是 | 数据集名称 |
| `desc` | `string` | 否 | 描述 |
| `tag_ids` | `int[]` | 否 | 标签 ID 列表 |

---

### 样本与处理

#### `GET /dataset/{dataset_id}/sample`

获取数据集前 N 条样本及表头。 **[认证]**

**查询参数**:

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `limit` | `int` | `100` | 返回行数（1-200） |

---

#### `POST /dataset/{dataset_id}/process`

提交数据清洗/格式转换任务。 **[认证]**

---

#### `POST /dataset/{dataset_id}/download`

生成下载令牌。 **[认证]**

**响应** `200`:

| 字段 | 类型 | 说明 |
|------|------|------|
| `download_token` | `string` | 下载令牌 |
| `filename` | `string` | 文件名 |
| `file_size` | `int` | 文件大小 |
| `format` | `string` | 文件格式 |

---

### `GET /down_dataset/{token}`

凭下载令牌获取文件流（二进制响应）。

---

## 标签

### `GET /tags`

获取当前用户的所有标签。 **[认证]**

**响应** `200`:

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | `bool` | 是否成功 |
| `error` | `string` | 错误信息 |
| `tags` | `TagInfo[]` | 标签列表 |

**TagInfo** 对象:

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | `bool` | 是否成功 |
| `error` | `string` | 错误信息 |
| `tag_id` | `int` | 标签 ID |
| `tag_name` | `string` | 标签名称 |
| `tag_color` | `string` | 标签颜色（hex） |
| `tag_desc` | `string` | 标签描述 |
| `tag_created_at` | `string` | 创建时间（ISO 8601） |

---

### `GET /tag/{tag_id}`

获取单个标签详情。 **[认证]**

**响应** `200`: 返回单个 `TagInfo` 对象（结构同上）。

**错误** `400`: 标签不存在或不属于当前用户时返回 `"Tag not found"`。

---

### `POST /tag/`

创建标签。 **[认证]**

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
| `error` | `string` | 错误信息（如重名时返回 `"Tag name already exists for this user: xxx"`） |

---

### `PATCH /tag/{tag_id}`

更新标签。 **[认证]**

仅需传入要修改的字段，未传入的字段保持不变。

**请求体** (`application/json`):

| 字段 | 类型 | 必填 | 说明 |
|------|------|------|------|
| `tag_name` | `string` | 否 | 新名称 |
| `tag_color` | `string` | 否 | 新颜色 |
| `tag_desc` | `string` | 否 | 新描述 |

**响应** `200`:

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | `bool` | 是否成功 |
| `error` | `string` | 错误信息（标签不存在/无权访问返回 `"Tag not found"`，重名返回相应错误） |

---

### `DELETE /tag/{tag_id}`

删除标签。 **[认证]**

**查询参数**:

| 参数 | 类型 | 默认 | 说明 |
|------|------|------|------|
| `force` | `bool` | `false` | `false` 时若标签被数据集引用则返回引用列表；`true` 时级联移除所有关联并删除 |

**响应** `200`:

| 字段 | 类型 | 说明 |
|------|------|------|
| `success` | `bool` | 是否成功 |
| `error` | `string` | 错误信息 |

**行为**:

- `force=false`，标签被数据集引用 → 返回 `"Tag is referenced by: [数据集名称列表]"`，不执行删除
- `force=true` → 遍历用户数据集移除该 `tag_id`，随后删除标签
- 标签不存在或不属于当前用户 → 返回 `"Tag not found"`
