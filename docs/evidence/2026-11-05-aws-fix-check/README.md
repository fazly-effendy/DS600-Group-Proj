# Checking the save fixes on AWS with three servers (5 Nov 2026)

The scaling run ([`../2026-11-05-aws-scaling/`](../2026-11-05-aws-scaling/)) found that a saved discussion could differ from the Compare screen and that one click could produce two records. This folder records the fixes being checked on the same stack, under load, with three servers.

| Item | Value |
|---|---|
| Stack | `nimbus`, us-east-1, AWS Academy Sandbox (same stack as the scaling run) |
| Code | Fazly's fork `fazly-effendy/DS600-Group-Proj`, branch `fix/multi-server-save`: rolling update to **`3db1a00`** at 01:32:51–01:34:56 SGT, then to **`530a7b7`** at about 02:08 SGT |
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
| Browser Back after Save: button usable and re-save shows the existing record | **Fail on AWS** (button stayed on "Saving…"); no duplicate was created | `app-530a7b7/05` |

## Follow-up

- **Back button:** the browser was still running the `compare.js` from before the update, because Nginx lets browsers cache `/static/` for an hour. Commit `4a0bebd` adds the deployed commit to every static URL so a deploy always serves the new script, and the dashboard's "Recent discussions" now lists saved discussions. Checked locally in Chrome with the back/forward cache on: page restored from cache, button enabled, re-save showed "This discussion was already saved", one record. **To be confirmed on AWS.**
- The two C-SCALE-01 records from the scaling run remained; they were deleted with the sandbox.

Console screenshots have the account ID and username blacked out (checked by eye: header corners and stack pages).
