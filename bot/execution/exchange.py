"""Binance USD-M futures adapter isolated from strategy logic."""

from __future__ import annotations

from typing import Any

from binance.client import Client

from utils.exceptions import ExchangeAdapterError


class BinanceFuturesAdapter:
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True) -> None:
        self.client = Client(api_key=api_key, api_secret=api_secret)
        if testnet:
            self.client.FUTURES_URL = "https://testnet.binancefuture.com/fapi"

    def get_futures_balance(self, asset: str = "USDT") -> float:
        try:
            balances = self.client.futures_account_balance()
            for row in balances:
                if row.get("asset") == asset:
                    return float(row["balance"])
            raise ExchangeAdapterError(f"Asset {asset} not found in futures balance")
        except Exception as exc:
            raise ExchangeAdapterError(f"Failed to fetch futures balance: {exc}") from exc

    def get_klines(self, symbol: str, interval: str, limit: int = 500) -> list[list[Any]]:
        try:
            return self.client.futures_klines(symbol=symbol, interval=interval, limit=limit)
        except Exception as exc:
            raise ExchangeAdapterError(f"Failed to fetch klines {symbol}/{interval}: {exc}") from exc

    def get_open_positions(self, symbol: str) -> list[dict]:
        try:
            positions = self.client.futures_position_information(symbol=symbol)
            return [p for p in positions if float(p.get("positionAmt", 0.0)) != 0.0]
        except Exception as exc:
            raise ExchangeAdapterError(f"Failed to fetch open positions: {exc}") from exc

    def get_exchange_info(self) -> dict:
        try:
            return self.client.futures_exchange_info()
        except Exception as exc:
            raise ExchangeAdapterError(f"Failed to fetch exchange info: {exc}") from exc

    def create_futures_order(self, **kwargs: Any) -> dict:
        try:
            return self.client.futures_create_order(**kwargs)
        except Exception as exc:
            raise ExchangeAdapterError(f"Failed to create order: {exc}") from exc
