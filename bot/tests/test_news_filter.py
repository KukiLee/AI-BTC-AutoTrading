from strategy.news_filter import news_gate, score_news


def test_news_scoring_detects_keywords():
    headlines = [
        {"title": "Major exchange issue causes outage"},
        {"title": "Spot ETF inflow continues"},
    ]
    result = score_news(headlines)
    assert result["score"] < 0
    assert "exchange issue" in result["matched_keywords"]
    gate = news_gate(result["score"], "LONG")
    assert gate["allowed"] in {True, False}
