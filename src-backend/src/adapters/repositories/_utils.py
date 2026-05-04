"""仓库层共享工具。"""
from datetime import datetime


def ensure_datetime(value) -> datetime:
    """将数据库行值转为 datetime，兼容字符串和 datetime 对象。"""
    if isinstance(value, datetime):
        return value
    if value is not None:
        return datetime.fromisoformat(str(value))
    return value
