# Nimbus RM QA report: scaling test

**App:** https://d14acasu5hk0nt.cloudfront.net · **Tester:** Claude (browser) · **Date:** 05 Nov 2026 (SGT)
**Status:** All steps done.

**Overall:** Cross-server consistency **PASS** (3 servers). Compare-to-saved price fidelity **FAIL** (see section 5).

## 1. Footer / commit

| Page | Server | Commit | Expected | Result |
|---|---|---|---|---|
| Home (dashboard) | i-098f56dc160c11619 | 04a80ba | 04a80ba | PASS |
| Saved record /discussions/2 | i-098f56dc160c11619 | 04a80ba | 04a80ba | PASS |

## 2. Compare (AAPL, MSFT · 1y) vs saved record (C-SCALE-01)

| Metric | AAPL Compare | AAPL Saved | MSFT Compare | MSFT Saved | Match |
|---|---|---|---|---|---|
| Last price | USD 351.26 | **USD 351.74** | USD 552.58 | **USD 553.27** | **NO** |
| Return 1y | +30.6% | +30.7% | +8.3% | +8.5% | NO |
| Market cap | 5.10T | 5.12T | 4.10T | 4.11T | NO |
| Revenue growth (YoY) | +6.4% | +6.4% | +17.8% | +17.8% | Yes |
| Net profit margin | 26.9% | 26.9% | 40.3% | 40.3% | Yes |
| Debt-to-equity | 1.34× | 1.34× | 0.13× | 0.13× | Yes |
| Fiscal year | 2025 | 2025 | 2026 | 2026 | Yes |

I recalculated the ratios from the figures the app shows, and they are consistent. AAPL: 112.0B / 416.2B = 26.9% margin, and 98.7B / 73.7B = 1.34× D/E. MSFT: 133.7B / 331.8B = 40.3% margin, and 56.8B / 442.4B = 0.13× D/E.

## 3. Saved record

- URL: /discussions/2. Saved **once**.
- Client: C-SCALE-01 · Scaling Test Client. Discussion date: 05 Nov 2026.
- Interests: "Dividend income; worried about AI valuations". Notes: "Scaling run".
- Saved at 05 Nov 2026, 00:31 SGT. The page says the market data was retrieved at 00:20 SGT. Price date: 04 Nov 2026.
- Saved on server i-098f56dc160c11619.

## 4. Cross-server check (C-SCALE-01, /discussions/2)

I opened the record from Discussions, then reloaded it 12 times. The footer showed 3 different servers. Every load showed the same prices and ratios.

| # | Server ID | AAPL price | MSFT price | Ratios (AAPL / MSFT) | Screenshot |
|---|---|---|---|---|---|
| 1 | i-098f56dc160c11619 | USD 351.74 | USD 553.27 | 6.4%/26.9%/1.34× · 17.8%/40.3%/0.13× | 04_app_cscale01_server_i-098f56dc160c11619.jpg |
| 2 | i-0083d2648e2c893e7 | USD 351.74 | USD 553.27 | same | 05_app_cscale01_server_i-0083d2648e2c893e7.jpg |
| 3 | i-061db5dcf7d1c873f | USD 351.74 | USD 553.27 | same | 06_app_cscale01_server_i-061db5dcf7d1c873f.jpg |

All three servers report commit 04a80ba. The record was saved on i-098f56dc160c11619 and read back correctly from the other two.

**Same record from 2+ servers: PASS** (3 servers, prices unchanged).

## 5. Unexpected findings

1. **Saved prices differ from the Compare screen the user was looking at (FAIL).** For AAPL, Compare showed 351.26 and the record saved 351.74. For MSFT, Compare showed 552.58 and the record saved 553.27. Return and market cap also moved. The banner says "Saves everything above… as they are now", but the snapshot does not match what was on screen.
2. **The snapshot's data time is earlier than the save.** The page says the market data was retrieved at 00:20 SGT, while the Compare was run and saved at about 00:31 SGT. This suggests the save used a different or cached data fetch, not the one shown on screen.
3. **The client already existed.** The steps said to create C-SCALE-01 as a new client, but "C-SCALE-01 · Scaling Test Client" was already in the dropdown (the dashboard showed 1 client). I selected the existing client rather than creating a duplicate.
4. **A second, identical discussion exists.** The Discussions list shows two C-SCALE-01 records (/discussions/1 and /discussions/2), both dated 05 Nov 2026 with the same prices (351.74 / 553.27) and interests. I clicked Save once and was taken to /discussions/2. Before the save, the dashboard showed 0 discussions. Possible causes: a double submit, a retry behind the load balancer, or another tester. Needs investigation. I did not delete either record.
5. **Analyst upside seems to use a different price (minor).** On Compare, AAPL upside was -5.3% against a USD 333.28 target. That implies a close of about 351.9, not the 351.26 shown. MSFT upside was +14.4%, which implies about 553.4. The label says the upside uses the "latest closing price", so this may be intended. Noted for consistency.

## Screenshots

- 01_app_home_footer.jpg: dashboard with footer (server and commit)
- 02a_app_compare_prices_header.jpg: Compare summary and Financials heading
- 02_app_compare_financials.jpg: key financials and ratios
- 03a_app_saved_record_header.jpg: saved confirmation and discussion record
- 03_app_saved_record.jpg: saved prices and ratios table
- 03b_app_saved_record_footer.jpg: saved record footer (server and commit)
- 04/05/06_app_cscale01_server_*.jpg: C-SCALE-01 record (prices, ratios and footer) as served by each of the 3 servers
