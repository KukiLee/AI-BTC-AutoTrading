"""Binance USD-M futures adapter isolated from strategy logic."""

from __future__ import annotations

from typing import Any

from binance.client import Client

from utils.exceptions import ExchangeAdapterError


class BinanceFuturesAdapter:
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True) -> None:
        self.client = Client(api_key=api_key, api_secret=api_secret, testnet=testnet)
        self.testnet = testnet
        self.base_endpoint = "https://demo-fapi.binance.com/fapi" if testnet else self.client.FUTURES_URL
        if testnet:
            self.client.FUTURES_URL = self.base_endpoint
        self._symbol_info_cache: dict[str, dict] = {}

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
            raise ExchangeAdapterError(
                f"Failed to fetch exchange info | endpoint={self.base_endpoint}: {exc}"
            ) from exc

    def get_symbol_info(self, symbol: str) -> dict:
        if symbol in self._symbol_info_cache:
            return self._symbol_info_cache[symbol]
        info = self.get_exchange_info()
        matched = next((row for row in info.get("symbols", []) if row.get("symbol") == symbol), None)
        if matched is None:
            raise ExchangeAdapterError(
                f"Symbol metadata not found | endpoint={self.base_endpoint} | symbol={symbol}"
            )
        self._symbol_info_cache[symbol] = matched
        return matched

    def get_symbol_filters(self, symbol: str) -> dict:
        symbol_info = self.get_symbol_info(symbol)
        filters = {f.get("filterType", "UNKNOWN"): f for f in symbol_info.get("filters", [])}
        return {
            "symbol": symbol,
            "PRICE_FILTER": filters.get("PRICE_FILTER"),
            "LOT_SIZE": filters.get("LOT_SIZE"),
            "MARKET_LOT_SIZE": filters.get("MARKET_LOT_SIZE"),
            "MIN_NOTIONAL": filters.get("MIN_NOTIONAL") or filters.get("NOTIONAL"),
            "raw": symbol_info,
        }

    def get_mark_price(self, symbol: str) -> float:
        try:
            row = self.client.futures_mark_price(symbol=symbol)
            return float(row.get("markPrice"))
        except Exception as exc:
            raise ExchangeAdapterError(
                f"Failed to fetch mark price | endpoint={self.base_endpoint} | symbol={symbol}: {exc}"
            ) from exc

    def create_futures_order(self, **kwargs: Any) -> dict:
        try:
            return self.client.futures_create_order(**kwargs)
        except Exception as exc:
            symbol = kwargs.get("symbol", "UNKNOWN")
            order_type = kwargs.get("type", "UNKNOWN")
            raise ExchangeAdapterError(
                f"Failed to create order | endpoint={self.base_endpoint} | symbol={symbol} | type={order_type}: {exc}"
            ) from exc
