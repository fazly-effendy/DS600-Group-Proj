# Feature 6: automatic scaling on AWS (5 Nov 2026)

| Item | Value |
|---|---|
| Commit deployed | **`04a80ba94002ce94f75e539f04b7758c61d68648`** (team repository `main`) |
| Stack | `nimbus`, us-east-1, AWS Academy Sandbox; created 23:54–00:08 SGT |
| Load | `scripts/load_test.py` from Fazly's laptop: 20 threads, about 870 requests/minute to the CloudFront URL, 00:41–00:59 SGT |
| Recorded by | Two Claude in Chrome sessions, one read-only in the AWS console (`aws/`, [`aws-report.md`](aws-report.md)) and one in the app (`app/`, [`app-report.md`](app-report.md)); run by Fazly Effendy; reviewed by Claude |

## Result: automatic scaling works out and back in

| Phase | Result | Key evidence |
|---|---|---|
| Baseline | 1 server; Auto Scaling group min 1 / max 3; two target-tracking policies (CPU 60%, 300 requests per server per minute); 4 CloudWatch alarms created by AWS | `aws/03`–`07b` |
| **Scale-out** | Load ~870 requests/min on one server (about 3× the target). The requests-high alarm fired at **00:46:03** (5 min after the load started) and the policy set desired capacity **1 → 3**. All **3 servers healthy at 00:48:45**; the load script saw 3 servers answering from 00:48:12 | `aws/12a`, `13`, `14a`, `16`; `load-test-0041-0055.txt` |
| **Any server serves any discussion** | The saved discussion C-SCALE-01 opened on all three servers (`i-098f56dc160c11619`, `i-0083d2648e2c893e7`, `i-061db5dcf7d1c873f`) with identical figures | `app/04`–`06` |
| **Scale-in** | Load stopped about 00:59:30. The requests-low alarm fired at **01:16:05** (after the required 15 minutes below target); desired 3 → 2 at 01:16:05 and 2 → 1 at 01:17:05; back to 1 server at 01:18:23 | `aws/30`–`35` |
| Reliability under load | 15,927 successful responses and 4 errors (0.03%), all after scale-out; the script does not record the error text (timeouts or dropped connections between the laptop and AWS) | `aws-report.md` §4.1 |

The CPU alarm never fired: these were light requests, so the requests-per-server policy did the work. That is why the stack has two policies (CPU for heavy work, requests for many light requests). With two target-tracking policies AWS scales in only when both agree, which is what happened.

Full Activity history, alarm names and timeline: [`aws-report.md`](aws-report.md).

## Defects found in this run, and their fix

| Finding | Cause | Fix |
|---|---|---|
| Saved prices differed from the Compare screen (AAPL 351.26 shown, 351.74 saved; snapshot data time 00:20 although saved at 00:31) | Market data is cached per process for 15 minutes. Each server runs 3 Gunicorn processes, and with the load balancer there are up to 3 servers, so the Compare page and the Save request can be answered by processes holding different cached prices. Save fetched the figures again instead of using the ones on screen | `fix/multi-server-save` (`731148e`): the API signs the exact figures it sends; the page posts them back with Save; the server verifies the signature and saves them without fetching. Covered by a two-server test and a real-browser two-server run |
| Two identical C-SCALE-01 discussions (`/discussions/1` and `/2`) | Not established. Only one server existed at 00:31, so a cross-server retry is ruled out; the client also already existed before this tester's save, which suggests an earlier test session saved once and this one saved again | Same branch: a one-time submission ID per Compare run, unique per RM in the database, so a repeated request shows the existing record instead of creating another |
| Analyst upside implied a slightly different price than the one shown | Computed by the server from a separate price request | The page computes upside from the price in the Summary table (`app/static/js/compare.js`) |

The fixes still need to be checked on AWS with two or more servers.

## Privacy

The AWS account ID and lab username are blacked out in every console screenshot (header, ARNs, owner fields). Screenshot `aws/03` was re-checked by eye and its partial Owner line blacked out.
