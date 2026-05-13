"""GraphGenClient 单元测试"""

from unittest.mock import MagicMock, patch

import pytest


class TestGraphGenClient:
    @pytest.fixture
    def client(self):
        with patch("src.services.interfaces.http_client.httpx.Client") as mc:
            mock_http = MagicMock()
            mock_resp = MagicMock()
            mock_resp.is_error = False
            mock_http.get.return_value = mock_resp
            mock_http.request.return_value = MagicMock(is_server_error=False)
            mc.return_value = mock_http

            from src.adapters.graphgen_client import GraphGenClient

            yield GraphGenClient(), mock_http

    def test_init_sets_base_url(self, client):
        cl, _ = client
        assert cl._API_PREFIX == "/api/v1"

    def test_health_check(self, client):
        _cl, mock_http = client
        mock_http.get.assert_called_with("/health")

    def test_validate_connection(self, client):
        cl, mock_http = client
        cl.validate_connection(
            base_url="https://api.example.com/v1",
            api_key="sk-xxx",
            model="test-model",
        )
        mock_http.request.assert_called_with(
            method="POST",
            url="/api/v1/connections/validate",
            params=None,
            json={"base_url": "https://api.example.com/v1", "api_key": "sk-xxx", "model": "test-model"},
            data=None,
            headers=None,
            files=None,
        )

    def test_submit_job(self, client):
        cl, mock_http = client
        payload = {"input_file": "test.jsonl", "mode": "atomic"}
        cl.submit_job(payload)
        mock_http.request.assert_called_with(
            method="POST",
            url="/api/v1/jobs",
            params=None,
            json=payload,
            data=None,
            headers=None,
            files=None,
        )

    def test_get_job(self, client):
        cl, mock_http = client
        cl.get_job("abc-123")
        mock_http.request.assert_called_with(
            method="GET",
            url="/api/v1/jobs/abc-123",
            params=None,
            json=None,
            data=None,
            headers=None,
            files=None,
        )

    def test_cancel_job(self, client):
        cl, mock_http = client
        cl.cancel_job("abc-123")
        mock_http.request.assert_called_with(
            method="DELETE",
            url="/api/v1/jobs/abc-123",
            params=None,
            json=None,
            data=None,
            headers=None,
            files=None,
        )
