# Nimbus RM: AWS Academy Sandbox QA report (us-east-1)

**Tester:** Claude (read-only on AWS) · **Run date:** Wed 4 Nov 2026 (SGT) · **Stack:** `nimbus` · **Expected commit:** `378c077f466c07dbd2bd1fdf7deff7753e43ba46`

## 1. Summary

**Overall: PASS. 13 of 13 checks passed.**

- The stack reached **CREATE_COMPLETE at 03:19:07 SGT** (2026-11-04). The start was 03:03, so it took about 16 minutes. 101 events, none `CREATE_FAILED` or `ROLLBACK_*`.
- Three observations need attention (none fails a check). See section 6:
  1. A secret value was exposed during testing, so the origin-verify header value should be rotated.
  2. The app saves discussions with the UTC date, which is 03 Nov while it is already 04 Nov in Singapore.
  3. The web servers run in the same two subnets as the load balancer.

## 2. Pass/fail checks

| Check | Result | Evidence (exact values) |
|---|---|---|
| A1 Stack and resources complete | **PASS** | Stack `CREATE_COMPLETE` at 2026-11-04 03:19:07 UTC+0800. All 30 resources `CREATE_COMPLETE`. 0 failed events. |
| A2 Auto Scaling group | **PASS** | Min 1, Max 3 ("Scaling limits 1 - 3"), Desired 1. Subnets `subnet-0d5806d366dd50eb8` (use1-az6 / us-east-1b) and `subnet-09dbb92a60ddd34fa` (use1-az4 / us-east-1a). Health check type **"EC2, ELB"**, grace 900 s. One instance `i-02f79542bf37ab30e` InService/Healthy; target group shows it Healthy on port 80. |
| A3 Target-tracking policies | **PASS** | `nimbus-CpuScalingPolicy-VKaOsQ0raAF4`: Average CPU utilization at **60**. `nimbus-RequestScalingPolicy-WewMTJ0txdDE`: ALB request count per target at **300**. Both enabled, 300 s warm-up, scale-in enabled. |
| A4 Load balancer rules | **PASS** | Listener HTTP:80. Default: fixed response **403**, "Use the Nimbus CloudFront URL.", text/plain. Rule priority 1: HTTP header **X-Origin-Verify** = (value not recorded) → forward to `nimbus-Targe-JUB07GLEBFRU` (100%). |
| A5 Security groups | **PASS** | alb: 80 from 0.0.0.0/0 (1 rule). web: 80 from `sg-0b9856abd6f620009` (alb SG) and 22 from 127.0.0.1/32 (2 rules). db: 3306 from `sg-0e50408f861cd2aa8` (web SG) (1 rule). No extra inbound rules. |
| A6 RDS not public | **PASS** | Publicly accessible: **No** |
| A7 HTTPS via CloudFront; direct ALB 403 | **PASS** | `https://d1y9ryte1qxb3e.cloudfront.net` loads over https with no browser warning; title "Log in · Nimbus RM". Direct `http://nimbus-LoadB-…elb.amazonaws.com/` returns HTTP **403** with body "Use the Nimbus CloudFront URL." |
| A8 Footer server and commit | **PASS** | "Server i-02f79542bf37ab30e · commit 378c077". This matches the ASG instance and the DeployedCommit output. |
| A9 Live data and news sources | **PASS** | No demo-data banner. News: 5 articles per company, each with headline, source and date (Nov 4, 2026). See notes in section 6. |
| A10 Save once; record matches | **PASS** | Save clicked once → `/discussions/1`. Record shows C-AWS-01, AAPL and MSFT, interests exactly "Dividend income; worried about AI valuations", notes "AWS run 1". Prices and ratios equal step 14 (section 4). |
| A11 Search | **PASS** | Client C-AWS-01 → 1 result. "MSFT" → 1. "apple" → 1. "NVDA" → "No saved discussions match." |
| A12 No /api/ on reopen | **PASS** | After clearing, reloading and opening "Financial ratios & trends" and waiting 5 s: 8 requests, **0** containing `/api/`. |
| A13 Clients list | **PASS** | C-AWS-01 · Discussions **1** · Last spoke 03 Nov 2026 |

## 3. Infrastructure detail

### Stack outputs (all 8)

| Key | Value |
|---|---|
| ApplicationURL | https://d1y9ryte1qxb3e.cloudfront.net |
| AutoScalingGroupName | nimbus-WebServerGroup-NmQLmWZGOn1w |
| CloudFrontDistributionId | E2GWJQNF79XZC |
| DatabaseEndpoint | nimbus-database-ju7odxp6oq48.cdgyu2umrhtq.us-east-1.rds.amazonaws.com |
| DeployedCommit | 378c077f466c07dbd2bd1fdf7deff7753e43ba46 |
| LoadBalancerDNSName | nimbus-LoadB-BzDi8rOYxkLM-211487104.us-east-1.elb.amazonaws.com |
| SnapshotArchiveBucketName | nimbus-snapshotarchivebucket-cxpdiwdaog6s |
| VpcId | vpc-0cf985bc05a2dc973 |

### Resources (30, all CREATE_COMPLETE)

| Logical ID | Type |
|---|---|
| CloudFrontDistribution | AWS::CloudFront::Distribution |
| CloudFrontOriginRequestPolicy | AWS::CloudFront::OriginRequestPolicy |
| CpuScalingPolicy | AWS::AutoScaling::ScalingPolicy |
| Database | AWS::RDS::DBInstance |
| DBSecurityGroup | AWS::EC2::SecurityGroup |
| DBSubnetGroup | AWS::RDS::DBSubnetGroup |
| ForwardFromCloudFront | AWS::ElasticLoadBalancingV2::ListenerRule |
| GatewayAttachment | AWS::EC2::VPCGatewayAttachment |
| InternetGateway | AWS::EC2::InternetGateway |
| LaunchTemplate | AWS::EC2::LaunchTemplate |
| Listener | AWS::ElasticLoadBalancingV2::Listener |
| LoadBalancer | AWS::ElasticLoadBalancingV2::LoadBalancer |
| LoadBalancerSecurityGroup | AWS::EC2::SecurityGroup |
| PrivateRouteTable | AWS::EC2::RouteTable |
| PrivateSubnet1 | AWS::EC2::Subnet |
| PrivateSubnet1RouteTableAssociation | AWS::EC2::SubnetRouteTableAssociation |
| PrivateSubnet2 | AWS::EC2::Subnet |
| PrivateSubnet2RouteTableAssociation | AWS::EC2::SubnetRouteTableAssociation |
| PublicDefaultRoute | AWS::EC2::Route |
| PublicRouteTable | AWS::EC2::RouteTable |
| PublicSubnet | AWS::EC2::Subnet |
| PublicSubnet2 | AWS::EC2::Subnet |
| PublicSubnet2RouteTableAssociation | AWS::EC2::SubnetRouteTableAssociation |
| PublicSubnetRouteTableAssociation | AWS::EC2::SubnetRouteTableAssociation |
| RequestScalingPolicy | AWS::AutoScaling::ScalingPolicy |
| SnapshotArchiveBucket | AWS::S3::Bucket |
| TargetGroup | AWS::ElasticLoadBalancingV2::TargetGroup |
| VPC | AWS::EC2::VPC |
| WebSecurityGroup | AWS::EC2::SecurityGroup |
| WebServerGroup | AWS::AutoScaling::AutoScalingGroup |

### Auto Scaling group `nimbus-WebServerGroup-NmQLmWZGOn1w`

- **Capacity:** desired 1, min 1, max 3. Status: At desired capacity. Created Wed Nov 04 2026 03:13:35 SGT.
- **Launch template:** `LaunchTemplate_xCpf4zDgujpR` (lt-0b99eb97472c914fc), **version 1**. AMI ami-0c230065b91270bc6, t3.micro, security group sg-0e50408f861cd2aa8. User data was not opened.
- **Network:** use1-az6 (us-east-1b) and use1-az4 (us-east-1a). Subnets subnet-0d5806d366dd50eb8 and subnet-09dbb92a60ddd34fa. AZ distribution: balanced best effort.
- **Health checks:** type "EC2, ELB", grace period 900.
- **Other settings:** not protected from scale-in, default termination policy, no lifecycle hooks, no warm pool.

**Policies**

| Name | Type | Metric | Target |
|---|---|---|---|
| nimbus-CpuScalingPolicy-VKaOsQ0raAF4 | Target tracking | Average CPU utilization | 60 |
| nimbus-RequestScalingPolicy-WewMTJ0txdDE | Target tracking | ALB request count per target | 300 |

Predictive scaling policies: 0.

**Instance management**

| Instance | Lifecycle | Type | Launch template / version | AZ | Health |
|---|---|---|---|---|---|
| i-02f79542bf37ab30e | InService | t3.micro | LaunchTemplate_xCpf4zDgujpR / 1 | use1-az6 (us-east-1b) | Healthy |

### Target group `nimbus-Targe-JUB07GLEBFRU`

HTTP:80, target type Instance, attached to load balancer nimbus-LoadB-BzDi8rOYxkLM. Totals: 1 target, 1 healthy, 0 unhealthy, 0 unused, 0 initial, 0 draining.

| Instance | Name | Port | Zone | Health |
|---|---|---|---|---|
| i-02f79542bf37ab30e | nimbus-web | 80 | us-east-1b (use1-az6) | Healthy |

Health check settings: HTTP, path `/api/health`, traffic port, healthy threshold 2, unhealthy threshold 3, timeout 5 s, interval 15 s, success code 200.

### Load balancer `nimbus-LoadB-BzDi8rOYxkLM`

- **Basics:** Application, **Internet-facing**, Active, IPv4. VPC vpc-0cf985bc05a2dc973. Created Nov 4 2026 03:02 SGT.
- **AZs:** subnet-0d5806d366dd50eb8 (us-east-1b) and subnet-09dbb92a60ddd34fa (us-east-1a).
- **Security group:** sg-0b9856abd6f620009 (nimbus-LoadBalancerSecurityGroup-nthAqgjqYU1L).

**Listener rules (HTTP:80, the only listener)**

| Priority | Condition | Action |
|---|---|---|
| 1 | HTTP header **X-Origin-Verify** = *(value not recorded)* | Forward to target group nimbus-Targe-JUB07GLEBFRU, weight 1 (100%), stickiness off |
| Last (default) | If no other rule applies | Return fixed response 403, "Use the Nimbus CloudFront URL.", text/plain |

### Security groups (inbound rules)

| Name tag | Group ID / name | Port | Source | Description |
|---|---|---|---|---|
| nimbus-alb-sg | sg-0b9856abd6f620009 / nimbus-LoadBalancerSecurityGroup-nthAqgjqYU1L | TCP 80 | 0.0.0.0/0 | HTTP from CloudFront; requests without the origin token get 403. |
| nimbus-web-sg | sg-0e50408f861cd2aa8 / nimbus-WebSecurityGroup-QnBTfDMA0kDs | TCP 80 | sg-0b9856abd6f620009 (alb SG) | HTTP from the load balancer only. |
| nimbus-web-sg | (same) | TCP 22 | 127.0.0.1/32 | Optional SSH, restricted to the configured admin CIDR. |
| nimbus-db-sg | sg-0416dea4487872d2f / nimbus-DBSecurityGroup-j1XPnOf6tLzW | TCP 3306 | sg-0e50408f861cd2aa8 (web SG) | MySQL from web tier only |

Each security group has one outbound rule. The RDS page lists the DB security group's outbound rule as 0.0.0.0/0.

### RDS `nimbus-database-ju7odxp6oq48`

| Setting | Value |
|---|---|
| Publicly accessible | **No** |
| VPC security group | nimbus-DBSecurityGroup-j1XPnOf6tLzW (sg-0416dea4487872d2f), Active |
| Subnet group | nimbus-dbsubnetgroup-a74pzww70z2f (subnet-00aece597855b60c1, subnet-0c2ff9799d09e43a0) |
| Multi-AZ | No |
| Engine / version | MySQL Community **8.4.11** |
| Other | db.t3.micro, us-east-1b, port 3306, IPv4, storage encrypted (aws/rds), gp2 20 GiB, deletion protection Disabled, status Available |

## 4. Compare page (step 14) vs saved record (step 16)

Compare inputs were "AAPL, MSFT" with period 1y; the resulting URL was `/compare?tickers=AAPL%2CMSFT&period=1y`. No demo-data banner was shown.

| Field | AAPL compare | AAPL saved | MSFT compare | MSFT saved |
|---|---|---|---|---|
| Last price / price at discussion | USD 331.62 | USD 331.62 | USD 521.46 | USD 521.46 |
| Price date | n/a | 03 Nov 2026 | n/a | 03 Nov 2026 |
| Source | Yahoo Finance | Yahoo Finance | Yahoo Finance | Yahoo Finance |
| Revenue growth (YoY) | +6.4% | +6.4% | +17.8% | +17.8% |
| Net profit margin | 26.9% | 26.9% | 40.3% | 40.3% |
| Debt-to-equity | 1.34× | 1.34× | 0.13× | 0.13× |
| Fiscal year | 2025 | 2025 | 2026 | 2026 |

Other values on the Compare page:

- **AAPL:** 1y return +23.7%, volatility 24.2%, max drawdown −13.8%, market cap 4.84T. Consensus Buy (38 analysts), mean target USD 333.44, upside +0.4%.
- **MSFT:** 1y return +1.7%, volatility 33.0%, max drawdown −31.3%, market cap 3.87T. Consensus Strong Buy (53 analysts), mean target USD 633.13, upside +21.5%.

**News check:** every article showed a headline, source and date. Sources were:

- **AAPL:** MT Newswires, Yahoo Finance RSS (publisher not given) ×2, Investing.com, Motley Fool.
- **MSFT:** Insider Monkey, GuruFocus.com, Yahoo Finance RSS (publisher not given) ×3.

**Save (step 15):**

- **Form values:** client "+ New client…", code C-AWS-01, name AWS Test Client. Discussion date was left at the form default, 2026-11-03. Segment and risk profile were blank. Interests and notes were entered as specified.
- **Success message:** "Saved the discussion with C-AWS-01 · AWS Test Client. This is the record as saved; reopening it never fetches new data."
- **Historical snapshot banner:** "Historical snapshot. Everything on this page is exactly as saved on 03 Nov 2026, 19:47 UTC (market data retrieved 03 Nov 2026, 19:45 UTC). It is not refreshed. Source: Yahoo Finance."
- **Saved record:** header "AWS Test Client · 03 Nov 2026" and "C-AWS-01 · AAPL, MSFT · period 1y". Interests "Dividend income; worried about AI valuations", notes "AWS run 1". Footer "Server i-02f79542bf37ab30e · commit 378c077".

## 5. Search results, server IDs and Activity history

**Search (step 17)**

| Search | Result |
|---|---|
| Client = C-AWS-01 | 1 row: 03 Nov 2026 · AWS Test Client C-AWS-01 · AAPL USD 331.62, MSFT USD 521.46 · "Dividend income; worried about AI valuations" |
| Company = MSFT | Same 1 row |
| Company = apple | Same 1 row; "Open" opened `/discussions/1` correctly |
| Company = NVDA | "No saved discussions match." |

**Footer server ID across 5 reloads of `/discussions/1` (step 18)**

| Reload | Footer |
|---|---|
| 1 | Server i-02f79542bf37ab30e · commit 378c077 |
| 2 | Server i-02f79542bf37ab30e · commit 378c077 |
| 3 | Server i-02f79542bf37ab30e · commit 378c077 |
| 4 | Server i-02f79542bf37ab30e · commit 378c077 |
| 5 | Server i-02f79542bf37ab30e · commit 378c077 |

The server ID stayed the same, which is expected with one instance.

**Clients list (step 19):** C-AWS-01 · AWS Test Client · segment — · risk — · Discussions 1 · Stock notes 0 · Last spoke 03 Nov 2026.

**Network requests (step 20):** after clearing, reloading and opening "Financial ratios & trends", then waiting 5 s, the page made these 8 requests:

1. `/discussions/1` (200)
2. fonts.googleapis.com CSS
3. `/static/css/style.css`
4–6. Three fonts.gstatic.com woff2 files
7. cdnjs Chart.js 4.4.1
8. `/static/js/compare.js`

None contained `/api/`.

**ASG Activity history (exact text)**

> Successful | Launching a new EC2 instance: i-02f79542bf37ab30e | At 2026-11-03T19:13:36Z a user request update of AutoScalingGroup constraints to min: 1, max: 3, desired: 1 changing the desired capacity from 0 to 1. At 2026-11-03T19:13:38Z an instance was started in response to a difference between desired and actual capacity, increasing the capacity from 0 to 1. | Start 2026 November 04, 03:13:40 AM +08:00 | End 2026 November 04, 03:18:45 AM +08:00

## 6. Errors, warnings, banners and anything unexpected

1. **Secret exposure (action recommended).** When I read the listener-rules table, the console text included the `X-Origin-Verify` header **value**, and it appeared in my tool output. It was not copied into this report, my notes or any screenshot; the listener-rules screenshot was taken after blanking it on the page. Because the value was displayed, consider rotating the origin-verify secret.
2. **Date mismatch.** The app treats "today" as UTC. The dashboard said "Tuesday, 03 November 2026" and the save form defaulted to 2026-11-03, while it was already 04 Nov in Singapore. The record therefore shows 03 Nov 2026 and the saved time 19:47 UTC, which is 03:47 SGT on 04 Nov.
3. **Web server subnets.** The ASG instances are in the same two subnets as the internet-facing load balancer (subnet-0d58…, subnet-09db…), while RDS uses separate subnets. I didn't check whether those subnets are public. The web security group still allows only the ALB on port 80 and SSH from 127.0.0.1/32.
4. **News fallback.** For both companies the page showed: "Via Yahoo Finance search + RSS — Yahoo's ticker news feed returned nothing, so these come from Yahoo search (only articles linked to the ticker that name the company) and Yahoo's RSS feed." Five of the ten articles list "Yahoo Finance RSS (publisher not given)".
5. **Health check type** displays as "EC2, ELB". ELB health checks are on, as A2 requires.
6. **Other resources in the account.** The EC2 dashboard showed 3 running instances, 3 ASGs, 3 load balancers and 10 security groups in us-east-1. Some belong to the lab, for example "Lab Instance SG". Only the `nimbus` resources were tested.
7. **Test-run issues on my side, not app defects:**
   - **Step 11:** the first try of the direct ALB URL showed a Chrome error page (`chrome-error://chromewebdata/`). The retry later returned the 403 page normally.
   - **Extension instability:** around 03:40–03:47 SGT the browser extension switched between two tab groups, and screenshots failed. A first Compare attempt was made in a tab that disappeared. Compare does not save, and the Discussions list confirms exactly one record, `/discussions/1`.
   - **No logged-in Dashboard screenshot:** screenshots were failing at that point. Its footer text was recorded instead, and the footer also appears in screenshots 22, 24–29.
8. **Sandbox timer:** not visible from the AWS console pages used, so it was not checked.
9. **Not opened, as instructed:** the stack Parameters tab and the launch template user data.

## Screenshots (in `nimbus_qa_screenshots.zip`)

01_stack_create_complete · 02_stack_outputs · 03_asg_details_capacity · 04_asg_details_network_healthchecks · 05_asg_automatic_scaling · 06_asg_instance_management · 07_target_group_targets · 08_alb_listeners · 09_alb_listener_rules_redacted · 10_sg_alb_inbound · 11_sg_web_inbound · 12_sg_db_inbound · 13_rds_connectivity · 14_app_login_page · 15_compare_form · 16_compare_summary · 17_compare_key_financials · 18_compare_news · 19_save_form · 20_saved_discussion_top · 21_saved_discussion_table · 22_saved_discussion_footer · 23_search_client_form · 24_search_client_results · 25_search_MSFT · 26_search_apple · 27_search_NVDA_no_match · 28_clients_list · 29_alb_direct_403
