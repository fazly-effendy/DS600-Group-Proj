# Nimbus RM – Feature 6 AWS Evidence Report

**Date:** 2026-11-04 (all times SGT, UTC+8)
**Environment:** AWS Academy Sandbox, us-east-1. The session ran 15:54:16–18:54:16 SGT.
**Stack:** `nimbus`. Created at commit `9acd7ef6342390cb2f76d11557e627227adda131`, then updated to `04a80ba94002ce94f75e539f04b7758c61d68648`.
**Tester:** Claude (read-only on AWS). The user ran the CloudShell commands and the stack update.

## 1. Summary

| Phase | Result | Key times (SGT) |
|---|---|---|
| A – Stack creation | **PASS** | Created 16:19:14, CREATE_COMPLETE 16:32:35 |
| B – Acceptance step 12 on RDS | **PASS** | Compare and save at 16:48. Saved values equal the compare values. Search "apple" returned 1 row |
| C – Rolling update | **PASS** | Submitted 17:04:10, cutover 17:06:27, 0 failed requests in 239. Data kept after the update (checked 18:38) |
| D – Scaling test | **NOT RUN** | Sandbox time ran out (under 30 min left by 18:36). No scale-out, cross-server reopen or scale-in evidence |

## 2. Details

### 2.1 Stack outputs (Phase A)

| Key | Value |
|---|---|
| ApplicationURL | https://d3t99542k07ov6.cloudfront.net |
| AutoScalingGroupName | nimbus-WebServerGroup-s4NnnJdcPJB3 |
| CloudFrontDistributionId | E141OMN8WX52HI |
| DatabaseEndpoint | nimbus-database-vb6sh8eqzicq.cdgyu2umrhtq.us-east-1.rds.amazonaws.com |
| DeployedCommit | 9acd7ef6342390cb2f76d11557e627227adda131 |
| LoadBalancerDNSName | nimbus-LoadB-39IkLnc98QLv-1108638929.us-east-1.elb.amazonaws.com |
| SnapshotArchiveBucketName | nimbus-snapshotarchivebucket-hz4cvm9lxm0n |
| VpcId | vpc-0fc0a01e2a699dbb8 |

**Auto Scaling group** (created 16:27:54)

- Capacity: desired 1, scaling limits 1–3, status "At desired capacity".
- `nimbus-CpuScalingPolicy-UFwEaMylr6q3`: target tracking, average CPU utilization 60, warm-up 300 s, scale-in enabled.
- `nimbus-RequestScalingPolicy-jb1qDEiCp3RO`: target tracking, ALB request count per target 300, warm-up 300 s, scale-in enabled.
- Instance after creation: `i-03fe1f736b2b28202`, InService, t3.micro, use1-az6, Healthy.

### 2.2 Compare vs saved (Phase B)

The home page footer at 16:48 read `Server i-03fe1f736b2b28202 · commit 9acd7ef`.

| | Compare: last price | Saved: price (price date) | Rev growth (compare / saved) | Net margin | D/E | FY |
|---|---|---|---|---|---|---|
| AAPL | USD 331.90 | USD 331.90 (03 Nov 2026) | +6.4% / +6.4% | 26.9% / 26.9% | 1.34× / 1.34× | 2025 |
| MSFT | USD 520.99 | USD 520.99 (03 Nov 2026) | +17.8% / +17.8% | 40.3% / 40.3% | 0.13× / 0.13× | 2026 |

Compare also showed these figures:

- **AAPL:** 1y return +23.4%, volatility 24.3%, max drawdown −13.8%, market cap 4.84T.
- **MSFT:** 1y return +2.1%, volatility 33.1%, max drawdown −31.0%, market cap 3.87T.

**Saved record** (`/discussions/1`, saved once at 04 Nov 2026 16:48 SGT)

- Client: C-AWS-01 · AWS Test Client.
- Discussion date: 04 Nov 2026, which is today in Singapore.
- Interests: "Dividend income; worried about AI valuations". Notes: "AWS final run".
- Banner: "Saved the discussion with C-AWS-01 · AWS Test Client. This is the record as saved; reopening it never fetches new data."

**Search:** Company "apple" returned 1 row: 04 Nov 2026, AWS Test Client, C-AWS-01, AAPL USD 331.90 and MSFT USD 520.99.

### 2.3 Rolling update (Phase C)

**What changed:** only GitCommit (screenshot 21 shows only that field). The change set preview listed four resources to modify:

- CpuScalingPolicy
- LaunchTemplate
- RequestScalingPolicy
- WebServerGroup

No RDS or CloudFront resources were in the change set, and no IAM acknowledgement was needed. (The change set comes from the user's notes. Claude did not see it.)

**Uptime log summary** (`rolling-update.log`, screenshot 26, copied exactly):
```
239 rolling-update.log
16:58:13 HTTP200 Server i-03fe1f736b2b28202 · commit 9acd7ef
17:18:12 HTTP200 Server i-07d2dee07752ad24e · commit 04a80ba
NON200: 0
CHANGES:
16:58:13 HTTP200 i-03fe1f736b2b28202 9acd7ef
17:06:27 HTTP200 i-07d2dee07752ad24e 04a80ba
```
- **Result: 239 requests, 0 non-HTTP200.** The cutover happened once, with no switching back.

**Data kept (C4, reopened at 18:38):** C-AWS-01 shows the footer `Server i-07d2dee07752ad24e · commit 04a80ba`. The values are unchanged from B4:

- AAPL USD 331.90, +6.4%, 26.9%, 1.34×.
- MSFT USD 520.99, +17.8%, 40.3%, 0.13×.
- Interests, notes and the saved time (16:48 SGT) are also unchanged.

**State afterwards (18:38):** desired 1, limits 1–3, "At desired capacity". There is 1 instance, `i-07d2dee07752ad24e`, which is InService.

### 2.4 Server IDs seen for C-AWS-01

| Time | Server | Commit |
|---|---|---|
| 16:48 (save) | i-03fe1f736b2b28202 | 9acd7ef |
| 18:38 (reopen) | i-07d2dee07752ad24e | 04a80ba |

### 2.5 Scaling timeline (Phase D)

Not run. No alarm states, load-test data, multi-target health or scale-in were recorded.

### 2.6 Auto Scaling Activity history (full text, copied 18:38)

```
Successful | Terminating EC2 instance: i-03fe1f736b2b28202 | At 2026-11-04T09:06:24Z instance i-03fe1f736b2b28202 was taken out of service in response to a user request, shrinking the capacity from 2 to 1. | Start 2026 November 04, 05:06:24 PM +08:00 | End 2026 November 04, 05:07:17 PM +08:00
Successful | Launching a new EC2 instance: i-07d2dee07752ad24e | At 2026-11-04T09:04:30Z a user request update of AutoScalingGroup constraints to min: 2, max: 3, desired: 2 changing the desired capacity from 1 to 2. At 2026-11-04T09:04:39Z an instance was started in response to a difference between desired and actual capacity, increasing the capacity from 1 to 2. | Start 2026 November 04, 05:04:41 PM +08:00 | End 2026 November 04, 05:09:46 PM +08:00
Successful | Launching a new EC2 instance: i-03fe1f736b2b28202 | At 2026-11-04T08:27:55Z a user request update of AutoScalingGroup constraints to min: 1, max: 3, desired: 1 changing the desired capacity from 0 to 1. At 2026-11-04T08:27:58Z an instance was started … (rest of the cause text cut off in the console extract)
```

## 3. Unexpected items and deviations

1. **Phase D was not executed.** The Sandbox had 18 minutes left at about 18:37. The rolling update finished at about 17:10, but the next step was not resumed until 18:31.
2. **The update briefly raised the ASG minimum to 2.** The rolling update set min 2 / max 3 / desired 2 at 17:04:30, then set it back to 1. This is expected behaviour for a CloudFormation rolling update.
3. **Old instance terminated before the new launch activity closed.** The old instance's termination started at 17:06:24. The new instance's launch activity was still open until 17:09:46, but traffic was already on the new server from 17:06:27 and no request failed.
4. **The uptime log ended early.** CloudShell ended the session after inactivity, so the log stops at 17:18:12, about 12 minutes after the cutover. The update was still in progress then. UPDATE_COMPLETE was confirmed by the user at 18:31, and there is **no screenshot of UPDATE_COMPLETE** in the set.
5. **The log was summarised differently from C3.** Instead of the exact `grep -c` / `grep -vc` / `awk | uniq` commands from C3, a combined one-shot summary was used: line count, first and last lines, non-200 count and change points. It gives the same facts.
6. **Opening CloudShell in a second tab disconnected the first tab's view.** It reconnected with no gap in the log.
7. **Cookie banner alert.** The console showed "Unable to save cookie preferences". It had no effect on the test.
8. **Screenshot 23 shows identifying details.** It contains the AWS account ID and lab username in the console header. No secrets or stack Parameters values appear in any screenshot.

## 4. Screenshot index

| # | Phase | Shows |
|---|---|---|
| 01, 01b | A | Stack CREATE_COMPLETE (Stack info and Events) |
| 02a, 02b | A | Outputs tab |
| 03 | A | ASG details (desired 1, limits 1–3) |
| 04 | A | Automatic scaling (both policies) |
| 05a, 05b | A | Instance management (1 InService, Healthy) |
| 06 | A | Activity (1 launch) |
| 07 | B | Home page and footer |
| 08a, 08b | B | Compare AAPL/MSFT 1y (glance and key financials) |
| 09a, 09b | B | Saved discussion (banner and record table) |
| 10 | B | Discussions search "apple" |
| 11–26 | C | User-captured rolling update (CloudShell loop, GitCommit-only change, UPDATE_IN_PROGRESS, log summary) |
| 27–29 | C4 | C-AWS-01 reopened (record, table, footer at commit 04a80ba) |
| 30 | C | ASG Activity after update (launch, then terminate) |
| 31 | C | Instance management after update (1 instance, i-07d2dee07752ad24e) |
