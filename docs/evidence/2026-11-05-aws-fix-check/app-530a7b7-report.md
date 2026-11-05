# Nimbus RM QA report: final fix check (commit 530a7b7)

**App:** https://d14acasu5hk0nt.cloudfront.net · **Tester:** Claude (browser) · **Date:** 05 Nov 2026, about 02:14–02:17 SGT

**Servers seen:** i-067c98387c2d3a311, i-0530ff58601692979 and i-00f4c5c2f349f22f8, all on commit 530a7b7.

## Summary

| Step | Check | Result |
|---|---|---|
| 1 | Footer shows commit 530a7b7. Dashboard counts are real, not 0. | **PASS** |
| 2 | Compare AAPL, MSFT (1y) loads, including "Financials, ratings & news" | **PASS** |
| 3 | Saved record table, Summary and Discussions list all equal Compare to the cent | **PASS** |
| 4 | After Back: button reads "Save discussion" and is enabled; Save shows the already-saved message | **FAIL** |
| 5 | Exactly one C-FIX-04; dashboard count +1 | **PASS** |

## Step 1: footer and dashboard (before the save)

- Footer: `Server i-067c98387c2d3a311 · commit 530a7b7`
- **Discussions saved: 5. This month: 5.** This matches the 5 records on the Discussions page (/discussions/1–5). It showed 0 on 3db1a00.
- Clients: 4.
- Still wrong: the "Recent discussions" panel says "Nothing saved yet. Record your first client discussion." even though 5 discussions exist.

## Step 2: Compare (server i-0530ff58601692979)

| | AAPL | MSFT |
|---|---|---|
| Last price | **USD 354.24** | **USD 555.42** |
| Return 1y | +31.7% | +8.9% |
| Market cap | 5.15T | 4.13T |
| Mean price target / upside | USD 333.28 / -5.9% | USD 633.13 / +14.0% |

"Financials, ratings & news" loaded. Upside check: 333.28 / 354.24 − 1 = -5.92%, and 633.13 / 555.42 − 1 = +13.99%. Both match what is shown.

## Step 3: saved record C-FIX-04 (/discussions/6, saved page on server i-0530ff58601692979)

Saved once at 02:15 SGT. Client "C-FIX-04 · Final Fix Client", interests "Dividend income", notes "Final fix check".

| Where | AAPL | MSFT | Equal to step 2? |
|---|---|---|---|
| Compare page (step 2) | 354.24 | 555.42 | — |
| Record table (Price at discussion) | 354.24 | 555.42 | Yes |
| Summary table (saved page) | 354.24 | 555.42 | Yes |
| Discussions list | 354.24 | 555.42 | Yes |

The saved page's return (+31.7% / +8.9%) and market cap (5.15T / 4.13T) also match. Ratios: AAPL +6.4% / 26.9% / 1.34×, MSFT +17.8% / 40.3% / 0.13×.
**Result: PASS.**

I opened the Discussions list in a second tab so the history needed for step 4 stayed intact. I closed that tab afterwards.

## Step 4: Back, then Save again

- On /discussions/6 I pressed the browser Back button. It returned to `/compare` (tickers AAPL,MSFT, period 1y) with the form still filled in: C-FIX-04, Final Fix Client, Dividend income, Final fix check.
- **Save button text: "Saving…". State: disabled (`disabled = true`).** It was still the same 6 seconds later. Expected "Save discussion", enabled.
- I clicked the button once. **Nothing happened:** no navigation, no request, and no message. The expected text "This discussion was already saved; showing the saved record." did not appear.
- The page appears to come back from the browser's back-forward cache in its pre-submit state, so the button is never reset. This is the same behaviour as on 3db1a00.
- **Result: FAIL.** As a side effect, no duplicate was created.

## Step 5: Discussions and dashboard (after the save)

- The Discussions page lists 6 records. **C-FIX-04 appears exactly once** (/discussions/6). Server: i-00f4c5c2f349f22f8.
- Dashboard: **Discussions saved 6** (was 5, so +1). **This month 6.** Clients 5. Server: i-067c98387c2d3a311.
- **Result: PASS.**

## Other observations

1. "Recent discussions" on the dashboard still says "Nothing saved yet" while the counters show 6.
2. The Discussions list now shows C-FIX-03 with AAPL **USD 353.91**. On 3db1a00 the same record showed 353.90, and its record table also showed 353.90. This suggests the display rounding changed in 530a7b7 rather than the stored data. I did not reopen /discussions/5 to confirm.
3. C-SCALE-01 still has two identical records (/discussions/1 and /discussions/2), carried over from the scaling run.

## Screenshots

- 01_fix_dashboard_counts_footer.jpg: dashboard showing 5 / 5, with footer commit 530a7b7
- 02_fix_compare_summary.jpg: Compare summary with last prices 354.24 / 555.42
- 03_fix_saved_C-FIX-04_record_summary.jpg: saved record table, summary table and footer
- 04_fix_discussions_list_prices.jpg: Discussions list showing C-FIX-04 at 354.24 / 555.42
- 05_fix_back_save_stuck_saving.jpg: after Back, Save button stuck on "Saving…" (taken after the click)
- 06_fix_dashboard_after_and_discussions.jpg: dashboard showing 6 / 6, plus the Discussions list with one C-FIX-04
