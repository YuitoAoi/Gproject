"""
服务层 — 工厂组装模式

    from src.services import ServiceFactory

    # 开发
    factory = ServiceFactory()

    # 生产
    factory = ServiceFactory(
        dataset_repo=MysqlDatasetRepoAdapter(db_conn),
        file_repo=WindowsFileRepoAdapter("/data"),
    )

    # 使用
    factory.create_dataset.execute(request)
    factory.get_datasets.get_all()
"""

from __future__ import annotations

from typing import Optional

from src.services.dataset_create_service import (
    CreateDatasetRequest,
    CreateDatasetResponse,
    CreateDatasetService,
)
from src.services.dataset_get_service import (
    GetDatasetResponse,
    GetDatasetsResponse,
    GetDatasetsService,
)
from src.services.dataset_import_export_service import (
    ExportDatasetService,
    ImportDatasetService,
    ImportExportDatasetRequest,
    ImportExportDatasetResponse,
)
from src.services.jwt_service import JWTService
from src.services.user_login_service import (
    UserLoginService,
    UserLoginRequest,
    UserLoginResponse,
)
from src.services.user_get_service import (
    UserGetService,
    UserInfoResponse,
)
from src.services.user_update_service import (
    UserUpdateService,
    UserUpdateRequest,
    UserUpdateResponse
)
from src.services.user_register_service import (
    UserRegisterService,
    UserRegisterRequest,
    UserRegisterResponse,
)
from src.services.interfaces.dataset_repository import DatasetRepository
from src.services.interfaces.dataset_tag_repository import DatasetTagRepository
from src.services.interfaces.user_repository import UserRepository
from src.services.interfaces.file_repository import FileRepository
from src.services.chunked_upload_service import (
    ChunkedUploadService,
)
from src.services.dataset_process_service import (
    DatasetProcessService,
    ProcessRequest,
    ProcessResponse,
)
from src.services.dataset_tag_service import DatasetTagService

__all__ = [
    "ServiceFactory",
    # 数据集
    "GetDatasetResponse",
    "GetDatasetsResponse",
    # 用户
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
        dataset_tag_repo: Optional[DatasetTagRepository] = None,
    ) -> None:
        from src.services import JWTService
        self._jwt = JWTService()
        self.user_repo = user_repo
        self._dataset_repo = dataset_repo
        self._file_repo = file_repo
        self._dataset_tag_repo = dataset_tag_repo

        self._dataset_create: Optional[CreateDatasetService] = None
        self._dataset_get: Optional[GetDatasetsService] = None
        self._dataset_import: Optional[ImportDatasetService] = None
        self._dataset_export: Optional[ExportDatasetService] = None
        self._dataset_process: Optional[DatasetProcessService] = None
        self._chunked_upload: Optional[ChunkedUploadService] = None

        self._user_login: Optional[UserLoginService] = None
        self._user_get: Optional[UserGetService] = None
        self._user_update: Optional[UserUpdateService] = None
        self._user_register: Optional[UserRegisterService] = None
        self._dataset_tag: Optional[DatasetTagService] = None

    # ── 仓储懒加载 ──────────────────────────────────────────

    @property
    def dataset_repo(self) -> DatasetRepository:
        if self._dataset_repo is None:
            from src.adapters.repositories.memory_dataset_repo import (
                MemoryDatasetRepoAdpter,
            )
            self._dataset_repo = MemoryDatasetRepoAdpter()
        return self._dataset_repo

    @property
    def dataset_tag_repo(self) -> DatasetTagRepository:
        if self._dataset_tag_repo is None:
            conn = getattr(self.dataset_repo, "_conn", None)
            if conn is None:
                raise RuntimeError(
                    "DatasetTagRepository requires a database-backed DatasetRepository. "
                    "Pass dataset_tag_repo explicitly to ServiceFactory."
                )
            from src.adapters.repositories.mysql_dataset_tag_repo import (
                MysqlDatasetTagRepository,
            )
            self._dataset_tag_repo = MysqlDatasetTagRepository(conn)
        return self._dataset_tag_repo

    @property
    def file_repo(self) -> FileRepository:
        if self._file_repo is None:
            from src.adapters.repositories.windows_file_repo import (
                WindowsFileRepository,
            )
            self._file_repo = WindowsFileRepository()
        return self._file_repo

    # ── 服务实例化（缓存单例） ────────────────────────────────

    def create_dataset(self) -> CreateDatasetService:
        """创建数据集服务。"""
        if self._dataset_create is None:
            self._dataset_create = CreateDatasetService(self.dataset_repo, self.file_repo)
        return self._dataset_create

    def get_datasets(self) -> GetDatasetsService:
        """数据集查询服务。"""
        if self._dataset_get is None:
            self._dataset_get = GetDatasetsService(self.dataset_repo)
        return self._dataset_get

    def import_dataset(self) -> ImportDatasetService:
        """数据集导入服务。"""
        if self._dataset_import is None:
            self._dataset_import = ImportDatasetService(self.dataset_repo, self.file_repo)
        return self._dataset_import

    def export_dataset(self) -> ExportDatasetService:
        """数据集导出服务。"""
        if self._dataset_export is None:
            self._dataset_export = ExportDatasetService(self.dataset_repo, self.file_repo)
        return self._dataset_export

    def chunked_upload(self) -> ChunkedUploadService:
        """分块上传服务。"""
        if self._chunked_upload is None:
            self._chunked_upload = ChunkedUploadService(
                self.dataset_repo, self.file_repo
            )
        return self._chunked_upload

    def process_dataset(self) -> DatasetProcessService:
        """数据处理服务：样本预览 + 清洗/转换/下载。"""
        if self._dataset_process is None:
            self._dataset_process = DatasetProcessService(
                self.dataset_repo, self.file_repo
            )
        return self._dataset_process
    
    def jwt(self) -> JWTService:
        if self._jwt is None:
            self._jwt = JWTService()
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
        """获取当前用户信息服务"""
        if self._user_update is None:
            self._user_update = UserUpdateService(self.user_repo)
        return self._user_update
    
    def register_user(self) -> UserRegisterService:
        """用户注册服务"""
        if self._user_register is None:
            self._user_register = UserRegisterService(self.user_repo)
        return self._user_register

    def dataset_tag(self) -> DatasetTagService:
        """数据集标签服务"""
        if self._dataset_tag is None:
            self._dataset_tag = DatasetTagService(self.dataset_tag_repo, self.dataset_repo)
        return self._dataset_tag

    # ── 生命周期 ─────────────────────────────────────────────

    def dispose(self) -> None:
        """释放所有资源（数据库连接等）。"""
        if self._dataset_repo is not None:
            # TODO 实现数据库释放资源业务
            # self._dataset_repo.dispose()
            pass
        
        self._dataset_create = None
        self._dataset_get = None
        self._dataset_import = None
        self._dataset_export = None
        self._dataset_process = None
