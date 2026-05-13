# ruff: noqa: RUF003
"""简单的内存级速率限制器。TODO 生产环境建议替换为 Redis 方案。"""

import time
from collections import defaultdict


class RateLimiter:
    """基于 IP + 时间窗口的内存速率限制器。

    Usage::

        limiter = RateLimiter(max_requests=5, window_seconds=60)
        if not limiter.is_allowed(client_ip):
            raise HTTPException(429, "Too many requests")
    """

    def __init__(self, max_requests: int = 5, window_seconds: int = 60):
        self._max = max_requests
        self._window = window_seconds
        self._store: dict[str, list] = defaultdict(list)

    def is_allowed(self, key: str) -> bool:
        now = time.time()
        window_start = now - self._window
        self._store[key] = [t for t in self._store[key] if t > window_start]
        if len(self._store[key]) >= self._max:
            return False
        self._store[key].append(now)
        return True


# 登录：5 次/分钟
login_limiter = RateLimiter(max_requests=5, window_seconds=60)

# 注册：3 次/分钟
register_limiter = RateLimiter(max_requests=3, window_seconds=60)
