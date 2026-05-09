"""测试工具函数"""

from urllib.parse import urlparse, urlunparse

from src.core.config import config


def get_test_db_url() -> str:
    """获取测试数据库 URL（基于项目配置，使用测试专用数据库名）。"""
    parsed = urlparse(config.DATABASE_URL)
    return urlunparse(parsed._replace(path="/llama_factory_test"))
