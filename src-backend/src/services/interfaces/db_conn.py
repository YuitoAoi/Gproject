import abc
from typing import Any

from sqlalchemy.orm import Session


class DatabaseConnection(abc.ABC):
    """数据库连接抽象。SQLAlchemy 引擎 + 会话工厂的生命周期管理。"""

    @property
    @abc.abstractmethod
    def engine(self):
        """SQLAlchemy Engine 实例。start() 后可用。"""
        ...

    @property
    @abc.abstractmethod
    def is_connected(self) -> bool:
        """当前连接是否可用。"""
        ...

    @abc.abstractmethod
    def start(self, **kwargs: Any) -> None:
        """初始化引擎与会话工厂。幂等操作，重复调用不重建。"""

    @abc.abstractmethod
    def new_session(self) -> Session:
        """创建一个新的 SQLAlchemy Session 实例。调用者负责关闭。"""

    @abc.abstractmethod
    def dispose(self) -> None:
        """释放引擎、清空连接池。"""

    @abc.abstractmethod
    def create_tables(self, base: Any) -> None:
        """根据 declarative Base 创建所有缺失的表。"""

    @abc.abstractmethod
    def drop_tables(self, base: Any) -> None:
        """根据 declarative Base 删除所有表。"""
