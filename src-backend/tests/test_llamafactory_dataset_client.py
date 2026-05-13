import json

from src.core.dataset import Dataset, DatasetMeta
from src.adapters.repositories.windows_file_repo import WindowsFileRepository


def test_sync_dataset_copies_file_and_updates_dataset_info(tmp_path):
    source = tmp_path / "source.jsonl"
    source.write_text('{"instruction":"hi","output":"there"}\n', encoding="utf-8")
    dataset = Dataset.new(
        owner_id=1,
        name="demo",
        meta=DatasetMeta(format="jsonl", file_path=str(source), file_size=source.stat().st_size),
        status=0,
    )
    file_repo = WindowsFileRepository()

    from src.adapters.llamafactory_dataset_client import LlamaFactoryDatasetClient

    client = LlamaFactoryDatasetClient(
        file_repo=file_repo,
        data_dir=str(tmp_path / "lf_data"),
        dataset_info_path=str(tmp_path / "lf_data" / "dataset_info.json"),
    )
    result = client.sync_dataset(dataset=dataset, dataset_name="demo_train")

    copied = tmp_path / "lf_data" / "demo_train.jsonl"
    assert copied.exists()
    info = json.loads((tmp_path / "lf_data" / "dataset_info.json").read_text(encoding="utf-8"))
    assert result["dataset_name"] == "demo_train"
    assert info["demo_train"]["file_name"] == "demo_train.jsonl"
