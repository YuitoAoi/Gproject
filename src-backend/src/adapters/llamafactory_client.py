from typing import Any


class LlamaFactoryClient:
    """LlamaFactory 编排门面客户端。"""

    def __init__(
        self,
        *,
        training: Any,
        datasets: Any,
        inference: Any,
        export: Any = None,
    ) -> None:
        self.training = training
        self.datasets = datasets
        self.inference = inference
        self.export = export
