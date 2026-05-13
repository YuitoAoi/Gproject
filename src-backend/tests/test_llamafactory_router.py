"""LlamaFactory 路由集成测试（同步原型）"""
from unittest.mock import MagicMock

import pytest
from fastapi import FastAPI
from fastapi.testclient import TestClient


def _make_token_payload(user_id="1"):
    from src.services.jwt_service import TokenPayload
    return TokenPayload(user_id=user_id, email="admin@test.com", exp=9999999999)


def _build_app():
    app = FastAPI()

    from src.app.v1.llamafactory import router
    app.include_router(router)

    mock_jwt = MagicMock()
    mock_jwt.verify_access_token.return_value = _make_token_payload()

    mock_svc = MagicMock()
    mock_svc.jwt.return_value = mock_jwt
    app.state.services = mock_svc

    from src.app.dependencies import get_services
    app.dependency_overrides[get_services] = lambda: mock_svc

    return app, mock_svc


@pytest.fixture
def client():
    app, mock_svc = _build_app()
    with TestClient(app) as tc:
        yield tc, mock_svc


def _auth(kwargs=None):
    if kwargs is None:
        kwargs = {}
    kwargs.setdefault("headers", {})["Authorization"] = "Bearer valid-token"
    return kwargs


class TestLlamaFactoryRouter:

    def test_list_models_success(self, client):
        tc, mock_svc = client
        from src.services.llamafactory_service import LlamaFactoryModelsResponse
        mock_svc.llamafactory.return_value.list_models.return_value = \
            LlamaFactoryModelsResponse(success=True, models=["gpt-3.5-turbo"])
        resp = tc.get("/llamafactory/models", **_auth())
        assert resp.status_code == 200
        assert resp.json()["models"] == ["gpt-3.5-turbo"]

    def test_list_models_upstream_error(self, client):
        tc, mock_svc = client
        from src.services.llamafactory_service import LlamaFactoryModelsResponse
        mock_svc.llamafactory.return_value.list_models.return_value = \
            LlamaFactoryModelsResponse(error="Connection refused")
        resp = tc.get("/llamafactory/models", **_auth())
        assert resp.status_code == 502
        assert resp.json()["error"] == "Connection refused"

    def test_chat_success(self, client):
        tc, mock_svc = client
        from src.services.llamafactory_service import LlamaFactoryChatResponse
        mock_svc.llamafactory.return_value.chat.return_value = \
            LlamaFactoryChatResponse(success=True, content="Hello!", raw_response={"choices": []})
        resp = tc.post("/llamafactory/chat", json={
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "hi"}],
        }, **_auth())
        assert resp.status_code == 200
        assert resp.json()["content"] == "Hello!"

    def test_chat_upstream_error(self, client):
        tc, mock_svc = client
        from src.services.llamafactory_service import LlamaFactoryChatResponse
        mock_svc.llamafactory.return_value.chat.return_value = \
            LlamaFactoryChatResponse(error="timeout")
        resp = tc.post("/llamafactory/chat", json={
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "hi"}],
        }, **_auth())
        assert resp.status_code == 502
        assert resp.json()["error"] == "timeout"

    def test_chat_requires_auth(self, client):
        tc, _ = client
        resp = tc.post("/llamafactory/chat", json={
            "model": "gpt-3.5-turbo",
            "messages": [{"role": "user", "content": "hi"}],
        })
        assert resp.status_code == 401
