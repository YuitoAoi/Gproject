# GProject Backend — 架构文档

**更新:** 2026-05-02  
**范式:** Clean Architecture (端口-适配器)  
**技术栈:** Python 3.12 / FastAPI / SQLAlchemy / Celery / Redis / MySQL  

---

## 1. 分层总览

```
┌──────────────────────────────────────────────────────────┐
│  src/app/                        交付层                  │
│  main.py, router.py, dependencies.py, v1/*.py            │
├──────────────────────────────────────────────────────────┤
│  src/services/                    用例层                  │
│  *_service.py (业务逻辑) + interfaces/ (仓储端口)          │
├──────────────────────────────────────────────────────────┤
│  src/core/                        领域层                  │
│  config.py, user.py, dataset.py, password_encryptor.py   │
├──────────────────────────────────────────────────────────┤
│  src/adapters/                    适配器层               │
│  repositories/mysql_*.py, windows_file_repo.py           │
├──────────────────────────────────────────────────────────┤
│  src/db_connections/ + src/tasks/  基础设施层              │
│  mysql.py, redis.py, celery_app.py, dataset_tasks.py     │
└──────────────────────────────────────────────────────────┘
```

**依赖方向**: `app → services → interfaces ← adapters ← db_connections / tasks`

所有依赖指向抽象 (`interfaces/`)，适配器仅实现接口。

---

## 2. 目录结构

```
src/
├── core/
│   ├── config.py                   # pydantic-settings 全局配置
│   ├── user.py                     # User 实体
│   ├── dataset.py                  # Dataset + DatasetMeta 实体
│   └── password_encryptor.py       # bcrypt 哈希 / 校验
├── services/
│   ├── __init__.py                 # ServiceFactory (DI 容器)
│   ├── interfaces/                 # 仓储接口 (abc 抽象)
│   │   ├── user_repository.py      #   UserRepository
│   │   ├── dataset_repository.py   #   DatasetRepository
│   │   ├── file_repository.py      #   FileRepository
│   │   └── db_conn.py              #   DatabaseConnection
│   ├── user_login_service.py       # 登录用例
│   ├── user_register_service.py    # 注册用例
│   ├── jwt_service.py              # JWT 签发 / 验证
│   ├── datasets_get_service.py     # 数据集查询
│   ├── dataset_create_service.py   # 数据集创建
│   ├── dataset_process_service.py  # 样本预览 + 清洗触发
│   ├── dataset_clean_service.py    # 清洗业务逻辑（纯 Python）
│   └── chunked_upload_service.py   # 分块上传
├── adapters/
│   └── repositories/
│       ├── mysql_user_repo.py      # User MySQL 仓储
│       ├── mysql_dataset_repo.py   # Dataset MySQL 仓储
│       ├── memory_dataset_repo.py  # 内存仓储 (dev/test)
│       └── windows_file_repo.py    # 文件系统适配器
├── db_connections/
│   ├── mysql.py                    # MySQL 连接池 (SQLAlchemy)
│   ├── memory.py                   # SQLite :memory: (测试)
│   └── redis.py                    # Redis 客户端
├── tasks/
│   ├── celery_app.py               # Celery 实例
│   └── dataset_tasks.py            # 清洗 / 转换异步任务
└── app/
    ├── main.py                     # FastAPI 入口 + lifespan + CORS
    ├── router.py                   # /api 路由聚合
    ├── dependencies.py             # 依赖注入 (get_services, get_current_user)
    └── v1/
        ├── apis.py                 # /api/v1 子路由
        ├── dataset.py              # 数据集端点
        └── user.py                 # 认证 / 用户端点
```

---

## 3. 依赖注入

`ServiceFactory` 在 `lifespan` 中实例化并挂载到 `app.state.services`：

```python
# main.py lifespan
db_conn = MysqlDatabaseConnection(config.DATABASE_URL)
app.state.services = ServiceFactory(
    user_repo=MysqlUserRepository(db_conn),
    dataset_repo=MysqlDatasetRepository(db_conn),
    file_repo=WindowsFileRepository(),
)
```

路由通过 `Depends(get_services)` 获取：

```python
@router.get("/")
def list_datasets(
    svc: ServiceFactory = Depends(get_services),
    ...
):
    return svc.get_datasets().get_all(owner_id=owner_id)
```

---

## 4. 认证

### 令牌体系

| 令牌 | 有效期 | 用途 |
|------|--------|------|
| access_token | 1h | `Authorization: Bearer <token>` |
| refresh_token | 7d | 刷新 access_token |
| download_token | 15min | 公开下载（免认证头） |

### 验证链

```
Authorization: Bearer <access_token>
  → Header() 提取
  → request.app.state.services.jwt().verify_access_token(token)
  → 有效 → TokenPayload(user_id, email, exp)
  → 无效 → 401
```

公开端点 (`/health`, `/api/v1/`, `/auth/login`, `/user`, `/down_dataset/{token}`) 不经过此链。

---

## 5. 分块上传

```
initiate                    upload_chunk × N              complete
    │                            │                            │
    ▼                            ▼                            ▼
 创建会话 (内存)            写入 chunks/                    合并分块
 返回 upload_id             {id}/0,1,2...                 SHA-256 校验
                            标记 received                 创建 Dataset 记录
                                                         重命名为 {id}.{ext}
                                                         清理分片
```

**存储**: `{DATA_DIR}/chunks/{upload_id}/` → `{DATA_DIR}/datasets/{id}.{ext}`  
**断点**: `GET /upload/{id}/status` 返回已收分片列表  
**状态**: 内存 dict + `threading.Lock`，单机无外部依赖  

---

## 6. 数据清洗

### 架构

```
DatasetProcessService.process()         ← 应用层（触发）
  → dataset_clean.delay()              ← 基础设施层（编排）
    → DatasetCleanService.execute()    ← 应用层（业务逻辑）
```

服务层 (`DatasetCleanService`) 包含全部清洗算子，纯 Python 实现，不依赖 Celery。  
任务层 (`dataset_clean`) 仅做文件 IO、进度上报、DB 更新。

### 流水线

```
_load (csv/xlsx/json)
  → _apply_field_mapping   源列 → instruction/input/output
  → _apply_basic_filtering 空白行 / 短文本过滤
  → _apply_text_formatting HTML剥离 / 全角半角
  → _apply_pii_masking     手机 / 邮箱 / 身份证 / 银行卡脱敏
  → _apply_deduplication   Exact / MinHash (128维签名)
  → 写入 {name}_cleaned.json
```

### 进度推送

```
Celery Worker → redis.publish("progress:{task_id}", json)
  → WebSocket → 前端 Step 3 实时监控
```

---

## 7. 关键模式

| 模式 | 应用 |
|------|------|
| 端口-适配器 | `interfaces/*.py` (端口) → `adapters/*.py` (适配器) |
| 依赖注入 | ServiceFactory 构造函数注入，路由 Depends 传递 |
| 仓储 | UserRepository / DatasetRepository / FileRepository |
| 工厂 | ServiceFactory 组装依赖，Dataset.new() 创建实体 |
| 策略 | CleanConfig 中每种算子可独立启用/配置 |

---

## 8. 配置

| 变量 | 默认值 | 用途 |
|------|--------|------|
| DATABASE_URL | `mysql+pymysql://root:***@localhost:3306/llama_factory` | MySQL |
| REDIS_URL | `redis://localhost:6379/0` | Redis 通用 |
| CELERY_BROKER_URL | `redis://localhost:6379/1` | Celery 队列 |
| CELERY_RESULT_BACKEND | `redis://localhost:6379/2` | Celery 结果 |
| DATA_DIR | `src-backend/datasets/` | 文件存储 |
| BACKEND_CORS_ORIGINS | `["http://localhost:3000", "http://localhost:5173"]` | CORS |
| JWT_SECRET_KEY | 环境变量 | JWT 签名密钥 |
