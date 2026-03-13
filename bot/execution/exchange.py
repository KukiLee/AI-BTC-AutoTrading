"""Binance USD-M futures adapter isolated from strategy logic."""

from __future__ import annotations

from typing import Any

from binance.client import Client

from ..utils.exceptions import ExchangeAdapterError


class BinanceFuturesAdapter:
    def __init__(self, api_key: str, api_secret: str, testnet: bool = True) -> None:
        self.client = Client(api_key=api_key, api_secret=api_secret, testnet=testnet, ping=False)
        self.testnet = testnet
        self.base_endpoint = "https://demo-fapi.binance.com/fapi" if testnet else self.client.FUTURES_URL
        if testnet:
            self.client.FUTURES_URL = self.base_endpoint
        self._symbol_info_cache: dict[str, dict] = {}

    def _format_error(self, operation: str, exc: Exception, symbol: str | None = None) -> str:
        base = f"Exchange operation failed | op={operation} | endpoint={self.base_endpoint}"
        if symbol:
            base += f" | symbol={symbol}"
        return f"{base}: {exc}"

    def get_futures_balance(self, asset: str = "USDT") -> float:
        try:
            balances = self.client.futures_account_balance()
            for row in balances:
                if row.get("asset") == asset:
                    return float(row["balance"])
            raise ExchangeAdapterError(
                f"Exchange operation failed | op=get_futures_balance | endpoint={self.base_endpoint} | asset={asset}: Asset not found in futures balance"
            )
        except Exception as exc:
            raise ExchangeAdapterError(self._format_error("get_futures_balance", exc)) from exc

    def get_klines(self, symbol: str, interval: str, limit: int = 500) -> list[list[Any]]:
        try:
            return self.client.futures_klines(symbol=symbol, interval=interval, limit=limit)
        except Exception as exc:
            raise ExchangeAdapterError(self._format_error("get_klines", exc, symbol=symbol)) from exc

    def get_open_positions(self, symbol: str) -> list[dict]:
        try:
            positions = self.client.futures_position_information(symbol=symbol)
            return [p for p in positions if float(p.get("positionAmt", 0.0)) != 0.0]
        except Exception as exc:
            raise ExchangeAdapterError(self._format_error("get_open_positions", exc, symbol=symbol)) from exc

    def get_exchange_info(self) -> dict:
        try:
            return self.client.futures_exchange_info()
        except Exception as exc:
            raise ExchangeAdapterError(self._format_error("get_exchange_info", exc)) from exc

    def get_symbol_info(self, symbol: str) -> dict:
        if symbol in self._symbol_info_cache:
            return self._symbol_info_cache[symbol]
        try:
            info = self.get_exchange_info()
            symbols = info.get("symbols", [])
            if not isinstance(symbols, list):
                raise ExchangeAdapterError(
                    f"Exchange operation failed | op=get_symbol_info | endpoint={self.base_endpoint} | symbol={symbol}: Invalid exchange info payload (symbols is not a list)"
                )
            matched = next(
                (row for row in symbols if isinstance(row, dict) and row.get("symbol") == symbol),
                None,
            )
            if matched is None:
                raise ExchangeAdapterError(
                    f"Exchange operation failed | op=get_symbol_info | endpoint={self.base_endpoint} | symbol={symbol}: Symbol metadata not found"
                )
            self._symbol_info_cache[symbol] = matched
            return matched
        except ExchangeAdapterError:
            raise
        except Exception as exc:
            raise ExchangeAdapterError(self._format_error("get_symbol_info", exc, symbol=symbol)) from exc

    def get_symbol_filters(self, symbol: str) -> dict:
        symbol_info = self.get_symbol_info(symbol)
        raw_filters = symbol_info.get("filters", [])
        if not isinstance(raw_filters, list):
            raw_filters = []
        filters = {
            f.get("filterType", "UNKNOWN"): f
            for f in raw_filters
            if isinstance(f, dict)
        }
        expected_filter_types = ("PRICE_FILTER", "LOT_SIZE", "MARKET_LOT_SIZE", "MIN_NOTIONAL")
        min_notional = filters.get("MIN_NOTIONAL") or filters.get("NOTIONAL")
        missing = [
            filter_type
            for filter_type in expected_filter_types
            if (filter_type == "MIN_NOTIONAL" and min_notional is None)
            or (filter_type != "MIN_NOTIONAL" and filters.get(filter_type) is None)
        ]
        return {
            "symbol": symbol,
            "PRICE_FILTER": filters.get("PRICE_FILTER"),
            "LOT_SIZE": filters.get("LOT_SIZE"),
            "MARKET_LOT_SIZE": filters.get("MARKET_LOT_SIZE"),
            "MIN_NOTIONAL": min_notional,
            "is_partial": len(missing) > 0,
            "missing_filter_types": missing,
            "raw": symbol_info,
        }

    def get_mark_price(self, symbol: str) -> float:
        try:
            row = self.client.futures_mark_price(symbol=symbol)
            return float(row.get("markPrice"))
        except Exception as exc:
            raise ExchangeAdapterError(self._format_error("get_mark_price", exc, symbol=symbol)) from exc

    def get_ticker_price(self, symbol: str) -> float:
        """Return the latest traded ticker price from futures_symbol_ticker (not mark price)."""
        try:
            row = self.client.futures_symbol_ticker(symbol=symbol)
            return float(row.get("price"))
        except Exception as exc:
            raise ExchangeAdapterError(self._format_error("get_ticker_price", exc, symbol=symbol)) from exc

    def create_futures_order(self, **kwargs: Any) -> dict:
        try:
            return self.client.futures_create_order(**kwargs)
        except Exception as exc:
            symbol = kwargs.get("symbol", "UNKNOWN")
            raise ExchangeAdapterError(self._format_error("create_futures_order", exc, symbol=symbol)) from exc
