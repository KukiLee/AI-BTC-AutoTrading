"""Dataset file appender utilities (JSONL)."""

from __future__ import annotations

import json
from dataclasses import asdict, is_dataclass
from datetime import datetime, timezone
from pathlib import Path

from ..utils.logger import get_logger


def _normalize_payload(row) -> dict:
    if is_dataclass(row):
        return asdict(row)
    if isinstance(row, dict):
        return row
    raise TypeError(f"Unsupported row type: {type(row).__name__}")


def _daily_file(dataset_dir: str, prefix: str) -> Path:
    day = datetime.now(timezone.utc).date().isoformat()
    return Path(dataset_dir) / f"{prefix}_{day}.jsonl"


def _append_jsonl(payload: dict, path: Path) -> bool:
    logger = get_logger()
    try:
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as f:
            f.write(json.dumps(payload, ensure_ascii=False, default=str) + "\n")
        return True
    except Exception as exc:
        logger.error(f"Dataset write failed ({path}): {type(exc).__name__}: {exc}")
        return False


def write_setup_row(row, dataset_dir: str) -> bool:
    return _append_jsonl(_normalize_payload(row), _daily_file(dataset_dir, "setups"))


def write_ai_eval_row(row, dataset_dir: str) -> bool:
    return _append_jsonl(_normalize_payload(row), _daily_file(dataset_dir, "ai_evals"))


def write_outcome_row(row, dataset_dir: str) -> bool:
    return _append_jsonl(_normalize_payload(row), _daily_file(dataset_dir, "outcomes"))
