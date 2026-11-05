# Nimbus RM: fix deployment and verification (commit 3db1a00)

**Environment:** AWS Academy Sandbox, us-east-1 · **Stack:** `nimbus` · **Date:** Thu 05 Nov 2026 · **All times SGT (UTC+8)**
**Testers:** Claude in the AWS console (read-only; this report) and Claude in the Nimbus app (window 2; its results are merged in section 4)

## 1. Summary

| Item | Result |
|---|---|
| **Stack update** | **PASS.** UPDATE_IN_PROGRESS at **01:32:51**, UPDATE_COMPLETE at **01:34:56** (2 min 5 s), no rollback |
| **DeployedCommit** | **`3db1a004130cfd614c3ff23be833979a23b19cee`**, matching the expected `3db1a00…` |
| **Rolling replacement** | New server i-09cc8a3aec7d4d7d3 (launch template v2) sent its success signal at 01:34:47. The old server i-098f56dc160c11619 was terminated at 01:34:50. |
| **Scale-out under load (commit 3db1a00)** | **PASS.** Desired went from 1 to 3 at 01:43:03, about **4.5 min** after the load started (~01:38:34). The load script saw 3 servers by 01:45:34 (about 7 min). The console showed 3 of 3 targets healthy at 01:46:46. |
| **App: footer commit on all servers** | **PASS.** All 3 servers show 3db1a00. |
| **App fix (1): save stores the figures shown on Compare** | **FAIL.** In save 3, the record table shows AAPL 353.90, but Compare showed 353.91. |
| **App fix (2): one click creates one record** | **PASS** |
| **App: duplicate re-submit (Back, then Save)** | **BLOCKED / FAIL.** After Back, the Save button stayed stuck on "Saving…". |
| **App fix (3): analyst upside matches the price shown** | **PASS** |

## 2. Stack update events

| Time | Resource | Event |
|---|---|---|
| 01:32:51 | nimbus | UPDATE_IN_PROGRESS |
| 01:33:03 | LaunchTemplate | UPDATE_COMPLETE |
| 01:33:05 | WebServerGroup | UPDATE_IN_PROGRESS |
| 01:33:10 | WebServerGroup | "Rolling update initiated. Terminating 1 obsolete instance(s) in batches of 1, while keeping at least 1 instance(s) in service. Waiting on resource signals with a timeout of PT25M…" |
| 01:33:10 | WebServerGroup | "Temporarily setting autoscaling group MinSize and DesiredCapacity to 2." |
| 01:33:16 | (Activity) | Launching i-09cc8a3aec7d4d7d3 (user request min 2 / max 3 / desired 2) |
| 01:33:26 | WebServerGroup | "New instance(s) added to autoscaling group - Waiting on 1 resource signal(s) with a timeout of PT25M." |
| 01:34:47 | WebServerGroup | "Received SUCCESS signal with UniqueId i-09cc8a3aec7d4d7d3" |
| 01:34:48 | WebServerGroup | "Terminating instance(s) [i-098f56dc160c11619]; replacing with 0 new instance(s)." |
| 01:34:50 | WebServerGroup | "Successfully terminated instance(s) [i-098f56dc160c11619] (Progress 100%)." |
| 01:34:52 | WebServerGroup | UPDATE_COMPLETE |
| 01:34:55 | nimbus | UPDATE_COMPLETE_CLEANUP_IN_PROGRESS |
| **01:34:56** | **nimbus** | **UPDATE_COMPLETE** |

The other 7 outputs did not change, including ApplicationURL https://d14acasu5hk0nt.cloudfront.net and AutoScalingGroupName nimbus-WebServerGroup-Ti0NHV1INoZL.

## 3. Timeline: desired and healthy counts

| Time | Desired | InService | Healthy targets | Activity / notes | Screenshots |
|---|---|---|---|---|---|
| 01:37 | 1 | 1 (i-09cc8a3aec7d4d7d3, LT v2, us-east-1a) | 1/1 | After the update | 03, 04 |
| ~01:38:34 | | | | **Load started** (the script's first line, at 01:39:04, covers the first 30 s) | |
| 01:40 | 1 | 1 | 1/1 | – | 04 |
| 01:42–01:43 | 1 | 1 | 1/1 | No scaling yet | 05, 06 |
| **01:43:03** | **1 → 3** | 1 | 1 | Requests-high alarm `AlarmHigh-bdb61146` triggered `nimbus-RequestScalingPolicy-0JtRFlzumUd6`. Launches i-0afd9c28f126f57a3 and i-035d65e50973f48b6 began at 01:43:12. | 07, 08, 09 |
| 01:45:34 | 3 | 3 | – | Load script: 3 servers responding | |
| **01:46:46** | 3 | 3 | **3/3** | Scaled out: i-0afd9c28f126f57a3 (1a), i-035d65e50973f48b6 (1b), i-09cc8a3aec7d4d7d3 (1a) | 10 |
| 01:48:17 / 01:48:19 | 3 | 3 | 3/3 | Both launches Successful (warm-up finished) | 13 |
| 01:49–01:56 | 3 | 3 | 3/3 | No new activity | 11, 12, 14, 15, 16 |
| 01:59 | 3 | 3 | – | No new activity; load due to end at ~01:58:34 (20-minute run) | 17 |

The load script output pasted at about 01:53 showed 832–914 requests per minute and **0 errors** (10,972 × 200 up to 01:51:04). In the previous run on 04a80ba there were 4 errors.

**Load stop:** the user has not confirmed it yet. A 20-minute run started at ~01:38:34 would end at about 01:58:34. Scale-in was not recorded in this run; the task asked to stop at load end.

## 4. App results (from the Nimbus app session, window 2)

The app saw servers i-0afd9c28f126f57a3, i-09cc8a3aec7d4d7d3 and i-035d65e50973f48b6, all on 3db1a00. These are exactly the 3 InService instances in the console.

| Client | Compare server → Save server | Compare | Saved record table | Equal? |
|---|---|---|---|---|
| C-FIX-01 (/discussions/3) | i-09cc8a3aec7d4d7d3 → i-035d65e50973f48b6 | AAPL 354.05 · MSFT 555.25 | 354.05 · 555.25 | YES |
| C-FIX-02 (/discussions/4) | i-09cc8a3aec7d4d7d3 → i-035d65e50973f48b6 | AAPL 353.83 · MSFT 554.44 | 353.83 · 554.44 | YES |
| C-FIX-03 (/discussions/5) | i-035d65e50973f48b6 → same | AAPL 353.91 · MSFT 554.13 | **353.90** · 554.13 | **NO** (0.01) |

- **Upside:** 6 of 6 values match target ÷ price − 1. This was fixed in 3db1a00.
- **Discussions:** one record each for C-FIX-01, 02 and 03. C-SCALE-01 still has 2 records from the earlier run.

App findings:

1. **Rounding mismatch.** The record table and the Discussions list show 353.90, while Compare and the summary show 353.91. The raw value is likely about 353.905, and the two places round it differently.
2. **Save button stuck after browser Back.** It stays on "Saving…" and is disabled, probably restored from the back-forward cache. The server-side duplicate message could not be tested this way.
3. **Dashboard counters show 0 discussions** while there are 5 records. This was also seen on 04a80ba.

## 5. Notes

- **Load start time:** at first I recorded it as 01:38:58, when your message arrived. I corrected it to ~01:38:34 from the load script output.
- **01:45 Activity check:** the Activity tab did not yet show the 01:43 launches. They appeared on the next check at 01:46. This was a console refresh delay; the timestamps in the table come from the entries themselves.
- **Account ID in screenshots:** all 18 AWS screenshots (00–17) were redacted. An OCR check found no readable account ID or username in any of them. The app screenshots come from the Nimbus app, not the AWS console.
- **Read-only:** no settings were changed. The Parameters tab and user data were not opened.

## 6. Files

`nimbus_fix_verification.zip` contains:

- `aws/`: 00–17 `_fixaws_` screenshots
- `app/`: the app session's 01–10 `_fix_` screenshots and `nimbus_fix_report.md`
- a copy of this report
