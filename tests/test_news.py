"""Feature 1: news with a summary and a source citation, analyst ratings and
key financials on the Compare page.

No test touches the network: yfinance and the RSS feed are replaced by fakes.
Rules being tested: summaries are never generated (a missing one stays None and
the page says so), every article keeps its publisher, date and link, unrelated
articles are filtered out, and demo mode never shows invented headlines or ratings.
"""
from pathlib import Path

import pandas as pd
import pytest

from app import news
from app.market import DemoProvider, YahooProvider, build_fundamental_rows

ROOT = Path(__file__).resolve().parents[1]

# ---- fake Yahoo data -------------------------------------------------------

NEW_FORMAT = {  # yfinance >= 0.2.50: fields nested under "content"
    "id": "a1",
    "content": {
        "title": "NVIDIA beats estimates on <b>data-centre</b> demand",
        "summary": "Revenue rose 60% &amp; guidance was raised.",
        "pubDate": "2026-10-30T12:00:00Z",
        "provider": {"displayName": "Reuters"},
        "canonicalUrl": {"url": "https://example.com/nvda-beats"},
        "clickThroughUrl": None,
    },
}
OLD_FORMAT = {  # older yfinance and Yahoo search: flat fields
    "uuid": "b2",
    "title": "Apple unveils new MacBook",
    "publisher": "Bloomberg",
    "link": "https://example.com/apple-macbook",
    "providerPublishTime": 1761825600,  # 2025-10-30T12:00:00Z
    "relatedTickers": ["AAPL"],
}
NO_SUMMARY = {
    "content": {
        "title": "Microsoft cloud revenue grows",
        "provider": {"displayName": "CNBC"},
        "canonicalUrl": {"url": "https://example.com/msft"},
        "pubDate": "2026-10-29T08:00:00Z",
    }
}

RSS_XML = b"""<?xml version="1.0"?>
<rss version="2.0"><channel><title>Yahoo</title>
<item><title>Apple unveils new MacBook</title><link>https://example.com/apple-macbook</link>
<description>Apple announced a new laptop line on Thursday.</description>
<pubDate>Thu, 30 Oct 2025 12:00:00 +0000</pubDate><guid>rss-1</guid></item>
<item><title>Apple supplier shares jump</title><link>https://example.com/apple-supplier</link>
<description>Suppliers rallied after the launch.</description>
<pubDate>Fri, 31 Oct 2025 09:00:00 +0000</pubDate><guid>rss-2</guid></item>
<item><title>Stocks close higher as Fed holds rates</title><link>https://example.com/market-wrap</link>
<description>A general market story.</description>
<pubDate>Fri, 31 Oct 2025 21:00:00 +0000</pubDate><guid>rss-3</guid></item>
</channel></rss>"""


class FakeResponse:
    def __init__(self, content=RSS_XML, status=200):
        self.content, self.status = content, status

    def raise_for_status(self):
        if self.status >= 400:
            raise RuntimeError(f"HTTP {self.status}")


def rss_ok(ticker):
    return FakeResponse()


def rss_down(ticker):
    raise ConnectionError("feed unreachable")


def fake_yf(news_items=(), search_items=()):
    class Ticker:
        def __init__(self, symbol):
            self.symbol = symbol

        def get_news(self, count=10, tab="news"):
            return list(news_items)

    class Search:
        def __init__(self, query, max_results=1, news_count=10):
            self.news = list(search_items)

    return type("FakeYF", (), {"Ticker": Ticker, "Search": Search})


# ---- parsing ----------------------------------------------------------------

def test_parses_new_content_format():
    item = news.parse_article(NEW_FORMAT)
    assert item["headline"] == "NVIDIA beats estimates on data-centre demand"  # tags stripped
    assert item["summary"] == "Revenue rose 60% & guidance was raised."  # entities decoded, wording kept
    assert item["publisher"] == "Reuters"
    assert item["url"] == "https://example.com/nvda-beats"
    assert item["published_at"] == "2026-10-30T12:00:00Z"


def test_parses_old_flat_format():
    item = news.parse_article(OLD_FORMAT)
    assert item["headline"] == "Apple unveils new MacBook"
    assert item["publisher"] == "Bloomberg"
    assert item["url"] == "https://example.com/apple-macbook"
    assert item["published_at"] == "2025-10-30T12:00:00Z"
    assert item["summary"] is None


def test_missing_summary_is_never_invented():
    item = news.parse_article(NO_SUMMARY)
    assert item["summary"] is None and item["summary_source"] is None
    # The page states it plainly instead of filling the gap.
    assert news.NO_SUMMARY_TEXT == "No summary provided by the source"
    assert news.NO_SUMMARY_TEXT in (ROOT / "app/static/js/compare.js").read_text()


def test_malformed_items_are_skipped_and_counted():
    items, skipped = news.parse_news([NEW_FORMAT, "junk", {"content": {}}, None, OLD_FORMAT], limit=5)
    assert [i["publisher"] for i in items] == ["Reuters", "Bloomberg"]
    assert skipped == 3


def test_non_http_links_are_dropped():
    item = news.parse_article({"title": "Apple news", "link": "javascript:alert(1)"})
    assert item["url"] is None


# ---- relevance filter ---------------------------------------------------------

def test_mentions_company_by_name_alias_or_ticker():
    assert news.mentions_company("NVIDIA beats estimates", "NVDA", "NVIDIA Corporation")
    assert news.mentions_company("Shares of NVDA rose", "NVDA", "NVIDIA Corporation")
    assert news.mentions_company("DBS profit hits record", "D05.SI", "DBS Group Holdings Ltd")
    assert news.mentions_company("OCBC raises dividend", "O39.SI", "Oversea-Chinese Banking Corp")
    assert not news.mentions_company("Stocks close higher as Fed holds rates", "AAPL", "Apple Inc.")
    assert not news.mentions_company("NVDAX fund launches", "NVDA", "NVIDIA Corporation")


# ---- fetch routes ------------------------------------------------------------

def test_ticker_news_feed_is_used_first():
    out = news.fetch_news(fake_yf(news_items=[NEW_FORMAT]), "NVDA", "NVIDIA Corporation", rss_get=rss_down)
    assert out["status"] == "ok" and out["route"] == "Yahoo Finance news"
    assert len(out["items"]) == 1


def test_search_fallback_filters_and_rss_adds_summary():
    unrelated = {**OLD_FORMAT, "title": "Stocks close higher as Fed holds rates",
                 "link": "https://example.com/other", "relatedTickers": ["AAPL", "MSFT"]}
    other_ticker = {**OLD_FORMAT, "title": "Apple deal with Tesla", "relatedTickers": ["TSLA"]}
    out = news.fetch_news(fake_yf(search_items=[OLD_FORMAT, unrelated, other_ticker]),
                          "AAPL", "Apple Inc.", rss_get=rss_ok)
    assert out["status"] == "ok"
    titles = [a["title"] for a in out["items"]]
    # Kept: the search article (now with the RSS description) and the RSS-only article
    # whose headline names Apple. Dropped: the market wrap and the TSLA-linked article.
    assert titles == ["Apple supplier shares jump", "Apple unveils new MacBook"]
    parsed, _ = news.parse_news(out["items"])
    macbook = next(p for p in parsed if p["headline"] == "Apple unveils new MacBook")
    assert macbook["summary"] == "Apple announced a new laptop line on Thursday."
    assert macbook["summary_source"] == news.RSS_SOURCE
    assert macbook["publisher"] == "Bloomberg"
    supplier = next(p for p in parsed if p["headline"] == "Apple supplier shares jump")
    assert supplier["publisher"] is None and supplier["via"] == news.RSS_SOURCE


def test_rss_failure_still_returns_search_articles_without_summary():
    out = news.fetch_news(fake_yf(search_items=[OLD_FORMAT]), "AAPL", "Apple Inc.", rss_get=rss_down)
    assert out["status"] == "ok" and "RSS feed failed" in out["message"]
    parsed, _ = news.parse_news(out["items"])
    assert parsed[0]["summary"] is None


def test_nothing_found_is_reported_not_invented():
    out = news.fetch_news(fake_yf(), "AAPL", "Apple Inc.", rss_get=rss_down)
    assert out["items"] == [] and out["status"] in {"empty", "error"} and out["message"]


# ---- ratings -----------------------------------------------------------------

def test_latest_ratings_prefers_current_month():
    df = pd.DataFrame({"period": ["0m", "-1m"], "strongBuy": [10, 8], "buy": [20, 19],
                       "hold": [5, 6], "sell": [1, 1], "strongSell": [0, 0]})
    r = news.extract_latest_ratings(df)
    assert r == {"strongBuy": 10, "buy": 20, "hold": 5, "sell": 1, "strongSell": 0, "period": "0m"}
    assert news.extract_latest_ratings(pd.DataFrame()) is None
    assert news.extract_latest_ratings(None) is None


def test_analyst_view_and_upside():
    view = news.extract_analyst_view({"recommendationKey": "strong_buy", "targetMeanPrice": 220.0,
                                      "targetHighPrice": 250.0, "targetLowPrice": 180.0,
                                      "numberOfAnalystOpinions": 40, "recommendationMean": 1.8}, 200.0)
    assert view["recommendation"] == "strong buy" and view["analysts"] == 40
    assert view["upside"] == pytest.approx(0.10)
    assert news.extract_analyst_view({"recommendationKey": "none"}, 100.0) is None


# ---- providers ---------------------------------------------------------------

def test_demo_provider_never_invents_news_or_ratings():
    demo = DemoProvider()
    n = demo.news("AAPL", "Apple Inc.")
    assert n["items"] == [] and n["status"] == "demo" and "never" in n["message"].lower()
    r = demo.ratings("AAPL")
    assert r["counts"] is None and r["view"] is None


def test_yahoo_provider_ratings_with_fake_yfinance():
    class T:
        def __init__(self, s):
            self.info = {"recommendationKey": "buy", "targetMeanPrice": 110.0, "numberOfAnalystOpinions": 12}
            self.recommendations = pd.DataFrame({"period": ["0m"], "strongBuy": [3], "buy": [5],
                                                 "hold": [4], "sell": [0], "strongSell": [0]})

    y = YahooProvider.__new__(YahooProvider)
    y.yf = type("YF", (), {"Ticker": T})
    r = y.ratings("FAKE")
    assert r["counts"]["buy"] == 5 and r["view"]["target_mean"] == 110.0
    assert r["view"]["upside"] is None  # needs a live price; the API adds it


def test_fundamental_rows_keep_debt_and_equity_for_the_financials_table():
    rows = build_fundamental_rows([{"year": 2024, "revenue": 100, "net_income": 10,
                                    "total_debt": 40, "equity": 80}])
    assert rows[0]["total_debt"] == 40 and rows[0]["equity"] == 80


# ---- API and page ------------------------------------------------------------

def test_briefing_api_shape_in_demo_mode(logged_in):
    d = logged_in.get("/api/briefing?tickers=AAPL,D05.SI").get_json()
    assert d["demo_data"] is True
    assert [c["ticker"] for c in d["companies"]] == ["AAPL", "D05.SI"]
    for c in d["companies"]:
        assert c["news"]["items"] == [] and c["news"]["source"] == "demo"
        assert c["ratings"]["counts"] is None
        fin = c["financials"]
        for key in ("year", "revenue", "net_income", "total_debt", "equity",
                    "revenue_growth", "net_margin", "debt_to_equity"):
            assert key in fin
    apple, dbs = d["companies"]
    assert apple["is_bank"] is False and dbs["is_bank"] is True
    assert dbs["financials"]["debt_to_equity"] is not None  # shown for banks, with a note in the page


def test_briefing_api_requires_login_and_valid_tickers(client, logged_in):
    assert client.application.test_client().get("/api/briefing?tickers=AAPL").status_code == 401
    assert logged_in.get("/api/briefing?tickers=").status_code == 400
    assert logged_in.get("/api/briefing?tickers=<script>").status_code == 400


class FakeLiveYahoo:
    """A Yahoo provider with live-looking data, for the API test."""

    name = "yahoo"

    def __init__(self):
        self.demo = DemoProvider()

    def info(self, ticker):
        return {**self.demo.info(ticker), "name": "Apple Inc."}

    def history(self, ticker, period):
        return [("2026-10-30", 190.0), ("2026-10-31", 200.0)]

    def fundamentals(self, ticker):
        return self.demo.fundamentals(ticker)

    def news(self, ticker, name):
        items, skipped = news.parse_news([NEW_FORMAT, NO_SUMMARY])
        return {"items": items, "skipped": skipped, "status": "ok", "route": "Yahoo Finance news", "message": None}

    def ratings(self, ticker):
        return {"counts": {"strongBuy": 1, "buy": 2, "hold": 3, "sell": 0, "strongSell": 0, "period": "0m"},
                "view": {"recommendation": "buy", "target_mean": 220.0, "upside": None}}


def test_briefing_api_with_live_provider(app, logged_in):
    app.extensions["market"].primary = FakeLiveYahoo()
    d = logged_in.get("/api/briefing?tickers=AAPL").get_json()
    c = d["companies"][0]
    assert d["demo_data"] is False and c["news"]["source"] == "yahoo"
    first, second = c["news"]["items"]
    assert first["publisher"] == "Reuters" and first["url"].startswith("https://")
    assert second["summary"] is None
    assert c["ratings"]["view"]["upside"] == pytest.approx(0.10)  # 220 / 200 - 1


def test_compare_page_has_financials_ratings_and_news_sections(logged_in):
    page = logged_in.get("/compare").data
    for marker in (b'id="financials-table"', b'id="ratings-table"', b'id="news-list"'):
        assert marker in page
    js = (ROOT / "app/static/js/compare.js").read_text()
    assert "/api/briefing" in js and "rel=\"noopener noreferrer\"" in js
