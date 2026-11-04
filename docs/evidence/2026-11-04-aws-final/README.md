# AWS final-code deployment, step 12 on RDS and rolling update (4 Nov 2026)

| Item | Value |
|---|---|
| Repository | Team repository `pujoglekar2026/DS600-Group-Proj` |
| Commits | Stack created at `9acd7ef6342390cb2f76d11557e627227adda131`, then rolling-updated to **`04a80ba94002ce94f75e539f04b7758c61d68648`** (team `main` after PR #6) |
| Template | `infra/nimbus-merged-stack.yaml` (unchanged from `378c077`, which passed 13/13 infrastructure checks in [`../2026-11-04-aws-deploy/`](../2026-11-04-aws-deploy/)) |
| When | Sandbox session 15:54–18:54 SGT; stack created 16:19–16:32 SGT |
| Who | Deployed and updated by Fazly Effendy; recorded by Claude in Chrome (read-only on AWS); reviewed by Claude |

## Results

| Phase | Result | Evidence |
|---|---|---|
| A. Stack created from the team repository | **Pass**: `CREATE_COMPLETE` in 13 minutes; Auto Scaling group 1–3 with both target-tracking policies (CPU 60, 300 requests per target) | 01–06 |
| B. Gaurav's step 12 on RDS | **Pass**: C-AWS-01 saved once; AAPL USD 331.90 and MSFT USD 520.99 and all ratios identical to the Compare page; discussion date 04 Nov 2026 (Singapore date, D-14 fix confirmed); search "apple" finds it | 07–10 |
| C. Rolling update `9acd7ef` → `04a80ba` (only GitCommit changed) | **Pass**: uptime log 239 requests every 5 s, **0 failures**; traffic moved from `i-03fe1f736b2b28202` (9acd7ef) to `i-07d2dee07752ad24e` (04a80ba) at 17:06:27 SGT; C-AWS-01 unchanged after the update | 11–31 |
| D. Scale-out / scale-in under load | **Not run**: the sandbox session ran out. To be recorded in a separate session | — |

Uptime log summary (screenshot 26):

```
239 rolling-update.log
16:58:13 HTTP200 Server i-03fe1f736b2b28202 · commit 9acd7ef
17:18:12 HTTP200 Server i-07d2dee07752ad24e · commit 04a80ba
NON200: 0
CHANGES:
16:58:13 HTTP200 i-03fe1f736b2b28202 9acd7ef
17:06:27 HTTP200 i-07d2dee07752ad24e 04a80ba
```

Auto Scaling activity (copied from the console): the group temporarily went to min 2 / desired 2 at 17:04:30, launched the new server, then terminated the old one at 17:06:24 and returned to 1. This is how a CloudFormation rolling update with `MinInstancesInService: 1` works.

## Notes

- The AWS account ID and lab username in the console header are blacked out in the screenshots (here and in `2026-11-04-aws-deploy/`). No secrets or stack parameter values appear.
- The uptime log stopped at 17:18 because CloudShell ends idle sessions after about 15 minutes; by then traffic had been on the new server for 12 minutes with no failures. For this reason the scaling test now runs its load from a laptop (`scripts/load_test.py`).
- No screenshot of `UPDATE_COMPLETE`; the user confirmed it at 18:31 and the Activity history shows both the launch and the termination completed.
