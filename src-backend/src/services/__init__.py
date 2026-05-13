# ruff: noqa: F401, RUF002, RUF003, N999
from __future__ import annotations

from src.core.config import config
from src.services.dataset_get_service import (
    GetDatasetResponse,
    GetDatasetsResponse,
    GetDatasetsService,
    GetTimesResponse,
)
from src.services.dataset_import_export_service import (
    CompleteUploadRequest,
    CompleteUploadResponse,
    DatasetDownloadRequest,
    DatasetImportExportResponse,
    DatasetImportExportService,
    DatasetImportRequest,
    InitiateUploadRequest,
    InitiateUploadResponse,
    UploadChunkResponse,
)
from src.services.dataset_process_service import (
    DatasetProcessRequest,
    DatasetProcessResponse,
    DatasetProcessService,
)
from src.services.dataset_remove_service import DatasetRemoveService
from src.services.dataset_tag_service import DatasetTagService
from src.services.dataset_update_service import DatasetAddTagsBatchService, DatasetUpdateService
from src.services.interfaces.dataset_repository import DatasetRepository
from src.services.interfaces.dataset_tag_repository import DatasetTagRepository
from src.services.interfaces.db_conn import DatabaseConnection
from src.services.interfaces.file_repository import FileRepository
from src.services.interfaces.user_repository import UserRepository
from src.services.jwt_service import JWTService
from src.services.llamafactory_service import (
    LlamaFactoryChatRequest,
    LlamaFactoryChatResponse,
    LlamaFactoryDatasetSyncRequest,
    LlamaFactoryDatasetSyncResponse,
    LlamaFactoryModelsResponse,
    LlamaFactoryService,
)
from src.services.user_get_service import (
    UserGetService,
    UserInfoResponse,
)
from src.services.user_login_service import (
    UserLoginRequest,
    UserLoginResponse,
    UserLoginService,
)
from src.services.user_register_service import (
    UserRegisterRequest,
    UserRegisterResponse,
    UserRegisterService,
)
from src.services.user_update_service import UserUpdateRequest, UserUpdateResponse, UserUpdateService

__all__ = [
    "GetDatasetResponse",
    "GetDatasetsResponse",
    "GetTimesResponse",
    "ServiceFactory",
    "UserLoginRequest",
    "UserLoginResponse",
    "UserRegisterRequest",
    "UserRegisterResponse",
]


class ServiceFactory:
    """服务工厂，负责依赖组装与服务实例化。

    每个 ``get_xxx()`` 方法按需创建并缓存单例，
    也可直接访问同名属性获取已缓存实例。
    """

    def __init__(
        self,
        user_repo: UserRepository,
        dataset_repo: DatasetRepository,
        file_repo: FileRepository,
        conn: DatabaseConnection | None = None,
        dataset_tag_repo: DatasetTagRepository | None = None,
    ) -> None:
        from src.services import JWTService

        self._jwt = JWTService(access_token_expire=config.ACCESS_TOKEN_EXPIRE_SECONDS)
        self.user_repo = user_repo
        self._dataset_repo = dataset_repo
        self._file_repo = file_repo
        self._conn = conn
        self._dataset_tag_repo = dataset_tag_repo

        self._dataset_create: DatasetImportExportService | None = None
        self._dataset_get: GetDatasetsService | None = None
        self._dataset_process: DatasetProcessService | None = None

        self._user_login: UserLoginService | None = None
        self._user_get: UserGetService | None = None
        self._user_update: UserUpdateService | None = None
        self._user_register: UserRegisterService | None = None
        self._dataset_update: DatasetUpdateService | None = None
        self._dataset_add_tags: DatasetAddTagsBatchService | None = None
        self._datasets_remove: DatasetRemoveService | None = None
        self._dataset_tag: DatasetTagService | None = None
        self._llamafactory = None

    # ── 仓储懒加载 ──────────────────────────────────────────

    @property
    def dataset_repo(self) -> DatasetRepository:
        if self._dataset_repo is None:
            if self._conn is None:
                raise RuntimeError(
                    "No DatabaseConnection available. Pass conn to ServiceFactory or dataset_repo explicitly."
                )
            from src.adapters.repositories.dataset_repo import (
                DatasetRepositoryAdapter,
            )

            self._dataset_repo = DatasetRepositoryAdapter(self._conn)
        return self._dataset_repo

    @property
    def dataset_tag_repo(self) -> DatasetTagRepository:
        if self._dataset_tag_repo is None:
            if self._conn is None:
                raise RuntimeError(
                    "DatasetTagRepository requires a DatabaseConnection. "
                    "Pass conn or dataset_tag_repo to ServiceFactory."
                )
            from src.adapters.repositories.dataset_tag_repo import (
                DatasetTagRepositoryAdapter,
            )

            self._dataset_tag_repo = DatasetTagRepositoryAdapter(self._conn)
        return self._dataset_tag_repo

    @property
    def dataset_log_repo(self):
        if not hasattr(self, "_dataset_log_repo_cache") or self._dataset_log_repo_cache is None:
            if self._conn is None:
                raise RuntimeError("DatasetLogRepository requires a DatabaseConnection.")
            from src.adapters.repositories.dataset_log_repo import (
                DatasetLogRepository,
            )

            repo = DatasetLogRepository(self._conn)
            repo.init_table()
            self._dataset_log_repo_cache = repo
        return self._dataset_log_repo_cache

    @property
    def task_repo(self):
        if not hasattr(self, "_task_repo_cache") or self._task_repo_cache is None:
            if self._conn is None:
                raise RuntimeError("TaskRepository requires a DatabaseConnection.")
            from src.adapters.repositories.task_repo import TaskRepository

            repo = TaskRepository(self._conn)
            repo.init_table()
            self._task_repo_cache = repo
        return self._task_repo_cache

    @property
    def file_repo(self) -> FileRepository:
        if self._file_repo is None:
            from src.adapters.repositories.windows_file_repo import (
                WindowsFileRepository,
            )

            self._file_repo = WindowsFileRepository()
        return self._file_repo

    # ── 服务实例化（缓存单例） ────────────────────────────────

    def dataset_import_export(self) -> DatasetImportExportService:
        """数据集导入导出统一服务（单例缓存）。"""
        if self._dataset_create is None:
            self._dataset_create = DatasetImportExportService(self.dataset_repo, self.file_repo)
        return self._dataset_create

    def get_datasets(self) -> GetDatasetsService:
        """数据集查询服务。"""
        if self._dataset_get is None:
            self._dataset_get = GetDatasetsService(self.dataset_repo)
        return self._dataset_get

    def chunked_upload(self) -> DatasetImportExportService:
        """分块上传服务，与导入导出共享同一实例。"""
        return self.dataset_import_export()

    def process_dataset(self) -> DatasetProcessService:
        """数据处理服务：样本预览 + 图生成任务 + 下载。

        GraphGen 未就绪时抛出 ConnectionError，不缓存损坏的实例，
        GraphGen 恢复后下次调用重新初始化。
        """
        if self._dataset_process is None:
            from src.adapters.celery_client import celery_client
            from src.adapters.graphgen_client import GraphGenClient

            try:
                self._dataset_process = DatasetProcessService(
                    self.dataset_repo,
                    self.file_repo,
                    GraphGenClient(),
                    celery_client=celery_client,
                    dataset_log_repo=self.dataset_log_repo,
                    task_repo=self.task_repo,
                )
            except ConnectionError:
                self._dataset_process = None
                raise
        return self._dataset_process

    def jwt(self) -> JWTService:
        if self._jwt is None:
            self._jwt = JWTService(access_token_expire=config.ACCESS_TOKEN_EXPIRE_SECONDS)
        return self._jwt

    def login_user(self) -> UserLoginService:
        """用户登录服务"""
        if self._user_login is None:
            self._user_login = UserLoginService(self._jwt, self.user_repo)
        return self._user_login

    def get_user_info(self) -> UserGetService:
        """获取当前用户信息服务"""
        if self._user_get is None:
            self._user_get = UserGetService(self.user_repo)
        return self._user_get

    def update_user_info(self) -> UserUpdateService:
        """更新用户信息服务"""
        if self._user_update is None:
            self._user_update = UserUpdateService(self.user_repo)
        return self._user_update

    def register_user(self) -> UserRegisterService:
        """用户注册服务"""
        if self._user_register is None:
            self._user_register = UserRegisterService(self.user_repo)
        return self._user_register

    def update_dataset(self) -> DatasetUpdateService:
        if self._dataset_update is None:
            self._dataset_update = DatasetUpdateService(self.dataset_repo)
        return self._dataset_update

    def add_tags_batch(self) -> DatasetAddTagsBatchService:
        if self._dataset_add_tags is None:
            self._dataset_add_tags = DatasetAddTagsBatchService(self.dataset_repo)
        return self._dataset_add_tags

    def remove_datasets(self) -> DatasetRemoveService:
        if self._datasets_remove is None:
            self._datasets_remove = DatasetRemoveService(self.dataset_repo, self.file_repo, self.task_repo)
        return self._datasets_remove

    def dataset_tag(self) -> DatasetTagService:
        """数据集标签服务"""
        if self._dataset_tag is None:
            self._dataset_tag = DatasetTagService(self.dataset_tag_repo, self.dataset_repo)
        return self._dataset_tag

    def llamafactory(self) -> LlamaFactoryService:
        if self._llamafactory is None:
            from src.adapters.celery_client import celery_client
            from src.adapters.llamafactory_client import LlamaFactoryClient
            from src.adapters.llamafactory_dataset_client import LlamaFactoryDatasetClient
            from src.adapters.llamafactory_inference_client import LlamaFactoryInferenceClient

            self._llamafactory = LlamaFactoryService(
                dataset_repo=self.dataset_repo,
                task_repo=self.task_repo,
                file_repo=self.file_repo,
                llama_client=LlamaFactoryClient(
                    datasets=LlamaFactoryDatasetClient(file_repo=self.file_repo),
                    inference=LlamaFactoryInferenceClient(),
                    training=None,
                ),
                celery_client=celery_client,
            )
        return self._llamafactory

    # ── 生命周期 ─────────────────────────────────────────────

    def dispose(self) -> None:
        """释放所有资源（数据库连接等）。"""
        if self._conn is not None:
            self._conn.dispose()
        self._dataset_create = None
        self._dataset_get = None
        self._dataset_process = None
        self._user_login = None
        self._user_get = None
        self._user_update = None
        self._user_register = None
        self._dataset_update = None
        self._datasets_remove = None
        self._dataset_tag = None
        self._llamafactory = None
