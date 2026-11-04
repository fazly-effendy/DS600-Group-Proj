"""News and analyst ratings from Yahoo Finance (Feature 1).

Ported from the reference project (smu-cce-starter-Fazly, src/services/yahoo.py)
without its Streamlit parts. Two kinds of function:

* fetch_* call Yahoo (through the yfinance module passed in, so tests use fakes);
* parse_* / extract_* / mentions_company turn raw data into clean values and
  never touch the network.

Rules: a summary is shown only if the source provides one. Nothing is generated,
paraphrased or guessed; a missing summary stays None and the page says
"No summary provided by the source". Every article keeps its headline,
publisher (when Yahoo gives one), date and link.
"""
from __future__ import annotations

import html
import logging
import math
import re
import xml.etree.ElementTree as ET
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime
from typing import Iterable, Optional

NO_SUMMARY_TEXT = "No summary provided by the source"
RSS_URL = "https://feeds.finance.yahoo.com/rss/2.0/headline"
RSS_SOURCE = "Yahoo Finance RSS"
SUMMARY_LIMIT = 400  # longer summaries are cut at a word boundary and end with "…"

_TAG_PATTERN = re.compile(r"<[^>]+>")

# How headlines refer to companies whose Yahoo name differs from everyday usage.
ALIASES = {
    "GOOGL": ["google"], "GOOG": ["google"], "META": ["facebook"],
    "D05.SI": ["dbs"], "O39.SI": ["ocbc"], "U11.SI": ["uob"],
    "JPM": ["jpmorgan", "jp morgan"], "BAC": ["bank of america", "bofa"],
    "GS": ["goldman sachs", "goldman"], "KO": ["coca-cola", "coke"], "XOM": ["exxon", "exxonmobil"],
}
# Words that do not identify a company on their own.
_NAME_NOISE = {"inc", "incorporated", "corporation", "corp", "company", "co", "ltd", "limited", "plc",
               "holdings", "group", "the", "sa", "nv", "ag", "se", "adr", "class", "a", "b", "c", "com"}
_GENERIC_FIRST_WORDS = {"bank", "first", "general", "united", "american", "international", "global",
                        "national", "new", "advanced", "taiwan", "china", "singapore", "oversea"}


# --------------------------------------------------------------------------
# Small helpers
# --------------------------------------------------------------------------
def clean_number(value) -> Optional[float]:
    if value is None or isinstance(value, bool):
        return None
    try:
        number = float(value)
    except (TypeError, ValueError):
        return None
    return None if math.isnan(number) or math.isinf(number) else number


def _clean_text(value) -> Optional[str]:
    """Strip HTML tags and entities and collapse whitespace. Wording is unchanged."""
    if not value or not isinstance(value, str):
        return None
    text = html.unescape(_TAG_PATTERN.sub(" ", value))
    text = re.sub(r"\s+", " ", text).strip()
    text = re.sub(r" ([.,;:!?])", r"\1", text)
    return text or None


def _shorten(text: Optional[str], limit: int = SUMMARY_LIMIT) -> Optional[str]:
    if text is None or len(text) <= limit:
        return text
    return text[:limit].rsplit(" ", 1)[0].rstrip(" ,.;:") + "…"


def _url_from(value) -> Optional[str]:
    """Yahoo gives URLs as strings or {"url": ...}. Only http(s) links are kept."""
    if isinstance(value, dict):
        value = value.get("url")
    if isinstance(value, str) and value.startswith(("http://", "https://")):
        return value
    return None


def _published_from(content: dict, article: dict) -> Optional[str]:
    for key in ("pubDate", "displayTime"):
        value = content.get(key)
        if isinstance(value, str) and value:
            return value
    epoch = article.get("providerPublishTime")
    if isinstance(epoch, (int, float)):
        return datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
    return None


# --------------------------------------------------------------------------
# Relevance filter
# --------------------------------------------------------------------------
def company_terms(ticker: str, name: Optional[str]) -> tuple[list[str], list[str]]:
    """How a headline can refer to a company: (ticker symbols, lower-case name phrases)."""
    symbol = ticker.upper()
    symbols = {symbol, symbol.split(".")[0]}
    words = [w for w in re.split(r"[^a-z0-9&]+", (name or "").lower()) if w and w not in _NAME_NOISE]
    phrases = set(ALIASES.get(symbol, []))
    if words:
        phrases.add(" ".join(words))
        if len(words[0]) >= 4 and words[0] not in _GENERIC_FIRST_WORDS:
            phrases.add(words[0])
    return sorted(symbols), sorted(phrases)


def mentions_company(text: str, ticker: str, name: Optional[str]) -> bool:
    """True if the text names the company or shows its ticker as a whole word."""
    symbols, phrases = company_terms(ticker, name)
    if any(re.search(rf"(?<![A-Za-z0-9]){re.escape(s)}(?![A-Za-z0-9])", text or "") for s in symbols):
        return True
    lowered = (text or "").lower()
    return any(re.search(rf"\b{re.escape(p)}\b", lowered) for p in phrases)


def _article_text(article: dict) -> str:
    content = article.get("content") if isinstance(article.get("content"), dict) else {}
    return " ".join(str(x) for x in (article.get("title"), article.get("summary"),
                                     content.get("title"), content.get("summary")) if x)


# --------------------------------------------------------------------------
# Yahoo RSS headline feed (has short descriptions, no publisher)
# --------------------------------------------------------------------------
def _rss_get(ticker: str):
    import requests  # installed with yfinance

    return requests.get(RSS_URL, params={"s": ticker, "region": "US", "lang": "en-US"},
                        headers={"User-Agent": "Mozilla/5.0"}, timeout=8)


def _rss_time(value: Optional[str]) -> Optional[int]:
    try:
        return int(parsedate_to_datetime(value).timestamp()) if value else None
    except (TypeError, ValueError, IndexError):
        return None


def fetch_rss(ticker: str, get=_rss_get) -> list[dict]:
    """RSS items in the same flat format as Yahoo search results. Raises on failure."""
    response = get(ticker)
    response.raise_for_status()
    root = ET.fromstring(response.content)
    items = []
    for element in root.findall("./channel/item"):
        fields = {child.tag: (child.text or "").strip() for child in element}
        if not fields.get("title"):
            continue
        items.append({
            "uuid": fields.get("guid") or fields.get("link"),
            "title": fields["title"],
            "link": fields.get("link") or None,
            "providerPublishTime": _rss_time(fields.get("pubDate")),
            "summary": fields.get("description") or None,
            "publisher": None,
            "nimbus_via": RSS_SOURCE,
        })
    return items


def _headline_key(text: Optional[str]) -> str:
    return re.sub(r"[^a-z0-9]", "", (text or "").lower())


def _with_rss(ticker, name, kept, get):
    """Add RSS descriptions to matching search articles, plus RSS-only articles whose
    HEADLINE names the company. Returns (kept, rss_only, problem or None)."""
    try:
        rss = fetch_rss(ticker, get)
    except Exception as exc:
        return kept, [], f"RSS feed failed ({exc.__class__.__name__})"
    by_title = {_headline_key(item["title"]): item for item in rss}
    by_link = {item["link"]: item for item in rss if item["link"]}
    enriched = []
    for article in kept:
        article = dict(article)
        if not _clean_text(article.get("summary")):
            match = by_title.get(_headline_key(article.get("title"))) or by_link.get(article.get("link"))
            if match and match.get("summary"):
                article["summary"] = match["summary"]
                article["nimbus_summary_source"] = RSS_SOURCE
        enriched.append(article)
    kept_titles = {_headline_key(a.get("title")) for a in kept}
    kept_links = {a.get("link") for a in kept if a.get("link")}
    rss_only = [item for item in rss
                if _headline_key(item["title"]) not in kept_titles and item["link"] not in kept_links
                and mentions_company(item["title"], ticker, name)]
    return enriched, rss_only, None


# --------------------------------------------------------------------------
# Fetch news: ticker feed, else search + RSS
# --------------------------------------------------------------------------
class _LogCapture(logging.Handler):
    """yfinance logs some failures instead of raising; collect them."""

    def __init__(self):
        super().__init__(level=logging.WARNING)
        self.messages: list[str] = []

    def emit(self, record):
        self.messages.append(record.getMessage())


def fetch_news(yf, ticker: str, name: Optional[str], count: int = 10, rss_get=None) -> dict:
    """Recent raw news items for a ticker, with an honest account of what happened.

    1. Ticker.get_news(): Yahoo's ticker feed (has summaries).
    2. If empty: Search(ticker).news (publisher, usually no summary), kept only if
       Yahoo links it to this ticker AND it names the company; plus Yahoo's RSS
       feed, which adds descriptions to the same articles and contributes
       articles whose headline names the company.
    Returns {"items", "route", "status": ok|empty|error, "message"}.
    """
    rss_get = rss_get or _rss_get
    capture = _LogCapture()
    logger = logging.getLogger("yfinance")
    logger.addHandler(capture)
    problems: list[str] = []
    try:
        try:
            items = yf.Ticker(ticker).get_news(count=count, tab="news") or []
        except Exception as exc:
            items = []
            problems.append(f"news feed failed ({exc.__class__.__name__})")
        if items:
            return {"items": list(items), "route": "Yahoo Finance news", "status": "ok", "message": None}
        try:
            found = yf.Search(ticker, max_results=1, news_count=count).news or []
        except Exception as exc:
            found = []
            problems.append(f"news search failed ({exc.__class__.__name__})")
        related = [a for a in found if isinstance(a, dict)
                   and ticker.upper() in [str(t).upper() for t in a.get("relatedTickers") or []]]
        about = [a for a in related if mentions_company(_article_text(a), ticker, name)]
        about, rss_only, rss_problem = _with_rss(ticker, name, about, rss_get)
        items = sorted(about + rss_only, key=lambda a: a.get("providerPublishTime") or 0, reverse=True)
        if items:
            used_rss = bool(rss_only) or any(a.get("nimbus_summary_source") for a in about)
            route = ("Yahoo Finance search + RSS" if about and used_rss
                     else "Yahoo Finance search" if about else RSS_SOURCE)
            notes = ["Yahoo's ticker news feed returned nothing, so these come from Yahoo search "
                     "(only articles linked to the ticker that name the company) and Yahoo's RSS feed."]
            if rss_problem:
                notes.append(rss_problem + ".")
            return {"items": items, "route": route, "status": "ok", "message": " ".join(notes)}
        if related or found:
            return {"items": [], "route": None, "status": "empty",
                    "message": f"Yahoo returned {len(found)} search articles, but none both link to "
                               f"{ticker.upper()} and name the company, so none are shown."}
    finally:
        logger.removeHandler(capture)
    problems += [f"yfinance: {m}" for m in capture.messages[:3]]
    if problems:
        return {"items": [], "route": None, "status": "error", "message": "; ".join(problems)}
    return {"items": [], "route": None, "status": "empty",
            "message": "Yahoo returned no articles for this company."}


# --------------------------------------------------------------------------
# Parse news items (both yfinance formats)
# --------------------------------------------------------------------------
def parse_article(article) -> Optional[dict]:
    """One Yahoo news item -> dict, or None if it has no headline.

    Current format nests fields under "content" (title, summary, pubDate,
    provider.displayName, canonicalUrl.url); the older / search format is flat
    (title, publisher, link, providerPublishTime).
    """
    if not isinstance(article, dict):
        return None
    content = article.get("content") if isinstance(article.get("content"), dict) else {}
    headline = _clean_text(content.get("title") or article.get("title"))
    if not headline:
        return None
    summary = (_clean_text(content.get("summary")) or _clean_text(content.get("description"))
               or _clean_text(article.get("summary")))
    provider = content.get("provider") if isinstance(content.get("provider"), dict) else {}
    publisher = provider.get("displayName") or article.get("publisher")
    via = article.get("nimbus_via")
    return {
        "headline": headline,
        "summary": _shorten(summary),
        "summary_source": article.get("nimbus_summary_source") if summary else None,
        "publisher": publisher if isinstance(publisher, str) and publisher else None,
        "published_at": _published_from(content, article),
        "url": (_url_from(content.get("canonicalUrl")) or _url_from(content.get("clickThroughUrl"))
                or _url_from(article.get("link"))),
        "via": via if isinstance(via, str) else None,
    }


def parse_news(raw_news: Optional[Iterable], limit: int = 5) -> tuple[list[dict], int]:
    """Parse up to `limit` items. Returns (items, number of malformed items skipped)."""
    items, skipped = [], 0
    for article in raw_news or []:
        try:
            item = parse_article(article)
        except Exception:
            item = None
        if item is None:
            skipped += 1
            continue
        items.append(item)
        if len(items) >= limit:
            break
    return items, skipped


# --------------------------------------------------------------------------
# Analyst ratings
# --------------------------------------------------------------------------
def extract_latest_ratings(recommendations) -> Optional[dict]:
    """Analyst recommendation counts for the current month ("0m") if available."""
    try:
        import pandas as pd
    except ImportError:  # pragma: no cover
        return None
    if recommendations is None or not isinstance(recommendations, pd.DataFrame) or recommendations.empty:
        return None
    table = recommendations.reset_index(drop=True)
    if "period" in table.columns and (table["period"] == "0m").any():
        row = table[table["period"] == "0m"].iloc[0]
    else:
        row = table.iloc[-1]
    counts = {}
    for column in ("strongBuy", "buy", "hold", "sell", "strongSell"):
        value = clean_number(row.get(column))
        counts[column] = int(value) if value is not None else None
    if all(v is None for v in counts.values()):
        return None
    counts["period"] = str(row.get("period", "latest"))
    return counts


def extract_analyst_view(info: Optional[dict], last_close: Optional[float]) -> Optional[dict]:
    """Consensus recommendation and price targets. Upside = mean target / last close - 1."""
    info = info or {}
    target = clean_number(info.get("targetMeanPrice"))
    analysts = clean_number(info.get("numberOfAnalystOpinions"))
    key = info.get("recommendationKey")
    view = {
        "recommendation": key.replace("_", " ") if isinstance(key, str) and key and key != "none" else None,
        "recommendation_mean": clean_number(info.get("recommendationMean")),  # 1 = strong buy … 5 = sell
        "analysts": int(analysts) if analysts else None,
        "target_mean": target,
        "target_high": clean_number(info.get("targetHighPrice")),
        "target_low": clean_number(info.get("targetLowPrice")),
        "upside": (target / last_close - 1.0) if target and last_close and last_close > 0 else None,
    }
    return view if any(v is not None for v in view.values()) else None
