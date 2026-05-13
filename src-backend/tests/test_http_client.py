# ruff: noqa: RUF002
"""HTTPClient 单元测试"""

from unittest.mock import MagicMock, patch

import pytest
from src.services.interfaces.http_client import HTTPClient, HTTPClientConfig


class _TestClient(HTTPClient):
    """具体子类，用于测试基类行为。"""


class TestHTTPClient:
    @pytest.fixture
    def config(self):
        return HTTPClientConfig(name="test", url="http://localhost:9999", retries=2, timeout=1000)

    @patch("src.services.interfaces.http_client.httpx.Client")
    def test_init_success(self, mock_client_cls, config):
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.is_error = False
        mock_client.get.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        client = _TestClient(config)
        assert client.config == config
        mock_client_cls.assert_called_once()

    @patch("src.services.interfaces.http_client.httpx.Client")
    def test_init_check_fails(self, mock_client_cls, config):
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.is_error = True
        mock_client.get.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        with pytest.raises(ConnectionError):
            _TestClient(config)
        mock_client.close.assert_called_once()

    @patch("src.services.interfaces.http_client.httpx.Client")
    def test_context_manager(self, mock_client_cls, config):
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.is_error = False
        mock_client.get.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        with _TestClient(config) as _client:
            pass
        mock_client.close.assert_called_once()

    @patch("src.services.interfaces.http_client.httpx.Client")
    def test_get_request(self, mock_client_cls, config):
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.is_error = False
        mock_client.get.return_value = mock_resp
        mock_client.request.return_value = MagicMock(is_server_error=False)
        mock_client_cls.return_value = mock_client

        client = _TestClient(config)
        _resp = client.get("/api/test", params={"key": "val"})
        mock_client.request.assert_called_with(
            method="GET",
            url="/api/test",
            params={"key": "val"},
            json=None,
            data=None,
            headers=None,
            files=None,
        )

    @patch("src.services.interfaces.http_client.httpx.Client")
    def test_post_request(self, mock_client_cls, config):
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.is_error = False
        mock_client.get.return_value = mock_resp
        mock_client.request.return_value = MagicMock(is_server_error=False)
        mock_client_cls.return_value = mock_client

        client = _TestClient(config)
        _resp = client.post("/api/data", json={"key": "val"})
        mock_client.request.assert_called_with(
            method="POST",
            url="/api/data",
            params=None,
            json={"key": "val"},
            data=None,
            headers=None,
            files=None,
        )

    @patch("src.services.interfaces.http_client.httpx.Client")
    def test_put_patch_delete(self, mock_client_cls, config):
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.is_error = False
        mock_client.get.return_value = mock_resp
        mock_client.request.return_value = MagicMock(is_server_error=False)
        mock_client_cls.return_value = mock_client

        client = _TestClient(config)
        client.put("/x")
        client.patch("/x")
        client.delete("/x")
        assert mock_client.request.call_count == 3

    @patch("src.services.interfaces.http_client.httpx.Client")
    def test_retry_on_server_error(self, mock_client_cls, config):
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.is_error = False
        mock_client.get.return_value = mock_resp
        r1 = MagicMock(is_server_error=True)
        r2 = MagicMock(is_server_error=False)
        mock_client.request.side_effect = [r1, r2]
        mock_client_cls.return_value = mock_client

        client = _TestClient(config)
        _resp = client.get("/test")
        assert mock_client.request.call_count == 2

    @patch("src.services.interfaces.http_client.httpx.Client")
    def test_check_exception(self, mock_client_cls, config):
        mock_client = MagicMock()
        mock_resp = MagicMock()
        mock_resp.is_error = False
        mock_client.get.return_value = mock_resp
        mock_client_cls.return_value = mock_client

        client = _TestClient(config)
        resp = MagicMock()
        client.check_exception(resp)
        resp.raise_for_status.assert_called_once()
