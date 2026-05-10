from typing import TYPE_CHECKING, List, Union

from graphgen.bases.base_reader import BaseReader

if TYPE_CHECKING:
    import ray
    from ray.data import Dataset


class XLSXReader(BaseReader):
    """
    Reader for XLSX / Excel files.

    读取每个 sheet 并转为 Ray Dataset。
    与 CSV/JSON Reader 相同，通过 _validate_batch 校验列结构。
    """

    def read(self, input_path: Union[str, List[str]]) -> "Dataset":
        import ray
        import pandas as pd

        paths = input_path if isinstance(input_path, list) else [input_path]
        ds: "Dataset" = ray.data.from_items([])

        for path in paths:
            xl = pd.ExcelFile(path, engine="openpyxl")
            for sheet_name in xl.sheet_names:
                df: pd.DataFrame = xl.parse(sheet_name)
                df["path"] = path
                sheet_ds = ray.data.from_pandas(df)
                ds = ds.union(sheet_ds)

        ds = ds.map_batches(self._validate_batch, batch_format="pandas")
        ds = ds.filter(self._should_keep_item)
        return ds
