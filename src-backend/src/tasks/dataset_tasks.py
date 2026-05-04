"""数据集异步任务 —— Celery 编排层。

不包含业务逻辑。每个任务从 service 层获取逻辑，本层只做：
- 文件装载 / 写入
- 进度上报 (Redis Pub/Sub)
- 数据库状态更新
- 异常处理
"""
from __future__ import annotations

import json
import os
from typing import Any, Dict

import redis

from src.core.config import config
from src.tasks.celery_app import celery_app


def _publish_progress(task_id: str, stage: str, progress: float, message: str):
    """向 Redis Pub/Sub 发布进度（非阻塞，失败不影响主任务）。"""
    try:
        r = redis.Redis.from_url(config.REDIS_URL, decode_responses=True)
        r.publish(
            f"progress:{task_id}",
            json.dumps({"stage": stage, "progress": progress, "message": message}),
        )
        r.close()
    except Exception:
        pass  # 进度上报失败不中断主任务


# ══════════════════════════════════════════════════════════
# 清洗任务
# ══════════════════════════════════════════════════════════

@celery_app.task(name="dataset.clean", bind=True)
def dataset_clean(self, dataset_id: int, config_dict: Dict[str, Any]) -> Dict[str, Any]:
    """执行数据集清洗流水线。

    Args:
        dataset_id: 数据集 ID
        config_dict: CleanConfig.model_dump() 的结果

    Returns:
        {"success": True, "rows_in": N, "rows_out": M, "output_path": str}
    """
    task_id = self.request.id
    output_path = ""

    try:
        from src.services.dataset_clean_service import DatasetCleanService
        from src.services.dataset_process_service import CleanConfig
        from src.db_connections.mysql import MysqlConnection

        _publish_progress(task_id, "start", 0.0, "Task started")

        # 连接数据库
        db_conn = MysqlConnection(config.DATABASE_URL)
        db_conn.start()

        from src.adapters.repositories.mysql_dataset_repo import DatasetRepositoryAdapter
        repo = DatasetRepositoryAdapter(db_conn)

        ds = repo.find(dataset_id)
        if ds is None:
            _publish_progress(task_id, "error", 0.0, f"Dataset {dataset_id} not found")
            return {"success": False, "error": f"Dataset {dataset_id} not found"}

        clean_config = CleanConfig.model_validate(config_dict.get("clean_config", {}))

        # 执行业务逻辑
        svc = DatasetCleanService()
        result = svc.execute(ds, clean_config, progress_callback=lambda s, p, m: _publish_progress(task_id, s, p, m))

        rows = result["rows"]
        stats = result["stats"]

        # 写入清洗后的文件
        output_dir = os.path.join(config.DATA_DIR, "datasets")
        os.makedirs(output_dir, exist_ok=True)
        base_name = os.path.splitext(os.path.basename(ds.meta.file_path))[0]
        output_path = os.path.join(output_dir, f"{base_name}_cleaned.json")

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(rows, f, ensure_ascii=False, indent=2)

        _publish_progress(task_id, "done", 1.0,
                          f"Complete: {stats['original_rows']} → {stats['final_rows']} rows")

        db_conn.dispose()

        return {
            "success": True,
            "rows_in": stats["original_rows"],
            "rows_out": stats["final_rows"],
            "filtered_out": stats.get("filtered_out", 0),
            "duplicates_removed": stats.get("duplicates_removed", 0),
            "output_path": output_path,
        }

    except Exception as exc:
        _publish_progress(task_id, "error", 0.0, str(exc))
        return {"success": False, "error": str(exc), "output_path": output_path}


# ══════════════════════════════════════════════════════════
# 格式转换任务
# ══════════════════════════════════════════════════════════

@celery_app.task(name="dataset.convert", bind=True)
def dataset_convert(self, dataset_id: int, target_format: str) -> Dict[str, Any]:
    """将数据集转换为 LLaMA-Factory 格式（Alpaca / ShareGPT）。

    Args:
        dataset_id: 数据集 ID
        target_format: "alpaca" | "sharegpt"

    Returns:
        {"success": True, "output_path": str, "samples": int}
    """
    task_id = self.request.id
    output_path = ""

    try:
        _publish_progress(task_id, "start", 0.0, f"Converting to {target_format}")

        from src.db_connections.mysql import MysqlConnection

        db_conn = MysqlConnection(config.DATABASE_URL)
        db_conn.start()

        from src.adapters.repositories.mysql_dataset_repo import DatasetRepositoryAdapter
        repo = DatasetRepositoryAdapter(db_conn)

        ds = repo.find(dataset_id)
        if ds is None:
            return {"success": False, "error": f"Dataset {dataset_id} not found"}

        # 加载源数据
        file_path = ds.meta.file_path
        if file_path.endswith(".csv"):
            import pandas as pd
            df = pd.read_csv(file_path)
            rows = df.to_dict(orient="records")
        elif file_path.endswith(".json"):
            with open(file_path, "r", encoding="utf-8") as f:
                rows = json.load(f)
        else:
            return {"success": False, "error": f"Unsupported format: {ds.meta.format}"}

        _publish_progress(task_id, "converting", 0.3, f"Loaded {len(rows)} rows")

        # 转换
        output_dir = os.path.join(config.DATA_DIR, "datasets")
        os.makedirs(output_dir, exist_ok=True)
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        output_path = os.path.join(output_dir, f"{base_name}_{target_format}.json")

        if target_format == "alpaca":
            converted = []
            for row in rows:
                item = {
                    "instruction": str(row.get("instruction", row.get("Q", ""))),
                    "input": str(row.get("input", "")),
                    "output": str(row.get("output", row.get("A", ""))),
                }
                converted.append(item)
        elif target_format == "sharegpt":
            converted = []
            for row in rows:
                item = {"conversations": [
                    {"from": "human", "value": str(row.get("instruction", row.get("Q", "")))},
                    {"from": "gpt", "value": str(row.get("output", row.get("A", "")))},
                ]}
                converted.append(item)
        else:
            return {"success": False, "error": f"Unknown target format: {target_format}"}

        with open(output_path, "w", encoding="utf-8") as f:
            json.dump(converted, f, ensure_ascii=False, indent=2)

        _publish_progress(task_id, "done", 1.0, f"Converted {len(converted)} samples to {target_format}")

        db_conn.dispose()

        return {
            "success": True,
            "output_path": output_path,
            "samples": len(converted),
        }

    except Exception as exc:
        _publish_progress(task_id, "error", 0.0, str(exc))
        return {"success": False, "error": str(exc)}
