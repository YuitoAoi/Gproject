import abc
import asyncio
import time
from typing import Any, Mapping, Self

import httpx
import msgspec
from httpx import Response


class HTTPClientConfig(msgspec.Struct):
    name: str
    url: str
    retries: int = 3
    timeout: int = 5000  # ms


class HTTPClient(abc.ABC):
    """HTTP 客户端基类，封装 httpx 同步客户端。

    内置连接健康检查、5xx 自动重试、上下文管理器。
    子类可重写 ``_check`` 或 ``_request`` 以自定义行为。
    """

    config: HTTPClientConfig

    def __init__(self, config: HTTPClientConfig) -> None:
        self.config = config
        self._client = httpx.Client(
            base_url=config.url,
            timeout=httpx.Timeout(config.timeout / 1000.0),
        )
        if not self._check():
            self._client.close()
            raise ConnectionError(f"Connect to {self.config.name} Failed.")

    # ---- 生命周期 ----

    def close(self) -> None:
        """关闭底层 httpx 客户端，释放连接。"""
        self._client.close()

    def __enter__(self) -> Self:
        return self

    def __exit__(self, *args: Any) -> None:
        self.close()

    # ---- 内部 ----

    def _check(self) -> bool:
        """连接健康检查，默认对 base_url 根路径发起 GET。"""
        try:
            status = self._client.get("/")
            return not status.is_error
        except httpx.RequestError:
            return False

    def _request(
        self,
        method: str,
        path: str = "/",
        *,
        params: Mapping[str, Any] | None = None,
        json: Any = None,
        data: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        files: Mapping[str, Any] | None = None,
    ) -> Response:
        """带自动重试的内部请求方法。仅对 5xx 和网络错误重试，带指数退避。"""
        last_exc: Exception | None
        for attempt in range(self.config.retries):
            try:
                resp = self._client.request(
                    method=method,
                    url=path,
                    params=params,
                    json=json,
                    data=data,
                    headers=headers,
                    files=files,
                )
                if not resp.is_server_error or attempt == self.config.retries - 1:
                    return resp
            except httpx.RequestError as exc:
                last_exc = exc
                if attempt == self.config.retries - 1:
                    raise
                time.sleep(2**attempt * 0.1)

    # ---- HTTP 方法 ----

    def get(
        self,
        path: str = "/",
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Response:
        return self._request("GET", path, params=params, headers=headers)

    def post(
        self,
        path: str = "/",
        *,
        json: Any = None,
        data: Mapping[str, Any] | None = None,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        files: Mapping[str, Any] | None = None,
    ) -> Response:
        return self._request(
            "POST",
            path,
            params=params,
            json=json,
            data=data,
            headers=headers,
            files=files,
        )

    def put(
        self,
        path: str = "/",
        *,
        json: Any = None,
        data: Mapping[str, Any] | None = None,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Response:
        return self._request(
            "PUT", path, params=params, json=json, data=data, headers=headers
        )

    def patch(
        self,
        path: str = "/",
        *,
        json: Any = None,
        data: Mapping[str, Any] | None = None,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Response:
        return self._request(
            "PATCH", path, params=params, json=json, data=data, headers=headers
        )

    def delete(
        self,
        path: str = "/",
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Response:
        return self._request("DELETE", path, params=params, headers=headers)

    # ---- 工具 ----

    def check_exception(self, resp: Response) -> None:
        """若响应异常则抛出 HTTPStatusError，子类可重写以注入自定义错误映射。"""
        resp.raise_for_status()


class AsyncHTTPClient(abc.ABC):
    """HTTP 客户端基类，封装 httpx 异步客户端。

    用法::

        async with AsyncHTTPClient(config) as client:
            resp = await client.get("/api/data")
    """

    config: HTTPClientConfig

    def __init__(self, config: HTTPClientConfig) -> None:
        self.config = config
        self._client: httpx.AsyncClient | None

    async def __aenter__(self) -> Self:
        self._client = httpx.AsyncClient(
            base_url=self.config.url,
            timeout=httpx.Timeout(self.config.timeout / 1000.0),
        )
        if not await self._check():
            await self._client.aclose()
            raise ConnectionError(f"Connect to {self.config.name} Failed.")
        return self

    async def __aexit__(self, *args: Any) -> None:
        if self._client is not None:
            await self._client.aclose()

    async def _check(self) -> bool:
        assert self._client is not None
        try:
            status = await self._client.get("/")
            return not status.is_error
        except httpx.RequestError:
            return False

    async def _request(
        self,
        method: str,
        path: str = "/",
        *,
        params: Mapping[str, Any] | None = None,
        json: Any = None,
        data: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        files: Mapping[str, Any] | None = None,
    ) -> Response:
        assert self._client is not None
        last_exc: Exception | None
        for attempt in range(self.config.retries):
            try:
                resp = await self._client.request(
                    method=method,
                    url=path,
                    params=params,
                    json=json,
                    data=data,
                    headers=headers,
                    files=files,
                )
                if not resp.is_server_error or attempt == self.config.retries - 1:
                    return resp
            except httpx.RequestError as exc:
                last_exc = exc
                if attempt == self.config.retries - 1:
                    raise
                await asyncio.sleep(2**attempt * 0.1)

    # ---- HTTP 方法 ----

    async def get(
        self,
        path: str = "/",
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Response:
        return await self._request("GET", path, params=params, headers=headers)

    async def post(
        self,
        path: str = "/",
        *,
        json: Any = None,
        data: Mapping[str, Any] | None = None,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
        files: Mapping[str, Any] | None = None,
    ) -> Response:
        return await self._request(
            "POST",
            path,
            params=params,
            json=json,
            data=data,
            headers=headers,
            files=files,
        )

    async def put(
        self,
        path: str = "/",
        *,
        json: Any = None,
        data: Mapping[str, Any] | None = None,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Response:
        return await self._request(
            "PUT", path, params=params, json=json, data=data, headers=headers
        )

    async def patch(
        self,
        path: str = "/",
        *,
        json: Any = None,
        data: Mapping[str, Any] | None = None,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Response:
        return await self._request(
            "PATCH", path, params=params, json=json, data=data, headers=headers
        )

    async def delete(
        self,
        path: str = "/",
        *,
        params: Mapping[str, Any] | None = None,
        headers: Mapping[str, str] | None = None,
    ) -> Response:
        return await self._request("DELETE", path, params=params, headers=headers)

    async def check_exception(self, resp: Response) -> None:
        resp.raise_for_status()
