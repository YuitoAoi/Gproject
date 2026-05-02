"""数据集清洗服务 —— 纯业务逻辑，不依赖 Celery。

每种清洗算子为独立方法，可由 Celery task 或同步测试直接调用。
"""
from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Dict, List

from src.core.dataset import Dataset
from src.services.dataset_process_service import CleanConfig, FieldMapping


class DatasetCleanService:
    """数据集清洗 — 将原始文件按 CleanConfig 变换为 LLaMA-Factory 标准格式。"""

    def __init__(self, file_repo=None):
        self._file_repo = file_repo

    # ── 入口 ──────────────────────────────────────────────────

    def execute(
        self, dataset: Dataset, config: CleanConfig, progress_callback=None
    ) -> Dict[str, Any]:
        """执行完整清洗流水线，返回统计信息。

        progress_callback(stage, progress, message) 用于上报进度。
        """
        file_path = dataset.meta.file_path
        rows = self._load(file_path, dataset.meta.format)
        stats = {"original_rows": len(rows)}

        def _progress(stage, pct, msg):
            if progress_callback:
                progress_callback(stage, pct, msg)

        _progress("loading", 0.0, f"Loaded {len(rows)} rows from {file_path}")

        # 1. 字段映射
        if config.field_mapping:
            rows = self._apply_field_mapping(rows, config.field_mapping)
            _progress("field_mapping", 0.10, f"Mapped {len(config.field_mapping)} fields")

        # 2. 基础过滤
        if config.basic_filtering.enabled:
            before = len(rows)
            rows = self._apply_basic_filtering(rows, config.basic_filtering)
            stats["filtered_out"] = before - len(rows)
            _progress("filtering", 0.25, f"Filtered: {before} → {len(rows)} rows")

        # 3. 文本格式化
        if config.text_formatting.enabled:
            rows = self._apply_text_formatting(rows, config.text_formatting)
            _progress("formatting", 0.40, "Text formatting applied")

        # 4. 隐私脱敏
        if config.pii_masking.enabled:
            rows = self._apply_pii_masking(rows, config.pii_masking)
            _progress("pii_masking", 0.55, "PII masking applied")

        # 5. 去重
        if config.deduplication.enabled:
            before = len(rows)
            rows = self._apply_deduplication(rows, config.deduplication)
            stats["duplicates_removed"] = before - len(rows)
            _progress("deduplication", 0.75, f"Dedup: {before} → {len(rows)} rows")

        stats["final_rows"] = len(rows)
        _progress("done", 1.0, f"Cleaning complete: {stats['original_rows']} → {stats['final_rows']} rows")

        return {"rows": rows, "stats": stats}

    # ── 算子实现 ──────────────────────────────────────────────

    def _load(self, file_path: str, format: str) -> List[Dict[str, Any]]:
        if format == "csv":
            import pandas as pd
            df = pd.read_csv(file_path)
            return df.to_dict(orient="records")
        elif format == "xlsx":
            import pandas as pd
            df = pd.read_excel(file_path)
            return df.to_dict(orient="records")
        elif format in ("json", "jsonl"):
            with open(file_path, "r", encoding="utf-8") as f:
                data = json.load(f)
            if isinstance(data, list):
                return data
            return [data]
        else:
            raise ValueError(f"Unsupported format: {format}")

    def _apply_field_mapping(
        self, rows: List[Dict], mappings: List[FieldMapping]
    ) -> List[Dict]:
        result = []
        for row in rows:
            mapped = {}
            for m in mappings:
                value = row.get(m.source_column, "")
                mapped[m.target_field] = str(value) if value is not None else ""
            # 保留未映射的原始字段
            for k, v in row.items():
                if k not in {m.source_column for m in mappings}:
                    if k not in mapped:
                        mapped[k] = v
            result.append(mapped)
        return result

    def _apply_basic_filtering(
        self, rows: List[Dict], config
    ) -> List[Dict]:
        result = []
        for row in rows:
            # 剔除空白行
            if config.remove_empty:
                if all(str(v).strip() == "" for v in row.values()):
                    continue
            # 过滤短文本
            if config.min_text_length:
                texts = [str(v) for v in row.values()]
                if all(len(t) < config.min_text_length for t in texts):
                    continue
            result.append(row)
        return result

    def _apply_text_formatting(
        self, rows: List[Dict], config
    ) -> List[Dict]:
        for row in rows:
            for k, v in row.items():
                if isinstance(v, str):
                    if config.remove_html:
                        v = re.sub(r"<[^>]+>", "", v)
                    if config.normalize_unicode:
                        v = self._full_to_half(v)
                    row[k] = v
        return rows

    @staticmethod
    def _full_to_half(text: str) -> str:
        result = []
        for ch in text:
            code = ord(ch)
            if 0xFF01 <= code <= 0xFF5E:
                result.append(chr(code - 0xFEE0))
            elif code == 0x3000:
                result.append(" ")
            else:
                result.append(ch)
        return "".join(result)

    def _apply_pii_masking(
        self, rows: List[Dict], config
    ) -> List[Dict]:
        patterns = {}
        if config.phone:
            patterns["phone"] = (re.compile(r"1[3-9]\d{9}"), "[MASK_PHONE]")
        if config.email:
            patterns["email"] = (
                re.compile(r"[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}"),
                "[MASK_EMAIL]",
            )
        if config.id_card:
            patterns["id_card"] = (
                re.compile(r"\d{17}[\dXx]"),
                "[MASK_IDCARD]",
            )
        if config.bank_card:
            patterns["bank_card"] = (
                re.compile(r"\d{16,19}"),
                "[MASK_BANKCARD]",
            )

        for row in rows:
            for k, v in row.items():
                if isinstance(v, str):
                    for _, (pattern, replacement) in patterns.items():
                        v = pattern.sub(replacement, v)
                    row[k] = v
        return rows

    def _apply_deduplication(
        self, rows: List[Dict], config
    ) -> List[Dict]:
        if config.method == "exact":
            seen = set()
            result = []
            for row in rows:
                key = hashlib.md5(
                    json.dumps(row, sort_keys=True, ensure_ascii=False).encode()
                ).hexdigest()
                if key not in seen:
                    seen.add(key)
                    result.append(row)
            return result

        # MinHash 简化实现：基于文本内容的 Jaccard 近似
        if config.method == "minhash":
            threshold = config.threshold
            result = []
            for row in rows:
                is_dup = False
                text = " ".join(str(v) for v in row.values())
                sig = self._minhash_signature(text)
                for existing_sig in [self._minhash_signature(
                    " ".join(str(v) for v in r.values())
                ) for r in result]:
                    if self._signature_similarity(sig, existing_sig) >= threshold:
                        is_dup = True
                        break
                if not is_dup:
                    result.append(row)
            return result

        return rows

    @staticmethod
    def _minhash_signature(text: str, num_hashes: int = 128) -> List[int]:
        """简化的 MinHash 签名。"""
        sig = []
        for i in range(num_hashes):
            h = hashlib.sha256(f"{i}:{text}".encode()).hexdigest()
            sig.append(int(h[:8], 16))
        return sig

    @staticmethod
    def _signature_similarity(sig1: List[int], sig2: List[int]) -> float:
        matches = sum(1 for a, b in zip(sig1, sig2) if a == b)
        return matches / len(sig1)
