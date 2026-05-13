from typing import Any, Mapping, Sequence

from httpx import RequestError, Response

from src.core.config import config as proj_config
from src.services.interfaces.http_client import HTTPClient, HTTPClientConfig


class LlamaFactoryInferenceClient(HTTPClient):
    _API_PREFIX = proj_config.LLAMAFACTORY_API_PREFIX

    def __init__(self, client_config: HTTPClientConfig | None = None) -> None:
        cfg = client_config or HTTPClientConfig(
            name="LlamaFactory Inference",
            url=proj_config.LLAMAFACTORY_URL,
            retries=proj_config.LLAMAFACTORY_RETRIES,
            timeout=proj_config.LLAMAFACTORY_TIMEOUT_MS,
        )
        super().__init__(cfg)

    def _check(self) -> bool:
        try:
            status = self._client.get(f"{self._API_PREFIX}/models")
            return not status.is_error
        except RequestError:
            return False

    @staticmethod
    def _auth_headers(api_key: str = "0") -> Mapping[str, str]:
        return {"Authorization": f"Bearer {api_key}"}

    def list_models(self, api_key: str = "0") -> Response:
        return self.get(f"{self._API_PREFIX}/models", headers=self._auth_headers(api_key))

    def chat(
        self,
        *,
        model: str,
        messages: Sequence[dict[str, Any]],
        api_key: str = "0",
        temperature: float | None = None,
        max_tokens: int | None = None,
    ) -> Response:
        payload: dict[str, Any] = {
            "model": model,
            "messages": list(messages),
        }
        if temperature is not None:
            payload["temperature"] = temperature
        if max_tokens is not None:
            payload["max_tokens"] = max_tokens
        return self.post(
            f"{self._API_PREFIX}/chat/completions",
            json=payload,
            headers=self._auth_headers(api_key),
        )
