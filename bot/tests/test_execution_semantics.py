from unittest.mock import Mock

from bot.config import ExecutionMode, Settings
from bot.execution.order_manager import place_market_order_with_sl_tp
from bot.main import execution_mode_allows_orders


SYMBOL_FILTERS = {
    "LOT_SIZE": {"minQty": "0.001", "maxQty": "100", "stepSize": "0.001"},
    "PRICE_FILTER": {"tickSize": "0.1"},
}


def test_dry_run_places_no_orders():
    adapter = Mock()

    out = place_market_order_with_sl_tp(
        adapter=adapter,
        symbol="BTCUSDT",
        side="LONG",
        qty=0.123,
        sl=62000.0,
        tp=64000.0,
        execution_mode=ExecutionMode.TESTNET_AUTO,
        enable_live_trading=False,
        symbol_filters=SYMBOL_FILTERS,
        dry_run=True,
    )

    assert out["dry_run"] is True
    assert "entry_payload" in out
    assert len(out["protective_payloads"]) == 2
    assert out["validated"] is True
    adapter.create_futures_order.assert_not_called()


def test_testnet_auto_not_forced_into_dry_run():
    st = Settings(EXECUTION_MODE="testnet_auto", BINANCE_TESTNET=True)
    assert st.execution_mode == ExecutionMode.TESTNET_AUTO
    assert st.enable_dry_run is False


def test_place_market_order_with_sl_tp_real_path_calls_entry_and_protective_orders():
    adapter = Mock()
    adapter.create_futures_order.side_effect = [
        {"orderId": 1},
        {"orderId": 2},
        {"orderId": 3},
    ]

    out = place_market_order_with_sl_tp(
        adapter=adapter,
        symbol="BTCUSDT",
        side="LONG",
        qty=0.123,
        sl=62000.0,
        tp=64000.0,
        execution_mode=ExecutionMode.TESTNET_AUTO,
        enable_live_trading=False,
        symbol_filters=SYMBOL_FILTERS,
        dry_run=False,
    )

    assert out["entry"]["orderId"] == 1
    assert out["sl"]["orderId"] == 2
    assert out["tp"]["orderId"] == 3
    assert adapter.create_futures_order.call_count == 3


def test_mixed_entry_test_and_real_protective_behavior_no_longer_exists():
    adapter = Mock()
    adapter.client = Mock()

    place_market_order_with_sl_tp(
        adapter=adapter,
        symbol="BTCUSDT",
        side="LONG",
        qty=0.123,
        sl=62000.0,
        tp=64000.0,
        execution_mode=ExecutionMode.TESTNET_AUTO,
        enable_live_trading=False,
        symbol_filters=SYMBOL_FILTERS,
        dry_run=True,
    )

    adapter.client.futures_create_test_order.assert_not_called()
    adapter.create_futures_order.assert_not_called()


def test_alert_modes_do_not_execute():
    assert execution_mode_allows_orders("baseline_alert_only", ExecutionMode.TESTNET_AUTO) is False
    assert execution_mode_allows_orders("ai_shadow", ExecutionMode.TESTNET_AUTO) is False
    assert execution_mode_allows_orders("baseline_testnet_auto", ExecutionMode.ALERT_ONLY) is False
    assert execution_mode_allows_orders("baseline_testnet_auto", ExecutionMode.TESTNET_AUTO) is True
