# Nimbus RM QA report: fix verification (commit 3db1a00)

**App:** https://d14acasu5hk0nt.cloudfront.net · **Tester:** Claude (browser) · **Date:** 05 Nov 2026, about 01:50–01:55 SGT

## Verdict

| Fix under test | Result |
|---|---|
| Footer shows commit 3db1a00 | **PASS**. All 3 servers seen show 3db1a00. |
| (1) Save stores exactly the figures shown on Compare | **FAIL**. Saves 1 and 2 match exactly. In save 3, the record table shows AAPL **353.90**, while Compare and the saved summary both show **353.91**. |
| (2) One click creates one record | **PASS** for the 3 single clicks: one record each. |
| Duplicate re-submit (Back, then Save) | **BLOCKED / FAIL**. After Back, the Save button was stuck on "Saving…" and disabled. Clicking it did nothing. The expected message never appeared. No duplicate was created. |
| (3) Analyst upside matches the price shown | **PASS**. 6 of 6 values match to 0.1%. |
| Discussions list: exactly one record each for C-FIX-01, 02 and 03 | **PASS** |

Servers seen: i-0afd9c28f126f57a3, i-09cc8a3aec7d4d7d3 and i-035d65e50973f48b6, all on commit 3db1a00.

## Per-save results

Compare values are those shown on the Compare page. Saved values come from the saved page's summary table and its "Price at discussion" record table.

| Client | Compare server | Saved-page server | Shown on Compare | Saved (summary table) | Saved (record table) | Equal? |
|---|---|---|---|---|---|---|
| C-FIX-01 (/discussions/3) | i-09cc8a3aec7d4d7d3 | i-035d65e50973f48b6 | AAPL 354.05, +31.6%, 5.15T · MSFT 555.25, +8.8%, 4.12T | identical | AAPL 354.05 · MSFT 555.25 | **YES** |
| C-FIX-02 (/discussions/4) | i-09cc8a3aec7d4d7d3 | i-035d65e50973f48b6 | AAPL 353.83, +31.5%, 5.14T · MSFT 554.44, +8.7%, 4.12T | identical | AAPL 353.83 · MSFT 554.44 | **YES** |
| C-FIX-03 (/discussions/5) | i-035d65e50973f48b6 | i-035d65e50973f48b6 | AAPL 353.91, +31.5%, 5.14T · MSFT 554.13, +8.6%, 4.12T | identical | **AAPL 353.90** · MSFT 554.13 | **NO** (AAPL off by 0.01) |

The ratios were the same on Compare and in every saved record: AAPL +6.4% / 26.9% / 1.34× and MSFT +17.8% / 40.3% / 0.13×. The fiscal years were also the same (AAPL 2025, MSFT 2026). Volatility and max drawdown matched within each pair too.

Saves 1 and 2 were cross-server: Compare and Save ran on different servers. Save 3 ran Compare and Save on the same server.

## Upside check (upside = mean target ÷ last price − 1)

| Run | AAPL: target / price → computed (shown) | MSFT: target / price → computed (shown) | Result |
|---|---|---|---|
| 1 | 333.28 / 354.05 → -5.87% (-5.9%) | 633.13 / 555.25 → +14.03% (+14.0%) | PASS |
| 2 | 333.28 / 353.83 → -5.81% (-5.8%) | 633.13 / 554.44 → +14.19% (+14.2%) | PASS |
| 3 | 333.28 / 353.91 → -5.83% (-5.8%) | 633.13 / 554.13 → +14.26% (+14.3%) | PASS |

This was a defect on 04a80ba. It is fixed on 3db1a00.

## Duplicate check (step 5)

- On the C-FIX-03 saved page I pressed the browser Back button. It returned to /compare with the form still filled in: C-FIX-03, Fix Test Client, Dividend income, Fix test 3. The same figures were on screen.
- The **Save button showed "Saving…" and was disabled** (`disabled = true`). Clicking it once did nothing: no request, no navigation, no message.
- **Expected message "This discussion was already saved; showing the saved record." did not appear.** The server-side duplicate guard could not be exercised this way. The page appears to restore its pre-submit state from the browser's back-forward cache and never resets the button.
- No duplicate record was created (see the Discussions list below).

## Discussions list (step 6)

| Client | Records | URL |
|---|---|---|
| C-FIX-01 | 1 | /discussions/3 |
| C-FIX-02 | 1 | /discussions/4 |
| C-FIX-03 | 1 | /discussions/5 |
| C-SCALE-01 (previous run) | 2 | /discussions/1, /discussions/2 |

## Unexpected findings

1. **Rounding mismatch in save 3 (FAIL for fix 1).** For AAPL, the Compare page showed USD 353.91. On the saved page, the summary table and "At a glance" also show 353.91. But the "Price at discussion" record table and the Discussions list both show **353.90**. The raw price is probably about 353.905, and the stored record price and the summary display round it differently.
2. **Save button stuck after Back** (see the duplicate check above).
3. **Dashboard counters are wrong.** The dashboard shows "Discussions saved 0" and "This month 0", and Recent discussions says "Nothing saved yet". Meanwhile it shows Clients 4, and the Discussions page lists 5 records. This was also seen on 04a80ba.
4. **Notes field:** the steps gave "Fix test 1". For runs 2 and 3 I used "Fix test 2" and "Fix test 3" so the records can be told apart.
5. I left segment, risk profile and follow-up date blank for every new client (they were optional).

## Screenshots

- 01_fix_home_footer_commit.jpg: dashboard footer, commit 3db1a00
- 02_fix_compare1_summary.jpg / 02b_fix_compare1_ratings.jpg: Compare run 1
- 03_fix_saved1_C-FIX-01.jpg: saved record 1 with footer
- 04_fix_compare2_summary_ratings.jpg: Compare run 2
- 05_fix_saved2_C-FIX-02.jpg: saved record 2 with footer
- 06_fix_compare3_summary_ratings.jpg: Compare run 3
- 07_fix_saved3_C-FIX-03.jpg: saved record 3 (record table showing 353.90, summary showing 353.91, footer)
- 08_fix_duplicate_back_save_stuck.jpg: after Back, Save stuck on "Saving…"
- 09_fix_discussions_list.jpg: Discussions list
- 10_fix_dashboard_counts_zero.jpg: dashboard showing 0 discussions
