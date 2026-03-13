from datetime import datetime, timedelta, timezone

from strategy.news_filter import news_gate, score_news


def test_news_scoring_detects_keywords_and_matched_items_shape():
    headlines = [
        {"title": "Major exchange issue causes outage", "source": "x"},
        {"title": "Spot ETF inflow continues", "source": "y"},
    ]
    result = score_news(headlines)
    assert result["score"] < 0
    assert "exchange issue" in result["matched_keywords"]
    assert all({"keyword", "weight", "title", "source"}.issubset(item.keys()) for item in result["matched_items"])


def test_timestamp_filtering():
    old_ts = (datetime.now(timezone.utc) - timedelta(minutes=500)).isoformat()
    now_ts = datetime.now(timezone.utc).isoformat()
    headlines = [
        {"title": "exchange issue", "published_ts": old_ts, "source": "x"},
        {"title": "etf inflow", "published_ts": now_ts, "source": "x"},
    ]
    result = score_news(headlines, lookback_minutes=120)
    assert result["score"] == 2


def test_strong_risk_off_blocks_all_entries():
    gate_long = news_gate(-5, "LONG")
    gate_short = news_gate(-5, "SHORT")
    assert gate_long["allowed"] is False
    assert gate_short["allowed"] is False


def test_positive_news_favors_long_without_forcing_trade():
    gate_long = news_gate(4, "LONG")
    gate_short = news_gate(4, "SHORT")
    assert gate_long["allowed"] is True
    assert gate_long["policy"] == "risk_on_long_favorable"
    assert gate_short["allowed"] is True
    assert gate_short["policy"] == "neutral"


def test_mixed_score_remains_neutral_policy():
    gate = news_gate(1, "LONG")
    assert gate["allowed"] is True
    assert gate["policy"] == "neutral"
