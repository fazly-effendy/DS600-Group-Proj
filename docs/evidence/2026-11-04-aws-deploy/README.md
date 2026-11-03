# AWS Sandbox deployment and Gaurav's step 12 on Amazon RDS (4 Nov 2026)

| Item | Value |
|---|---|
| What | First deployment of the scaling stack (Feature 6 architecture) and Gaurav's acceptance test step 12: save, search and reopen a discussion with the data in Amazon RDS |
| Commit deployed | `378c077f466c07dbd2bd1fdf7deff7753e43ba46` (stack output `DeployedCommit`; app footer "commit 378c077") |
| Template | `infra/nimbus-merged-stack.yaml` at that commit; stack name `nimbus`, us-east-1 |
| When | Stack created 03:03–03:19 SGT; checks 03:20–03:50 SGT |
| Who | Deployed by Fazly Effendy in his AWS Academy Sandbox; checked by Claude in Chrome (read-only on AWS); reviewed by Claude |
| Not covered here | Scale-out / scale-in under load and the rolling update: separate evidence folders |

## Result: 13 of 13 checks passed

Full report: [`qa-report.md`](qa-report.md).

| Check | Screenshots |
|---|---|
| Stack `CREATE_COMPLETE` in 16 minutes, all 30 resources created, no failures | 01, 02 |
| Auto Scaling group: min 1, max 3, two subnets in us-east-1a and us-east-1b, ELB health checks, one healthy server | 03, 04, 06, 07 |
| Two target-tracking policies: CPU 60%, ALB requests per target 300 | 05 |
| Load balancer: default 403; forwards only requests with the `X-Origin-Verify` header (value redacted) | 08, 09 |
| Security groups: internet → ALB :80; ALB → servers :80; servers → RDS :3306; nothing else | 10–12 |
| RDS not publicly accessible | 13 |
| App over HTTPS via CloudFront; direct load-balancer URL refused with 403 | 14, 29 |
| Live Yahoo data; news with sources | 15–18 |
| **Step 12:** discussion saved to RDS, prices and ratios identical to the Compare page (AAPL 331.62, MSFT 521.46) | 19–22 |
| Search by client, `MSFT`, `apple` finds it; `NVDA` does not | 23–27 |
| Clients list counts the discussion | 28 |
| Reopen made no `/api/` requests (network log in the report) | — |

## Observations and follow-up

1. **Origin token seen by the test tool:** the console showed the `X-Origin-Verify` value to the testing assistant (never written to any file or screenshot). Rotated in the next stack update.
2. **Dates were UTC:** the server's "today" was UTC, so a discussion saved at 03:47 SGT on 4 Nov defaulted to 3 Nov. Fixed in the next commit (app uses Asia/Singapore time); deployed by the rolling update.
3. **Servers in public subnets:** by design. The servers need outbound internet (packages, Yahoo Finance) and the sandbox design avoids a NAT gateway; inbound HTTP is accepted only from the load balancer. Documented in `docs/CLOUDFRONT_SANDBOX.md`.
