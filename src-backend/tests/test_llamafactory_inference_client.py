from unittest.mock import MagicMock, patch

import pytest
from src.adapters.llamafactory_client import LlamaFactoryClient
from src.core.config import Config


def test_llamafactory_config_defaults():
    cfg = Config()

    assert cfg.LLAMAFACTORY_API_PREFIX == "/v1"
    assert cfg.LLAMAFACTORY_TIMEOUT_MS == 30000
    assert cfg.LLAMAFACTORY_RETRIES == 2
    assert cfg.LLAMAFACTORY_DATA_DIR == "data/llamafactory/data"
    assert cfg.LLAMAFACTORY_DATASET_INFO_PATH == "data/llamafactory/data/dataset_info.json"
    assert cfg.LLAMAFACTORY_JOB_DIR == "data/llamafactory/jobs"
    assert cfg.LLAMAFACTORY_TRAIN_COMMAND == "llamafactory-cli"
    assert cfg.LLAMAFACTORY_POLL_INTERVAL_SECONDS == 5


def test_llamafactory_client_facade_slots():
    training = object()
    datasets = object()
    inference = object()

    client = LlamaFactoryClient(
        training=training,
        datasets=datasets,
        inference=inference,
    )

    assert client.training is training
    assert client.datasets is datasets
    assert client.inference is inference


@pytest.fixture
def inference_client():
    with patch("src.services.interfaces.http_client.httpx.Client") as mock_client_cls:
        mock_http = MagicMock()
        mock_resp = MagicMock()
        mock_resp.is_error = False
        mock_http.get.return_value = mock_resp
        mock_http.request.return_value = MagicMock(is_server_error=False)
        mock_client_cls.return_value = mock_http

        from src.adapters.llamafactory_inference_client import LlamaFactoryInferenceClient

        yield LlamaFactoryInferenceClient(), mock_http


def test_inference_health_check_uses_models_endpoint(inference_client):
    client, mock_http = inference_client
    assert client._API_PREFIX == "/v1"
    mock_http.get.assert_called_with("/v1/models")


def test_list_models_uses_bearer_zero(inference_client):
    client, mock_http = inference_client
    client.list_models()
    mock_http.request.assert_called_with(
        method="GET",
        url="/v1/models",
        params=None,
        json=None,
        data=None,
        headers={"Authorization": "Bearer 0"},
        files=None,
    )


def test_chat_completion_posts_openai_payload(inference_client):
    client, mock_http = inference_client
    client.chat(
        model="meta-llama/Meta-Llama-3-8B-Instruct",
        messages=[{"role": "user", "content": "hello"}],
        temperature=0.2,
        max_tokens=64,
    )
    mock_http.request.assert_called_with(
        method="POST",
        url="/v1/chat/completions",
        params=None,
        json={
            "model": "meta-llama/Meta-Llama-3-8B-Instruct",
            "messages": [{"role": "user", "content": "hello"}],
            "temperature": 0.2,
            "max_tokens": 64,
        },
        data=None,
        headers={"Authorization": "Bearer 0"},
        files=None,
    )
