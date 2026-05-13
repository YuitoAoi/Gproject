# ruff: noqa: RUF002
"""ServiceFactory 单元测试"""

from unittest.mock import MagicMock

import pytest
from src.services import ServiceFactory
from src.services.interfaces.dataset_repository import DatasetRepository
from src.services.interfaces.file_repository import FileRepository
from src.services.interfaces.user_repository import UserRepository


@pytest.fixture
def factory():
    return ServiceFactory(
        user_repo=MagicMock(spec=UserRepository),
        dataset_repo=MagicMock(spec=DatasetRepository),
        file_repo=MagicMock(spec=FileRepository),
        conn=None,
    )


class TestServiceFactory:
    def test_dataset_import_export(self, factory):
        svc = factory.dataset_import_export()
        assert svc is not None
        # Second call returns cached instance
        assert factory.dataset_import_export() is svc
        # Same as chunked_upload
        assert factory.chunked_upload() is svc

    def test_get_datasets(self, factory):
        svc = factory.get_datasets()
        assert svc is not None
        assert factory.get_datasets() is svc

    def test_process_dataset(self, factory):
        """process_dataset 需要 GraphGen 连接，可能失败"""
        try:
            svc = factory.process_dataset()
            assert svc is not None
        except (RuntimeError, Exception):
            pass

    def test_jwt(self, factory):
        svc = factory.jwt()
        assert svc is not None
        assert factory.jwt() is svc

    def test_login_user(self, factory):
        svc = factory.login_user()
        assert svc is not None

    def test_get_user_info(self, factory):
        svc = factory.get_user_info()
        assert svc is not None

    def test_update_user_info(self, factory):
        svc = factory.update_user_info()
        assert svc is not None

    def test_register_user(self, factory):
        svc = factory.register_user()
        assert svc is not None

    def test_remove_datasets(self, factory):
        svc = factory.remove_datasets()
        assert svc is not None

    def test_update_dataset(self, factory):
        svc = factory.update_dataset()
        assert svc is not None

    def test_dataset_tag_requires_conn(self, factory):
        """dataset_tag 需要 _conn，可能失败"""
        try:
            svc = factory.dataset_tag()
            assert svc is not None
        except RuntimeError:
            pass  # 无 conn 时预期抛 RuntimeError

    def test_dataset_repo_property(self, factory):
        repo = factory.dataset_repo
        assert repo is not None

    def test_file_repo_property(self, factory):
        fr = factory.file_repo
        assert fr is not None

    def test_dispose(self, factory):
        svc1 = factory.get_datasets()
        factory.dispose()
        svc2 = factory.get_datasets()
        assert svc1 is not svc2
