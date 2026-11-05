# Checking the save fixes on AWS with three servers (5 Nov 2026)

The scaling run ([`../2026-11-05-aws-scaling/`](../2026-11-05-aws-scaling/)) found that a saved discussion could differ from the Compare screen and that one click could produce two records. This folder records the fixes being checked on the same stack, under load, with three servers.

| Item | Value |
|---|---|
| Stack | `nimbus`, us-east-1, AWS Academy Sandbox (same stack as the scaling run) |
| Code | Fazly's fork `fazly-effendy/DS600-Group-Proj`, branch `fix/multi-server-save`: rolling update to **`3db1a00`** at 01:32:51–01:34:56 SGT, then to **`530a7b7`** at about 02:08 SGT; Back-button check on a fresh stack at **`9530f71`** (same app code as `4a0bebd`), 13:13 SGT in a new sandbox session |
| Load | `scripts/load_test.py` from the laptop, 01:38:34–01:58:34 SGT: 17,605 responses, **0 errors** ([`load-test.log`](load-test.log)) |
| Recorded by | Claude in Chrome: one session read-only in the console ([`aws-report.md`](aws-report.md), `aws/`), one in the app (`app-3db1a00/`, `app-530a7b7/` and their reports); reviewed by Claude |

## Results

| Check | Result | Evidence |
|---|---|---|
| Rolling update to `3db1a00`: new server signalled success, old one terminated, no rollback | **Pass** (2 min) | `aws/00`–`02b`, `aws-report.md` §2 |
| Scale-out again under load (1 → 3 at 01:43:03, 3 healthy at 01:46:46) | **Pass** | `aws/08`–`10` |
| **Saved figures equal the Compare screen when another server handles the Save** | **Pass**: C-FIX-01 and C-FIX-02 were compared on `i-09cc8a3aec7d4d7d3` and saved on `i-035d65e50973f48b6`; prices identical | `app-3db1a00/03`, `05` |
| One click creates one record | **Pass** | `app-3db1a00/09`; `app-530a7b7/06` |
| Analyst upside matches the price shown (6 of 6 values) | **Pass** | `app-3db1a00/02b`, `app-530a7b7/02` |
| Display rounding (C-FIX-03 showed 353.91 on Compare, 353.90 in the record on `3db1a00`) | Fixed in `530a7b7`: **Pass**, C-FIX-04 equal to the cent in the record table, summary and Discussions list | `app-530a7b7/02`–`04` |
| Dashboard counts saved discussions (showed 0 on `3db1a00`) | Fixed in `530a7b7`: **Pass** (5 → 6 after one save) | `app-530a7b7/01`, `06` |
| Browser Back after Save: button usable and re-save shows the existing record | **Fail on `530a7b7`** (button stayed on "Saving…"; no duplicate created). **Pass on `9530f71`** (fresh stack, 13:13 SGT): button "Save discussion" and enabled after Back; re-save showed "This discussion was already saved; showing the saved record."; exactly one record | `app-530a7b7/05`; `app-9530f71/03`, `04`, `05` ([report](app-9530f71-report.md)) |
| Dashboard "Recent discussions" lists saved discussions | **Pass on `9530f71`** | `app-9530f71/05a` |

## Follow-up

- **Back button:** on `530a7b7` the browser was still running the `compare.js` from before the update, because Nginx lets browsers cache `/static/` for an hour. `4a0bebd` adds the deployed commit to every static URL, so a deploy always serves the new script; confirmed on AWS on `9530f71` (see the table).
- The two C-SCALE-01 records from the scaling run remained; they were deleted with the sandbox.

**All findings from the 5 Nov AWS runs are fixed and confirmed on AWS.**

Console screenshots have the account ID and username blacked out (checked by eye: header corners and stack pages).
