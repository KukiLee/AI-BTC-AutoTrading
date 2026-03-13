"""Thin logging helpers around dataset writer."""

from __future__ import annotations

from dataclasses import asdict, is_dataclass

from .dataset_writer import (
    write_ai_eval_row,
    write_candidate_row,
    write_outcome_label,
    write_policy_decision,
    write_setup_row,
)


def _payload(row):
    if is_dataclass(row):
        return asdict(row)
    return row


def log_setup_feature_row(row, dataset_dir: str) -> bool:
    return write_setup_row(_payload(row), dataset_dir)


def log_candidate_feature_rows(rows: list, dataset_dir: str) -> bool:
    return all(write_candidate_row(_payload(row), dataset_dir) for row in rows)


def log_ai_evaluations(rows: list, dataset_dir: str) -> bool:
    return all(write_ai_eval_row(_payload(row), dataset_dir) for row in rows)


def log_policy_decision(row, dataset_dir: str) -> bool:
    return write_policy_decision(_payload(row), dataset_dir)


def log_outcome_label(row, dataset_dir: str) -> bool:
    return write_outcome_label(_payload(row), dataset_dir)
