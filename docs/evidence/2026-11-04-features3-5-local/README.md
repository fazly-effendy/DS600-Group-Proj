# Features 3–5 – local acceptance test with live Yahoo Finance data (4 Nov 2026)

| Item | Value |
|---|---|
| Features | Lesson 4, Features 3–5 as specified by Gaurav: save a client-discussion snapshot (Client ID, tickers, discussion date, price at discussion, client interests), retrieve by client and by company, reopen the saved snapshot (never current data) |
| Commit tested | `e5c258b` (branch `feature/discussion-snapshot`) |
| Where | Fazly's laptop, `flask --app wsgi run --port 5001`, SQLite, `MARKET_DATA_PROVIDER=yahoo` |
| When | 4 Nov 2026, about 02:08–02:30 SGT |
| Who | Run by Fazly Effendy with Claude in Chrome as the scripted tester; reviewed by Claude |
| Not covered | AWS / Amazon RDS (step 12 of Gaurav's test, to be run on the deployed stack) |

## Result

**11 of 11 acceptance checks passed.** Full report: [`qa-report.md`](qa-report.md).

| Gaurav's step | Result | Screenshots |
|---|---|---|
| 1–5 Client ID, 2 tickers, compare prices, revenue growth, margin, D/E | Pass | 01–03 |
| 6–7 Client interests, one Save | Pass | 04–07 |
| Saved values equal the Compare page (AAPL 330.81, MSFT 520.92; ratios identical) | Pass | 08–12 |
| Reopen makes no `/api/` requests (incl. the trends panel) | Pass | 13–14 |
| 8–9 Search by client, by `MSFT`, by `apple`; excluded for `NVDA` and a future date | Pass | 15–20 |
| Client page lists the discussion | Pass | 22 |
| Empty client interests refused; single ticker refused | Pass | 23–25 |
| 10–11 Restart the app; record identical | Pass | 26–29 |

## Defect found and fixed

The **Clients list** showed `0` discussions and `—` for "Last spoke" for a client with a saved discussion (screenshots 21, 30); it counted only stock notes. Fixed in commit `7f0bd62` with a regression test.

## Other notes from the run

- Times on the saved page are in UTC (02:09 SGT shows as 18:09 UTC the previous day); the price date is the latest US close. Both are correct but could be shown in local time later.
- Whitespace-only client interests are refused by the server too (automated test `test_invalid_input_is_refused_and_nothing_saved`).
- Narrow-window layout: the record table scrolls sideways; nothing overlaps.
