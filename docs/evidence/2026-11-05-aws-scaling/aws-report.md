# Nimbus RM, Feature 6: auto-scaling evidence report

**Environment:** AWS Academy Sandbox, us-east-1 · **Stack:** `nimbus` · **Commit:** `04a80ba94002ce94f75e539f04b7758c61d68648`
**Date:** Thu 05 Nov 2026 · **All times SGT (UTC+8)** · **Testers:** Claude in the AWS console (this report), Claude in the Nimbus app (second browser window; its findings are merged here)
**Auto Scaling group:** `nimbus-WebServerGroup-Ti0NHV1INoZL`, min 1 / max 3, target tracking on CPU 60% and 300 ALB requests per target.

All console work was read-only. No Update, Delete, Edit, Terminate or capacity change was clicked. The stack Parameters tab and the launch template user data were never opened.

---

## 1. Summary

| Phase | Result | Evidence |
|---|---|---|
| **A. Stack** | **PASS.** `CREATE_COMPLETE`; DeployedCommit = `04a80ba…` | 01, 02a, 02b |
| **B. Baseline** | **PASS.** Desired 1, min 1, max 3; 2 target-tracking policies; 1 InService/Healthy; 1 healthy target; 4 TargetTracking alarms | 03–07b, app 01–03b |
| **C. Scale-out** | **PASS.** Reached **3 servers** (the max). Requests-high alarm fired **5 min** after load start (00:46:03). Desired 1 → 3 at 00:46:03. **3 healthy targets ≈7–8 min** after load start (first seen by the load script in the 00:47:42–00:48:12 window; confirmed in the console at 00:48:45). | 08a–25 |
| **D. Cross-server reopen** | **PASS.** The app session reopened C-SCALE-01 on all 3 servers (i-098f56dc160c11619, i-0083d2648e2c893e7, i-061db5dcf7d1c873f) with identical prices (AAPL 351.74, MSFT 553.27). | app 04–06 |
| **E. Scale-in** | **PASS.** Requests-low alarm fired 01:16:05 (**16.6 min** after load stop). Desired 3 → 2 at 01:16:05, 2 → 1 at 01:17:05 (**17.6 min**). Last termination complete 01:18:23 (**18.9 min**). Back to 1 InService (the original i-098f56dc160c11619). | 26–35 |

- **Load start:** 00:41 (user); the load script's first line is 00:41:42.
- **Load stop:** about 00:59:30. The last script line is 00:59:12, followed by "Stopped."; the "minutes from load stop" figures use 00:59:30.
- **Separate app finding (FAIL):** the prices saved in the discussion snapshot differ from the Compare screen. See section 5.

---

## 2. Timeline

| Time | Requests-high alarm | CPU-high alarm | Desired | InService | Healthy targets | Activity / notes |
|---|---|---|---|---|---|---|
| 00:30–00:34 | OK | OK | 1 | 1 | 1 | Baseline. Both low alarms In alarm (idle). |
| 00:41 | | | | | | **Load started** (20 threads, ~800–900 req/min) |
| 00:42 | OK | OK | 1 | 1 | 1 | Only the original launch (00:03) |
| 00:43–00:44 | OK | OK | 1 | 1 | 1 | Requests-low → OK at 00:44:05 |
| **00:46:03** | **ALARM** | OK | **1 → 3** | 1 | 1 | Alarm `AlarmHigh-bdb61146` triggered `nimbus-RequestScalingPolicy-0JtRFlzumUd6`. Launches started 00:46:10 (i-0083d2648e2c893e7) and 00:46:11 (i-061db5dcf7d1c873f). |
| 00:47 | ALARM | OK | 3 | 3 | 1 | The 2 new targets were Unhealthy ("Health checks failed") while booting |
| 00:48:12 (load script) | | | | | | Load output shows **3 servers** responding |
| **00:48:45** | ALARM | OK | 3 | 3 | **3** | **Scaled out**: 3 healthy, 0 unhealthy |
| 00:51 | ALARM | OK | 3 | 3 | 3 | Launches Successful at 00:51:15 and 00:51:18 (end of the 300 s warm-up) |
| 00:52:03 | **OK** | OK | 3 | 3 | 3 | Load per target fell to about 300 once spread across 3 servers |
| 00:55–00:58 | OK | OK | 3 | 3 | 3 | No change |
| ~00:59:30 | | | | | | **Load stopped** |
| 01:01–01:10 | OK | OK | 3 | 3 | – | Requests-low still OK (needs 15 one-minute datapoints below 210). CPU-low In alarm since 00:20. |
| **01:16:05** | OK | OK | **3 → 2** | 3 | – | Requests-low → **ALARM**. i-0083d2648e2c893e7 selected for termination at 01:16:12; done 01:17:05. |
| **01:17:05** | OK | OK | **2 → 1** | 2 | – | i-061db5dcf7d1c873f selected for termination at 01:17:10; done 01:18:23 |
| 01:20 | OK | OK | 1 | 1 | – | Final state: 1 InService/Healthy (i-098f56dc160c11619); "At desired capacity" |

The CPU-high alarm (`AlarmHigh-3cddb63c`, CPU > 60) stayed **OK for the whole test**. Both scale-out and scale-in were driven by the requests policy.

### Alarms (names and states)

| Alarm (prefix `TargetTracking-nimbus-WebServerGroup-Ti0NHV1INoZL-`) | Rule | Baseline | Peak load | End |
|---|---|---|---|---|
| `AlarmHigh-bdb61146-d8ac-4d85-b79a-5f1df16c3c66` | RequestCountPerTarget > 300, 3 of 3 min | OK | **ALARM 00:46:03 → OK 00:52:03** | OK |
| `AlarmHigh-3cddb63c-e948-4878-a724-770c1e2513a5` | CPUUtilization > 60, 3 of 3 min | OK | OK | OK |
| `AlarmLow-f4bda157-373e-45c8-8ea2-56b5b44595fc` | RequestCountPerTarget < 210, 15 of 15 min | In alarm | OK at 00:44:05 | **ALARM 01:16:05** |
| `AlarmLow-e558b940-3934-43f6-9de0-9c8ea3fd0c8b` | CPUUtilization < 42, 15 of 15 min | In alarm | In alarm | In alarm |

---

## 3. Server IDs seen on C-SCALE-01 (from the app session)

The record is `/discussions/2`, saved once at 00:31 on i-098f56dc160c11619. The app session reloaded it 12 times while the load was running.

| # | Server | AAPL | MSFT | Ratios (AAPL / MSFT) | Commit | App screenshot |
|---|---|---|---|---|---|---|
| 1 | i-098f56dc160c11619 | USD 351.74 | USD 553.27 | 6.4% / 26.9% / 1.34× · 17.8% / 40.3% / 0.13× | 04a80ba | 04 |
| 2 | i-0083d2648e2c893e7 | USD 351.74 | USD 553.27 | same | 04a80ba | 05 |
| 3 | i-061db5dcf7d1c873f | USD 351.74 | USD 553.27 | same | 04a80ba | 06 |

These three IDs match exactly the three InService instances in the Auto Scaling group (screenshots 14b, 19, 25).

---

## 4. Raw records

### 4.1 Load script output (pasted by user; abridged, every server change and error change kept)

```
Sending load to https://d14acasu5hk0nt.cloudfront.net/login with 20 threads for 20 minutes. Ctrl+C to stop.
00:41:42  874 requests/min  responses so far {'200': 437}  servers since last line: 1 ['i-098f56dc160c11619']
... 00:42:12–00:47:42: 804–900 requests/min, 1 server ['i-098f56dc160c11619']
00:47:42  900 requests/min  responses so far {'200': 5601}  servers since last line: 1 ['i-098f56dc160c11619']
00:48:12  888 requests/min  responses so far {'200': 6045}  servers since last line: 3 ['i-0083d2648e2c893e7', 'i-061db5dcf7d1c873f', 'i-098f56dc160c11619']
00:49:42  898 requests/min  responses so far {'200': 7381, 'error': 1}  servers since last line: 3 [same]
00:55:12  872 requests/min  responses so far {'200': 12182, 'error': 2}  servers since last line: 3 [same]
00:56:42  874 requests/min  responses so far {'200': 13505, 'error': 4}  servers since last line: 3 [same]
00:58:42  890 requests/min  responses so far {'200': 15244, 'error': 4}  servers since last line: 3 ['i-0083d2648e2c893e7', 'i-061db5dcf7d1c873f', 'i-098f56dc160c11619']
00:59:12  894 requests/min  responses so far {'200': 15691, 'error': 4}  servers since last line: 3 ['i-0083d2648e2c893e7', 'i-061db5dcf7d1c873f', 'i-098f56dc160c11619']
Stopped.
Total responses: {'200': 15927, 'error': 4}
```

### 4.2 Auto Scaling group Activity history (all 5 entries, newest first, copied 01:20)

1. **Successful** | Terminating EC2 instance: i-061db5dcf7d1c873f | Start 2026 November 05, 01:17:10 AM +08:00 | End 01:18:23 AM +08:00
   Cause: "At 2026-11-04T17:17:05Z a monitor alarm TargetTracking-nimbus-WebServerGroup-Ti0NHV1INoZL-AlarmLow-f4bda157-373e-45c8-8ea2-56b5b44595fc in state ALARM triggered policy nimbus-RequestScalingPolicy-0JtRFlzumUd6 changing the desired capacity from 2 to 1. At 2026-11-04T17:17:10Z an instance was taken out of service in response to a difference between desired and actual capacity, shrinking the capacity from 2 to 1. At 2026-11-04T17:17:10Z instance i-061db5dcf7d1c873f was selected for termination."
2. **Successful** | Terminating EC2 instance: i-0083d2648e2c893e7 | Start 01:16:12 AM +08:00 | End 01:17:05 AM +08:00
   Cause: "At 2026-11-04T17:16:05Z a monitor alarm TargetTracking-nimbus-WebServerGroup-Ti0NHV1INoZL-AlarmLow-f4bda157-373e-45c8-8ea2-56b5b44595fc in state ALARM triggered policy nimbus-RequestScalingPolicy-0JtRFlzumUd6 changing the desired capacity from 3 to 2. At 2026-11-04T17:16:12Z an instance was taken out of service in response to a difference between desired and actual capacity, shrinking the capacity from 3 to 2. At 2026-11-04T17:16:12Z instance i-0083d2648e2c893e7 was selected for termination."
3. **Successful** | Launching a new EC2 instance: i-061db5dcf7d1c873f | Start 12:46:11 AM +08:00 | End 12:51:18 AM +08:00
   Cause: "At 2026-11-04T16:46:03Z a monitor alarm TargetTracking-nimbus-WebServerGroup-Ti0NHV1INoZL-AlarmHigh-bdb61146-d8ac-4d85-b79a-5f1df16c3c66 in state ALARM triggered policy nimbus-RequestScalingPolicy-0JtRFlzumUd6 changing the desired capacity from 1 to 3. At 2026-11-04T16:46:08Z an instance was started in response to a difference between desired and actual capacity, increasing the capacity from 1 to 3."
4. **Successful** | Launching a new EC2 instance: i-0083d2648e2c893e7 | Start 12:46:10 AM +08:00 | End 12:51:15 AM +08:00
   Cause: same text as entry 3.
5. **Successful** | Launching a new EC2 instance: i-098f56dc160c11619 | Start 12:03:04 AM +08:00 | End 12:08:11 AM +08:00
   Cause: "At 2026-11-04T16:02:59Z a user request update of AutoScalingGroup constraints to min: 1, max: 3, desired: 1 changing the desired capacity from 0 to 1. At 2026-11-04T16:03:02Z an instance was started in response to a difference between desired and actual capacity, increasing the capacity from 0 to 1."

### 4.3 Stack outputs (8)

| Key | Value |
|---|---|
| ApplicationURL | https://d14acasu5hk0nt.cloudfront.net |
| AutoScalingGroupName | nimbus-WebServerGroup-Ti0NHV1INoZL |
| CloudFrontDistributionId | E388PHMLYZGY1V |
| DatabaseEndpoint | nimbus-database-bi0nobv9f388.cdgyu2umrhtq.us-east-1.rds.amazonaws.com |
| DeployedCommit | 04a80ba94002ce94f75e539f04b7758c61d68648 ✔ |
| LoadBalancerDNSName | nimbus-LoadB-9mCB08jhfAXl-1451304457.us-east-1.elb.amazonaws.com |
| SnapshotArchiveBucketName | nimbus-snapshotarchivebucket-licl2unwk8r3 |
| VpcId | vpc-0cf0d25820f6e6c84 |

### 4.4 Other baseline facts

- **Scaling policies:** `nimbus-CpuScalingPolicy-fb3TjDEodhGQ` (target tracking, average CPU 60) and `nimbus-RequestScalingPolicy-0JtRFlzumUd6` (target tracking, ALB request count per target 300). Both are enabled, with a 300 s warm-up and scale-in enabled. There are no predictive policies.
- **Instances:** launch template `LaunchTemplate_EDFUnRBN3YWQ` version 1, t3.micro. During scale-out, two instances were in us-east-1b (use1-az6) and one in us-east-1a (use1-az4).
- **Target group:** `nimbus-Targe-QS7OFNCMHK7I`, HTTP:80, instance targets.

---

## 5. Unexpected findings and notes

### AWS console (this session)

1. **4 load-script errors out of 15,931 requests (0.03%).** They appeared between 00:49:12–00:49:42, 00:54:42–00:55:12 and 00:56:12–00:56:42, all after the scale-out. The script does not print the error text, so their cause is not known. `load-test.log` should show more detail.
2. **New targets failed health checks for about 1–2 minutes** after launch: "Health checks failed" at 00:47, Healthy by 00:48:45. This is expected while the servers boot; no traffic errors were seen at that point.
3. **Scale-in waited for the requests-low alarm only.** CPU-low was In alarm from 00:20 onward, but nothing scaled in until requests-low also fired at 01:16:05. This is consistent with how AWS target tracking works: with two policies, it scales in only when both policies agree.
4. **Scale-in stepped down one server per minute** (3 → 2 at 01:16:05, 2 → 1 at 01:17:05) rather than going straight from 3 to 1.
5. **Timing details:**
   - The stack's "Created time" is 2026-11-04 23:54:20 +08, and the Auto Scaling group was created at 00:02:58 on 05 Nov. Both fit a stack that finishes only once a server has bootstrapped.
   - The Sandbox timer pasted at 00:35 SGT gave the session end as 2026-11-04T10:48:52-0800, which is 02:48:52 SGT on 05 Nov. The 25-minute stop line (02:23) was never reached.
6. **Console actions that did not change anything:**
   - I collapsed the console side menus.
   - One click by mistake opened the CloudWatch "Mute rules" tab (view only, 0 rules).
   - One browser window resize had no effect.

### Nimbus app (from the app session's report)

7. **FAIL: saved prices differ from the Compare screen.**

   | Field | Compare screen | Saved record |
   |---|---|---|
   | AAPL price | 351.26 | 351.74 |
   | MSFT price | 552.58 | 553.27 |

   1-year return and market cap also differ. The save banner says it saves the figures "as they are now".
8. **The snapshot's data time (00:20) is earlier than the save (00:31).** This suggests the save used a separate or cached data fetch.
9. **Client C-SCALE-01 already existed before the test.** The app session selected the existing client rather than creating a duplicate.
10. **A second, identical C-SCALE-01 discussion exists (`/discussions/1`)** although Save was clicked once and the dashboard showed 0 discussions beforehand. Possible causes are a double submit, a retry behind the load balancer, or another tester; this needs investigating. The save happened at 00:31, before the load and while only one server existed, so a retry across servers is less likely. Neither record was deleted.
11. **Minor:** the analyst-upside figure appears to use a slightly different price than the one shown on screen.

### Account ID in screenshots

The account ID and username appear in the console's top-right header on every console page. They also appear inside ARN lines, the launch template "Owner" field, and nested stack names.

- **AWS screenshots:** every one (01–35) was redacted: header blacked out, plus OCR-based blacking of any account ID or username text. An OCR check after redaction found **no readable account ID or username in any AWS screenshot**.
- **Screenshot 01:** a nested stack name containing the account ID was blacked out by hand.
- **Screenshot 03:** the bottom edge cuts off a partial line of the Owner field. It was not caught by OCR. Please check it by eye before sharing.
- **App screenshots (`app/`):** taken in the Nimbus app, not the AWS console, so they contain no AWS header.

---

## 6. Screenshot index

The zip `nimbus_feature6_screenshots.zip` contains two folders, `aws/` and `app/`.

| Folder | Files | What they show |
|---|---|---|
| `aws/` | 01–02b | Stack status and outputs |
| | 03 | Auto Scaling group details |
| | 04a, 04b | Scaling policies |
| | 05a, 05b | Instances at baseline |
| | 06a, 06b | Target group at baseline |
| | 07a, 07b | Alarms at baseline |
| | 08a–25 | Phase C: alarms, Activity, instances and targets every 2–3 minutes. Key frames: 13 (scale-out activity), 14a (desired 3), 16 (3 healthy), 17a (requests-high In alarm), 21 (back to OK). |
| | 26–35 | Phase E: 29 (requests-low still OK), 30 (requests-low graph In alarm), 31 (desired 1), 32/33 (termination activity), 34 (1 instance), 35 (final alarms) |
| `app/` | 01–06 | The app session's screenshots: home footer, Compare, saved record, and C-SCALE-01 on each of the 3 servers |
| | `nimbus_qa_report_final.md` | The app session's full report |
