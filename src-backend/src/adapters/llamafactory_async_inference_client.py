from collections.abc import Mapping, Sequence
from typing import Any, AsyncGenerator

import httpx

from src.core.config import config as proj_config
from src.services.interfaces.http_client import AsyncHTTPClient, HTTPClientConfig


class LlamaFactoryAsyncInferenceClient(AsyncHTTPClient):
    _API_PREFIX = proj_config.LLAMAFACTORY_API_PREFIX

    def __init__(self, client_config: HTTPClientConfig | None = None) -> None:
        cfg = client_config or HTTPClientConfig(
            name="LlamaFactory Async Inference",
            url=proj_config.LLAMAFACTORY_URL,
            retries=proj_config.LLAMAFACTORY_RETRIES,
            timeout=proj_config.LLAMAFACTORY_TIMEOUT_MS,
        )
        super().__init__(cfg)

    async def _check(self) -> bool:
        assert self._client is not None
        try:
            status = await self._client.get(f"{self._API_PREFIX}/models")
            return not status.is_error
        except httpx.RequestError:
            return False

    @staticmethod
    def _auth_headers(api_key: str = "0") -> Mapping[str, str]:
        return {"Authorization": f"Bearer {api_key}"}

    async def list_models(self, api_key: str = "0") -> httpx.Response:
        assert self._client is not None
        return await self._client.get(
            f"{self._API_PREFIX}/models",
            headers=self._auth_headers(api_key),
        )

    async def chat(
        self,
        *,
        model: str,
        messages: Sequence[dict[str, Any]],
        api_key: str = "0",
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> httpx.Response:
        assert self._client is not None
        payload: dict[str, Any] = {
            "model": model,
            "messages": list(messages),
            "stream": False,
        }
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        return await self._client.post(
            f"{self._API_PREFIX}/chat/completions",
            json=payload,
            headers=self._auth_headers(api_key),
        )

    async def stream_chat(
        self,
        *,
        model: str,
        messages: Sequence[dict[str, Any]],
        api_key: str = "0",
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> AsyncGenerator[bytes, None]:
        """流式对话，以 SSE 格式 yield 每个 data: {...} 行。"""
        assert self._client is not None
        payload: dict[str, Any] = {
            "model": model,
            "messages": list(messages),
            "stream": True,
        }
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens

        headers = {**self._auth_headers(api_key), "Accept": "text/event-stream"}

        async with self._client.stream(
            "POST",
            f"{self._API_PREFIX}/chat/completions",
            json=payload,
            headers=headers,
        ) as resp:
            resp.raise_for_status()
            async for line in resp.aiter_lines():
                if line.startswith("data: "):
                    data = line[6:].strip()
                    if data == "[DONE]":
                        break
                    yield f"{line}\n\n".encode()
