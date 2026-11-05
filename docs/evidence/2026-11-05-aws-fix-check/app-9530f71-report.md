# Nimbus RM QA – Browser Back / re-save test (C-BACK-01)

- App: https://d1yevl6ye65kjd.cloudfront.net/
- Date: Thu 05 Nov 2026, ~13:13 SGT
- Build: footer `Server i-027a37967870952b3 · commit 9530f71`
- Data: fictional client C-BACK-01 "Back Button Client"

**Overall: PASS (6/6 steps)**

| Step | Result | Observed |
|---|---|---|
| 1 | PASS | Footer shows "commit 9530f71". Recent discussions: "Nothing saved yet. Compare companies and save a discussion." Tiles: Clients 0, Discussions saved 0, This month 0, Follow-ups due 0. |
| 2 | PASS | Compare "AAPL, MSFT", period 1y. "Financials, ratings & news" loaded (Key financials + Analyst ratings shown). Last price: **AAPL USD 349.51**, **MSFT USD 555.80** (same in cards and Summary table). |
| 3 | PASS | Saved once. Redirected to /discussions/1. Banner: "Saved the discussion with C-BACK-01 · Back Button Client. This is the record as saved; reopening it never fetches new data." Record: Client interests "Dividend income"; Price at discussion AAPL USD 349.51, MSFT USD 555.80 (price date 04 Nov 2026) – equal to step 2. |
| 4 | PASS | After browser Back: button text "Save discussion", enabled (`disabled=false`). Form still holds C-BACK-01 / Back Button Client / Dividend income. |
| 5 | PASS | One click → page /discussions/1 with message "This discussion was already saved; showing the saved record." C-BACK-01 record shown (saved 05 Nov 2026, 13:13 SGT). |
| 6 | PASS | Dashboard: Clients 1, Discussions saved 1, This month 1; Recent discussions: "05 Nov · Back Button Client · AAPL · MSFT". Discussions page: exactly one row – 05 Nov 2026, Back Button Client / C-BACK-01, AAPL USD 349.51, MSFT USD 555.80, Dividend income. Client filter lists only "C-BACK-01 · Back Button Client". |

## Screenshots
- 01_back_dashboard_initial.jpg – empty Recent discussions + footer commit
- 00a_back_compare_prices.jpg, 00b_back_financials_loaded.jpg – step 2 support
- 02_back_saved_record.jpg, 02b_back_saved_prices.jpg – after first save
- 03_back_after_browser_back.jpg – form after Back, button enabled
- 04_back_resave_message.jpg – "already saved" message
- 05_back_discussions_list.jpg, 05a_back_dashboard_recent.jpg – single record

## Notes
- No defects found. Price date on the record is 04 Nov 2026 (previous close) while saved timestamp is 05 Nov 2026 13:13 SGT – informational only.
