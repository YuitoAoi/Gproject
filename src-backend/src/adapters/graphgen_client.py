from typing import Optional
from urllib.parse import urlparse

from httpx import Response

from src.core.config import config as proj_config
from src.services.interfaces.http_client import HTTPClient, HTTPClientConfig


class GraphGenClient(HTTPClient):
    """GraphGen 数据生成 API 客户端。

    base_url 取 GRAPHGEN_API_URL 的 scheme+host+port，
    API 路径统一带 /api/v1 前缀，健康检查在 /health。
    """

    _API_PREFIX = "/api/v1"

    def __init__(self, config: Optional[HTTPClientConfig] = None) -> None:
        url = proj_config.GRAPHGEN_API_URL  # http://localhost:8001/api/v1
        parsed = urlparse(url)
        base = f"{parsed.scheme}://{parsed.netloc}"

        if config is None:
            config = HTTPClientConfig(name="GraphGen", url=base)
        else:
            config.url = base
        super().__init__(config)

    # ── 健康检查 ──────────────────────────────────────────────

    def _check(self) -> bool:
        try:
            status = self._client.get("/health")
            return not status.is_error
        except Exception:
            return False

    # ── 连接验证 ──────────────────────────────────────────────

    def validate_connection(
        self,
        base_url: str,
        api_key: str,
        model: str,
    ) -> Response:
        """测试 LLM API 连通性。

        POST /api/v1/connections/validate
        """
        return self._request(
            "POST",
            f"{self._API_PREFIX}/connections/validate",
            json={
                "base_url": base_url,
                "api_key": api_key,
                "model": model,
            },
        )

    # ── 任务 ──────────────────────────────────────────────────

    def submit_job(self, payload: dict) -> Response:
        """提交数据生成任务。

        POST /api/v1/jobs → 202
        """
        return self._request(
            "POST",
            f"{self._API_PREFIX}/jobs",
            json=payload,
        )

    def get_job(self, job_id: str) -> Response:
        """查询任务状态。

        GET /api/v1/jobs/{job_id} → 200
        """
        return self._request("GET", f"{self._API_PREFIX}/jobs/{job_id}")

    def cancel_job(self, job_id: str) -> Response:
        """取消任务。

        DELETE /api/v1/jobs/{job_id} → 200
        """
        return self._request("DELETE", f"{self._API_PREFIX}/jobs/{job_id}")
