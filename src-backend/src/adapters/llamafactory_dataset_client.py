import json
from pathlib import Path

from src.core.config import config
from src.core.dataset import Dataset
from src.services.interfaces.file_repository import FileRepository


class LlamaFactoryDatasetClient:
    def __init__(
        self,
        *,
        file_repo: FileRepository,
        data_dir: str | None = None,
        dataset_info_path: str | None = None,
    ) -> None:
        self._file_repo = file_repo
        self._data_dir = Path(data_dir or config.LLAMAFACTORY_DATA_DIR)
        self._dataset_info_path = Path(dataset_info_path or config.LLAMAFACTORY_DATASET_INFO_PATH)

    def sync_dataset(self, *, dataset: Dataset, dataset_name: str | None = None) -> dict[str, str]:
        alias = dataset_name or f"dataset_{dataset.id}"
        ext = Path(dataset.meta.file_path).suffix or ".jsonl"
        target_name = f"{alias}{ext}"
        target_path = self._data_dir / target_name

        self._file_repo.makedirs(str(self._data_dir))
        self._file_repo.copy(dataset.meta.file_path, str(target_path))

        dataset_info = self._read_dataset_info()
        dataset_info[alias] = {"file_name": target_name}
        self._write_dataset_info(dataset_info)
        return {
            "dataset_name": alias,
            "file_name": target_name,
            "target_path": str(target_path),
        }

    def _read_dataset_info(self) -> dict:
        dataset_info_path = str(self._dataset_info_path)
        if not self._file_repo.exists(dataset_info_path):
            return {}
        content = self._file_repo.read(dataset_info_path)
        return json.loads(content.decode("utf-8"))

    def _write_dataset_info(self, dataset_info: dict) -> None:
        self._file_repo.makedirs(str(self._dataset_info_path.parent))
        self._file_repo.over_write(
            str(self._dataset_info_path),
            json.dumps(dataset_info, ensure_ascii=False, indent=2).encode("utf-8"),
        )
