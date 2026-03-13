"""Market data fetch and normalization helpers."""

from __future__ import annotations

import pandas as pd

from execution.exchange import BinanceFuturesAdapter
from utils.exceptions import DataValidationError

KLINE_COLUMNS = [
    "open_time",
    "open",
    "high",
    "low",
    "close",
    "volume",
    "close_time",
    "quote_asset_volume",
    "number_of_trades",
    "taker_buy_base_asset_volume",
    "taker_buy_quote_asset_volume",
    "ignore",
]


def _to_df(raw: list[list], min_rows: int = 220) -> pd.DataFrame:
    if not raw:
        raise DataValidationError("Empty kline response")

    df = pd.DataFrame(raw, columns=KLINE_COLUMNS)
    keep = ["open_time", "open", "high", "low", "close", "volume", "close_time"]
    df = df[keep].copy()
    for col in ["open", "high", "low", "close", "volume"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")

    df["open_time"] = pd.to_datetime(df["open_time"], unit="ms", utc=True)
    df["close_time"] = pd.to_datetime(df["close_time"], unit="ms", utc=True)
    df = df.sort_values("open_time").reset_index(drop=True)

    if df.empty or len(df) < min_rows:
        raise DataValidationError(f"Insufficient rows for indicator stack: got {len(df)}, need >= {min_rows}")
    if df[["open", "high", "low", "close"]].isna().any().any():
        raise DataValidationError("Found NaN in critical OHLC fields")
    return df


def fetch_multi_timeframe_data(adapter: BinanceFuturesAdapter, symbol: str) -> dict[str, pd.DataFrame]:
    return {
        "15m": _to_df(adapter.get_klines(symbol=symbol, interval="15m", limit=500)),
        "1h": _to_df(adapter.get_klines(symbol=symbol, interval="1h", limit=500)),
        "4h": _to_df(adapter.get_klines(symbol=symbol, interval="4h", limit=500)),
    }
