# QA Report — Nimbus RM, Features 3–5 (Save / Search / Reopen discussion snapshot)

- **Branch / commit under test:** feature/discussion-snapshot (e5c258b), as stated by the tester. I did not verify the commit myself.
- **App URL used:** http://127.0.0.1:5001. **http://127.0.0.1:5000 did not load:** the tab only showed the URL as its title and page tools failed.
- **Run date/time:** 04 Nov 2026, approx. 02:08–02:30 SGT (03 Nov 2026 18:08 UTC onward)
- **Browser viewport:** 539 × 567–623 px (narrow side-panel width)
- **Login:** already signed in as "Fazly Effendy"; no login prompt appeared.

## 1. Summary

**PASS — 11 / 11 acceptance checks passed.**
I found one defect that the checks do not cover. On the **Clients list**, QA Test Client shows **Discussions = 0** and **Last spoke = "—"**, even though one discussion is saved. This was still the case after the restart. See section 6.

## 2. Check results

| Check | Result | Evidence |
|---|---|---|
| C1 Save worked with one click; landed on saved page with success message | PASS | Clicked "Save discussion" once and landed on `/discussions/1`, page title "Discussion with QA Test Client · Nimbus RM". Green message: "Saved the discussion with C-QA-01 · QA Test Client. This is the record as saved; reopening it never fetches new data." |
| C2 Record shows Client ID, both tickers, today's date, price per company, interests exactly as typed | PASS | Client "C-QA-01 · QA Test Client"; heading "QA Test Client · 04 Nov 2026"; subheading "C-QA-01 · AAPL, MSFT · period 1y"; Discussion date "04 Nov 2026"; Client interests "Dividend income; worried about AI valuations" (exact); prices USD 330.81 / USD 520.92 |
| C3 Price at discussion = Last price from step 2 | PASS | AAPL 330.81 = 330.81; MSFT 520.92 = 520.92 |
| C4 Revenue growth, net margin, D/E equal step 2 | PASS | AAPL +6.4% / 26.9% / 1.34× ; MSFT +17.8% / 40.3% / 0.13×. Identical on both pages. |
| C5 Labelled "Historical snapshot", source "Yahoo Finance" | PASS | Banner: "Historical snapshot. Everything on this page is exactly as saved on 03 Nov 2026, 18:09 UTC (market data retrieved 03 Nov 2026, 18:08 UTC). It is not refreshed. Source: Yahoo Finance." Each price cell also shows "Yahoo Finance". |
| C6 Reopening made no "/api/" requests | PASS | Cleared requests, reloaded `/discussions/1`, opened "Financial ratios & trends", waited 5 s. Requests: the page itself, style.css, compare.js, Chart.js (cdnjs), Google Fonts (CSS + 3 woff2) and one `data:` URI. **Zero "/api/" requests.** After the restart, reopening also made zero "/api/" requests. |
| C7 Search finds by client, "MSFT", "apple"; not "NVDA" or future date | PASS | 7a, 7b and 7c each returned 1 row (the QA record). 7d and 7e returned "No saved discussions match." See section 4. |
| C8 Client page lists the discussion | PASS | `/clients/1` → "Saved discussions": 04 Nov 2026 · AAPL USD 330.81 · MSFT USD 520.92 · "Dividend income; worried about AI valuations" · Open. (The Clients *list* count is wrong; see section 6.) |
| C9 Empty client interests refused; no record created | PASS | Browser tooltip "Please fill out this field." on Client interests (field is `required`). Page stayed on /compare. Discussions list still showed exactly 1 record. |
| C10 After restart, record identical to step 5 | PASS | Every field and table value is the same (section 3). Saved timestamp is unchanged: 03 Nov 2026, 18:09 UTC. |
| C11 No error, raw code, undefined/null/NaN, broken layout | PASS (with notes) | Text scan of the main content found no "undefined", "null", "NaN", "Traceback" or template tags. There are minor narrow-width layout notes in section 6. None counts as broken layout. |

## 3. Values side by side

| Company | Field | Compare page (step 2) | Saved record (step 5) | After restart (step 11) |
|---|---|---|---|---|
| AAPL (Apple Inc.) | Price | USD 330.81 | USD 330.81 (price date 03 Nov 2026, Yahoo Finance) | USD 330.81 (03 Nov 2026, Yahoo Finance) |
| | Revenue growth | +6.4% | +6.4% | +6.4% |
| | Net margin | 26.9% | 26.9% | 26.9% |
| | Debt-to-equity | 1.34× | 1.34× | 1.34× |
| | Fiscal year | 2025 | 2025 | 2025 |
| MSFT (Microsoft Corporation) | Price | USD 520.92 | USD 520.92 (price date 03 Nov 2026, Yahoo Finance) | USD 520.92 (03 Nov 2026, Yahoo Finance) |
| | Revenue growth | +17.8% | +17.8% | +17.8% |
| | Net margin | 40.3% | 40.3% | 40.3% |
| | Debt-to-equity | 0.13× | 0.13× | 0.13× |
| | Fiscal year | 2026 | 2026 | 2026 |

Other step-5 record fields, unchanged after restart: Client "C-QA-01 · QA Test Client"; Discussion date "04 Nov 2026"; Client interests "Dividend income; worried about AI valuations"; Notes "QA run 1"; Follow up on "04 Dec 2026"; Saved "03 Nov 2026, 18:09 UTC".

Demo-data banner (step 2): **not shown.** The page contains a hidden element (`div.flash.warning`, `hidden`, display:none) with the text "Live market data was unavailable, so some figures below are demo data…". It was not visible.

## 4. Search results (Discussions page)

| Test | Filter (URL params confirmed) | Result |
|---|---|---|
| 7a | client_id=1 | 1 row: 04 Nov 2026 · QA Test Client C-QA-01 · AAPL USD 330.81 · MSFT USD 520.92 · Dividend income; worried about AI valuations · Open |
| 7b | company=MSFT | Same 1 row (QA discussion appears) |
| 7c | company=apple | Same 1 row (QA discussion appears) |
| 7d | company=NVDA | "No saved discussions match." (does not appear) ✔ |
| 7e | date_from=2026-11-05 | "No saved discussions match." (does not appear) ✔ |
| Step 11 | company=AAPL (after restart) | Same 1 row; opened → `/discussions/1` |

Step 8: opened the record from the 7a results and got `/discussions/1`. All fields matched step 5 exactly.

Caveat: only one discussion exists in the database. So 7a–7c show that the record *is* found, but they cannot show that other clients' or companies' records are *excluded*. 7d and 7e cover exclusion.

## 5. Exact banner, warning and error text

- Success (after save): "Saved the discussion with C-QA-01 · QA Test Client. This is the record as saved; reopening it never fetches new data."
- Snapshot banner: "Historical snapshot. Everything on this page is exactly as saved on 03 Nov 2026, 18:09 UTC (market data retrieved 03 Nov 2026, 18:08 UTC). It is not refreshed. Source: Yahoo Finance."
- Save-form help text: "Saves everything above for one client: prices, financials, ratings and news as they are now, with the client's interests and your notes. Reopening it later shows exactly this, never today's data. Demo data is never saved as a client record."
- Step 10a (browser validation tooltip): "Please fill out this field."
- Step 10b (red app message): "Enter at least 2 tickers."
- Search, no results: "No saved discussions match." plus the button "Compare companies and save a discussion".
- News sections (shown on both pages): "Via Yahoo Finance search + RSS — Yahoo's ticker news feed returned nothing, so these come from Yahoo search (only articles linked to the ticker that name the company) and Yahoo's RSS feed."
- Hidden (not displayed) elements in the DOM: "Live market data was unavailable, so some figures below are demo data. They are for illustration only." (compare page), and "These figures were saved from demo data (offline demo mode). They are for illustration only." (saved page).

## 6. Other observations not covered by the checks

1. **Defect: Clients list count is wrong.** `/clients` shows "C-QA-01 · QA Test Client · — · — · **0** · **—**" in the columns Code / Name / Segment / Risk profile / Discussions / Last spoke. The client has 1 saved discussion, dated 04 Nov 2026. This was the same after the restart. Likely cause: the list counts or reads only "stock notes" or a different table, not saved discussions.
2. **Port:** the app was on 5001, not 5000.
3. **Saved timestamp vs discussion date:** "Saved 03 Nov 2026, 18:09 UTC" next to "Discussion date 04 Nov 2026" is correct (02:09 SGT on 04 Nov), but it may confuse users in Singapore. Consider showing local time.
4. **Price date is 03 Nov 2026** (previous US close), while the discussion date is 04 Nov. This is expected for US stocks, but worth a note in the UI.
5. **Narrow-width layout (539 px):** the Discussion record table scrolls sideways, so Company and Fiscal year are not both visible at once. On `/clients`, the table card sits slightly wider than the other cards, the Code column wraps to "C- / QA- / 01", and "Risk profile" wraps. On Discussions, the "Open" button sits at the card's right edge. Nothing was broken or overlapping, apart from the mouse cursor in the screenshots.
6. **Accessibility:** the "To" date filter on Discussions has no accessible label name (the accessibility tree shows an empty label). "From" is labelled.
7. **Whitespace-only interests not tested.** The browser's `required` check accepts a value made of spaces only. Whether the server rejects "   " was not tested, because a passing test would create an extra record.
8. **News text from source:** one MSFT summary reads "Key TakeawaysAlphabet…" with a missing space. This comes from the source feed, which the app says it shows verbatim.
9. The "Loading financials, analyst ratings and news…" element stays in the DOM but is hidden after loading. It is not visible.

## 7. Evidence (zip: `QA_evidence_discussion-snapshot.zip`)

01–03 Compare page and step-2 values · 04–06 Save form filled in · 07–12 Saved discussion page, top to bottom · 13–14 Financial ratios opened (no /api/ calls) · 15–20 Discussions search 7a–7e · 21–22 Clients list (0 count bug) and client page · 23–25 Negative tests · 26–30 After restart (search, record top, record table, clients list).
