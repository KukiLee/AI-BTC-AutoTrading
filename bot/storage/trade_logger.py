"""Thin logging helpers around dataset writer."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass

from .dataset_writer import write_ai_eval_row, write_outcome_row, write_setup_row


def _payload(row):
    if is_dataclass(row):
        return asdict(row)
    return row


def log_setup_row(row, dataset_dir: str) -> bool:
    return write_setup_row(_payload(row), dataset_dir)


def log_ai_evaluation(row, dataset_dir: str) -> bool:
    return write_ai_eval_row(_payload(row), dataset_dir)


def log_outcome_label(row, dataset_dir: str) -> bool:
    return write_outcome_row(_payload(row), dataset_dir)
