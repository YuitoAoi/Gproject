from unittest.mock import MagicMock

from src.core.dataset import Dataset, DatasetMeta


def test_sync_dataset_returns_not_found_when_dataset_missing():
    from src.services.llamafactory_service import LlamaFactoryDatasetSyncRequest, LlamaFactoryService

    dataset_repo = MagicMock()
    dataset_repo.find_by_id.return_value = None
    service = LlamaFactoryService(
        dataset_repo=dataset_repo,
        task_repo=MagicMock(),
        file_repo=MagicMock(),
        llama_client=MagicMock(),
    )

    result = service.sync_dataset(LlamaFactoryDatasetSyncRequest(dataset_id=99), owner_id=1)
    assert not result.success
    assert result.error == "Dataset not found: 99"


def test_sync_dataset_success_returns_alias():
    from src.services.llamafactory_service import LlamaFactoryDatasetSyncRequest, LlamaFactoryService

    dataset = Dataset.new(
        owner_id=7,
        name="demo",
        meta=DatasetMeta(format="jsonl", file_path="data/demo.jsonl", file_size=10),
        status=0,
    )
    dataset.id = 5

    dataset_repo = MagicMock()
    dataset_repo.find_by_id.return_value = dataset
    llama_client = MagicMock()
    llama_client.datasets.sync_dataset.return_value = {
        "dataset_name": "demo_train",
        "file_name": "demo_train.jsonl",
        "target_path": "data/llamafactory/data/demo_train.jsonl",
    }

    service = LlamaFactoryService(
        dataset_repo=dataset_repo,
        task_repo=MagicMock(),
        file_repo=MagicMock(),
        llama_client=llama_client,
    )

    result = service.sync_dataset(LlamaFactoryDatasetSyncRequest(dataset_id=5, dataset_name="demo_train"), owner_id=7)
    assert result.success is True
    assert result.dataset_name == "demo_train"


def test_chat_success_returns_content():
    from src.services.llamafactory_service import LlamaFactoryChatRequest, LlamaFactoryService

    llama_client = MagicMock()
    llama_client.inference.chat.return_value.json.return_value = {
        "id": "chatcmpl-1",
        "choices": [
            {
                "index": 0,
                "message": {"role": "assistant", "content": "Hello from model"},
                "finish_reason": "stop",
            }
        ],
    }

    service = LlamaFactoryService(
        dataset_repo=MagicMock(),
        task_repo=MagicMock(),
        file_repo=MagicMock(),
        llama_client=llama_client,
    )

    result = service.chat(
        LlamaFactoryChatRequest(
            model="test-model",
            messages=[{"role": "user", "content": "hi"}],
        )
    )

    assert result.success is True
    assert result.content == "Hello from model"
    assert result.raw_response == llama_client.inference.chat.return_value.json.return_value


def test_chat_invalid_response_returns_error():
    from src.services.llamafactory_service import LlamaFactoryChatRequest, LlamaFactoryService

    llama_client = MagicMock()
    llama_client.inference.chat.return_value.json.return_value = {"choices": [{}]}

    service = LlamaFactoryService(
        dataset_repo=MagicMock(),
        task_repo=MagicMock(),
        file_repo=MagicMock(),
        llama_client=llama_client,
    )

    result = service.chat(
        LlamaFactoryChatRequest(
            model="test-model",
            messages=[{"role": "user", "content": "hi"}],
        )
    )

    assert result.success is False
    assert result.error is not None
    assert result.error.startswith("Invalid LlamaFactory chat response:")
