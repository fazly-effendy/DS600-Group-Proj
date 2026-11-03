# Feature 1 – local check with live Yahoo Finance data (4 Nov 2026)

| Item | Value |
|---|---|
| Feature | Lesson 4, Feature 1: one screen with financials, news and price/ratings; numbers in M/B; news with summary and source |
| Commit tested | `79e0311` (branch `feature/news-ratings`) |
| Where | Fazly's laptop, `flask --app wsgi run`, SQLite, `MARKET_DATA_PROVIDER=yahoo`, `DEMO_FALLBACK=false` |
| When | 4 Nov 2026, about 01:20–01:40 SGT |
| Who | Run by Fazly Effendy; screenshots reviewed by Claude |
| Not covered | AWS (to be repeated on the deployed stack with its own evidence) |

## Runs

1. **AAPL, MSFT, D05.SI**, period 1y: `run1_01.jpg` … `run1_07.jpg`
2. **JPM, BAC**, period 1y: `run2_01.jpg` … `run2_05.jpg`

## What the screenshots show

| Check | Result | Evidence |
|---|---|---|
| Live data, no "demo data" banner | Pass | No banner in any screenshot |
| Key financials in M/B, latest fiscal year | Pass | e.g. Apple FY2025 revenue 416.2B, net income 112.0B; Microsoft FY2026 (June year end) 331.8B; DBS 22.9B (`run1_01`, `run1_02`) |
| Core row: revenue growth, net margin, D/E | Pass | Shown for all five companies; D/E marked "not meaningful for banks" for D05.SI, JPM and BAC (`run1_02`, `run2_02`) |
| Analyst ratings and price targets | Pass | Counts, consensus, mean target and upside for all five, incl. D05.SI (17 analysts, SGD 79.24) (`run1_02`, `run1_03`, `run2_02`, `run2_03`) |
| News: headline link, source, date | Pass | Every article shows "Source: … · date"; RSS items say "publisher not given" |
| News: source's summary or the explicit note | Pass | Summaries labelled "Summary from Yahoo Finance RSS"; one BAC item shows "No summary provided by the source" (`run2_04`) |
| News relevance | Partial | DBS, JPM, BAC and Apple articles are about the company. Two Microsoft items are market-research press releases that only list Microsoft among many companies (`run1_04`, `run1_05`); one JPM item is an ETF trade note (`run2_04`) |

## Observations

- Yahoo's per-ticker news feed returned nothing for all five tickers; every article came from the fallback (Yahoo search filtered for relevance, plus Yahoo's RSS feed). The page says so above each list.
- Long summaries are cut at about 400 characters and end with "…"; the wording is the source's.
