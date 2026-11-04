# Nimbus RM on the AWS Academy sandbox

> **The sandbox deletes everything when its session ends**: the stack, the database and every saved discussion. Plan each AWS task (demo, evidence recording, presentation) to fit inside **one** session, and create the stack fresh at the start. Creation took 13–16 minutes in our runs.

One CloudFormation stack, [`infra/nimbus-merged-stack.yaml`](../infra/nimbus-merged-stack.yaml), creates the network, a load balancer, an Auto Scaling group of application servers, the private RDS database and the CloudFront distribution. It targets the AWS Academy sandbox described in [`AWS_ACADEMY_SANDBOX_LIMITATIONS.txt`](AWS_ACADEMY_SANDBOX_LIMITATIONS.txt) and must be deployed in **us-east-1**.

## Architecture

```text
Browser --HTTPS--> CloudFront --HTTP + origin token--> Application Load Balancer (2 AZs)
                                                           | forwards only with the token
                                                           v
                                         Auto Scaling group: 1 to 3 EC2 servers
                                         (Nginx -> Gunicorn -> Flask), 2 public subnets
                                                           |
                                                           v MySQL :3306
                                         Amazon RDS MySQL, 2 private subnets (single-AZ)
```

CloudFront provides HTTPS at its generated `*.cloudfront.net` hostname, so no domain, Route 53 or custom certificate is needed. Scaling follows the course's Lab 6 pattern: launch template, Auto Scaling group across two Availability Zones behind an Application Load Balancer, and target-tracking policies on CloudWatch metrics.

## Deploy (first time)

1. Start the lab and check that the Region is **us-east-1**.
2. Make sure the commit you want is pushed to the public GitHub repository, and copy its hash (`git rev-parse HEAD`, or the commit link on GitHub).
3. Generate three random values on your own computer (never commit them):

   ```bash
   python3 -c "import secrets; print('AppSecretKey=' + secrets.token_hex(32)); print('OriginVerifyToken=' + secrets.token_hex(32)); print('DBPassword=' + secrets.token_hex(20))"
   ```

4. **CloudFormation → Create stack → Upload a template file** → `infra/nimbus-merged-stack.yaml`. Stack name: `nimbus`.
5. Parameters:
   - **RepositoryUrl**: the public repository URL, e.g. `https://github.com/pujoglekar2026/DS600-Group-Proj`.
   - **GitCommit**: the hash from step 2.
   - **AppSecretKey**, **OriginVerifyToken**, **DBPassword**: the values from step 3.
   - Leave the rest at their defaults (`t3.micro`, CPU target 60%, 300 requests per server per minute). Leave **KeyName** empty and use Session Manager unless you need SSH.
6. Submit and wait for `CREATE_COMPLETE` (about 20–25 minutes; RDS and CloudFront take the longest). The stack completes only after a server has installed the app and signalled that it is healthy.
7. Open the **ApplicationURL** output. If Chrome warns, check the address starts with `https://`. Register a login on the Register page (or seed demo data with Session Manager: `cd /opt/nimbus && sudo -u nimbus .venv/bin/flask --app wsgi seed-demo`).
8. The page footer shows **Server i-… · commit …**: which server answered and which commit it runs.

## Deploy new code (rolling update)

**Update stack → Use current template** → change only **GitCommit** → submit.

The launch template gets a new version, and the Auto Scaling group replaces the servers **one at a time**: it starts a server with the new commit, waits for its success signal, then removes an old one. (While it does this, CloudFormation temporarily raises the group's minimum to 2; it returns to 1 afterwards.) The load balancer keeps sending traffic to healthy servers throughout, and the database is not touched. When the update completes, the footer shows the new commit.

**Never delete the stack to redeploy:** RDS has `DeletionPolicy: Delete`, so deleting the stack deletes every saved discussion.

## Recording the Feature 6 scaling evidence

The instructor accepts recorded evidence kept in the repository (decision D-02). Save everything in `docs/evidence/<date>-scaling/`, with a `README.md` naming the stack's **DeployedCommit** output. Because the sandbox is wiped at the end of the session, **do all of this in the same session as creating the stack**, and keep the steps moving.

| Step | Typical time |
|---|---|
| Create the stack | 15 min |
| Register, save one discussion | 5 min |
| Load until 2–3 servers are healthy | 10–15 min |
| Reopen the discussion from two servers | 5 min |
| Stop load, wait for scale-in | 15–25 min |
| **Total** | **about 60–70 min** (start with at least 90 min on the session timer) |

1. **Before:** screenshot **EC2 → Auto Scaling groups → (AutoScalingGroupName output)**: *Desired 1, Min 1, Max 3*, and the **Automatic scaling** tab showing both target-tracking policies.
2. **Save a discussion** in the app (Compare two companies → Save this discussion) and note the footer's server ID.
3. **Generate load from your laptop**, not CloudShell. CloudShell ends its session after about 15 minutes without a keypress, which stops anything running in it. In the project folder, with the virtual environment active:

   ```bash
   python scripts/load_test.py https://dxxxxxxxxxxxx.cloudfront.net --minutes 20
   ```

   It sends thousands of requests per minute (well above the 300 requests per server per minute target) and prints, every 30 seconds, the request rate, the responses, and which servers answered. Keep its output for the evidence README.
4. **Scale-out:** within about 3–5 minutes the request alarm goes into *In alarm* (CloudWatch → Alarms, names start with `TargetTracking-`). The group's **Activity** tab shows *Launching a new EC2 instance*, and **Instance management** shows 2–3 instances. **Target groups → Targets** shows them becoming *healthy* (5–9 minutes each). The load script's "servers" list grows at the same time. Screenshot each.
5. **Any server reopens any discussion:** while two or more servers are healthy, open **Discussions → Open** on the saved discussion and reload a few times. The footer's server ID changes while the record stays identical. Screenshot two different server IDs with the same record.
6. **Scale-in:** stop the load (Ctrl+C, or let it finish). About 15 minutes later the low-load alarm fires and the Activity tab shows *Terminating EC2 instance*, back to 1. Screenshot it.
7. Copy the Activity history text into the evidence README. Any change you make by hand to *Desired capacity* must be labelled **manual**, separately from this automatic test.

## Presentation-day checklist

Nothing from earlier sessions exists on the day, so:

1. **45 minutes before:** start the sandbox (check the session timer covers the whole presentation) and create the stack from the team repository with the final commit (see *Deploy (first time)*). Generate fresh secrets.
2. **When `CREATE_COMPLETE`:** open the ApplicationURL, register a login, and run one comparison so the market data is cached.
3. **During the demo:** Compare → Save this discussion → Discussions search → Open. Show the footer (server and commit) and the Auto Scaling group page.
4. **For scaling:** show the recorded evidence in `docs/evidence/` (scale-out takes too long to show live).
5. **Afterwards:** nothing to clean up; the sandbox deletes everything when the session ends.

## Why these resources and settings

| Resource or setting | Reason |
|---|---|
| CloudFormation | Reproducible setup, rolling code updates and teardown of everything the sandbox permits. |
| CloudFront, caching disabled | Public HTTPS endpoint with the default certificate. Pages are personalised and use session cookies and query parameters, so nothing is cached and cookies and query strings are forwarded. |
| Origin verification header | CloudFront adds a secret header; the load balancer's listener forwards only requests carrying it (others get 403), and Nginx checks it again. Only `/api/health` is open on the servers, because load balancer health checks cannot add headers; it reveals only whether the app and database are up. |
| Application Load Balancer, two public subnets | Spreads requests across servers in two Availability Zones and removes unhealthy servers from service (health check every 15 s on `/api/health`, which also checks the database). A load balancer must span at least two AZs. |
| Launch template + Auto Scaling group, 1–3 servers | Feature 6: capacity grows and shrinks with demand. Maximum 3 stays within the sandbox's instance limits; minimum 1 keeps the app always available. Servers are replaced automatically if they fail the health check. |
| Two target-tracking policies | CPU 60% (the Lab 6 metric) catches heavy work such as many comparisons; requests per server catches many light requests. The group scales out if either is above target and scales in only when both are below. |
| Rolling update on `GitCommit` | Deploys an exact, recorded commit. One server at a time, each must signal success first, so updates cause no downtime and keep the database. |
| No sticky sessions | Logins are signed cookies and saved discussions are in RDS, so any server can answer any request. |
| Servers in public subnets, no NAT gateway | Servers need outbound internet to clone the repository, install packages and call Yahoo Finance. A public subnet with an Internet Gateway avoids NAT gateway cost. Their security group accepts HTTP only from the load balancer. |
| Existing `LabInstanceProfile` | IAM is read-only in the sandbox, so the template cannot create a role. The profile allows Session Manager access and S3 for the archive. |
| RDS MySQL in private subnets, single-AZ | No public endpoint; MySQL is accepted only from the servers' security group. The subnet group needs two AZs, but the sandbox does not allow Multi-AZ databases. |
| Connection limits per server | Each Gunicorn worker keeps at most 3 + 2 MySQL connections: 3 workers × 3 servers stays inside a `db.t3.micro`'s limit. |
| Archive lock | Every server has the monthly archive timer; a MySQL named lock lets only one of them run it. |
| `t3.micro`, gp2, `PriceClass_100` | Within sandbox limits (Auto Scaling groups may use t2/t3 nano to small) and low cost. |

## Considerations and limitations

- **Session reset:** the sandbox deletes all resources, including the database, when the session timer reaches 0:00. Saved discussions do not survive between sessions; this is a property of the course sandbox, not of the design (in a normal AWS account the stack and RDS persist).
- **Timing:** a new server needs about 5–9 minutes to install the app, and target tracking waits about 15 minutes of low load before removing servers. Record the scaling test in advance rather than live.
- **Deleting the stack** deletes the database. The snapshot archive bucket is retained until the sandbox session ends.
- **Snapshot archive:** a monthly timer moves stock notes whose `discussed_on` date is more than five years old from RDS to private, SSE-S3-encrypted S3 objects, verifying each object before deleting the row; S3 moves them to Glacier Flexible Retrieval after 30 days. Run it now with Session Manager: `sudo -u nimbus /opt/nimbus/.venv/bin/flask --app wsgi archive-snapshots`. Confirm `LabInstanceProfile` allows `s3:PutObject` and `s3:GetObject` on the bucket; otherwise the job fails without deleting anything.
- **Secrets:** CloudFormation `NoEcho` hides parameter values in most displays, but the values are in the launch template's user data, readable by anyone with console access to it. Use generated secrets, never commit them, and delete the stack after the course.
- **Per-server cache:** each server caches market data for 15 minutes in its own memory, so two servers may each fetch the same figures once. Saved discussions are unaffected: they are read from RDS.
- **CloudFront delay:** distribution creation and updates take several minutes; wait for **Deployed** before testing.
- **Market data:** Yahoo Finance may rate-limit cloud servers. Nimbus never saves demo data into a client record and labels it wherever it is shown.
- **Production gap:** a production system would use private subnets with a NAT gateway or VPC endpoints for the servers, HTTPS between CloudFront and the load balancer, managed secrets, Multi-AZ RDS with backups, and alarms that notify people.

To clean up, delete the CloudFormation stack and wait until deletion completes. This removes CloudFront, the load balancer, the servers and the database, but keeps the archive bucket.
