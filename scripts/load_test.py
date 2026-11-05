"""Send steady HTTP load to Nimbus to trigger auto scaling (Feature 6 evidence).

Runs on your own laptop (Python 3.10+, standard library only), so it is not
cut off by CloudShell's inactivity timeout. Example, for 20 minutes:

    python scripts/load_test.py https://dxxxxxxxxxxxx.cloudfront.net --minutes 20

It requests the public login page, which goes CloudFront -> load balancer ->
a server, and prints a summary every 30 seconds, including which servers
answered (from the page footer). Press Ctrl+C to stop early.
"""
import argparse
import re
import threading
import time
import urllib.request
from collections import Counter

SERVER_RE = re.compile(rb"Server (i-[0-9a-z]+)")


def worker(url, stop_at, stats, lock):
    while time.time() < stop_at:
        code, server = "error", None
        try:
            with urllib.request.urlopen(url, timeout=15) as resp:
                body = resp.read()
                code = str(resp.status)
                m = SERVER_RE.search(body)
                server = m.group(1).decode() if m else None
        except urllib.error.HTTPError as exc:
            code = str(exc.code)
        except Exception:
            pass
        with lock:
            stats["codes"][code] += 1
            if server:
                stats["servers"][server] += 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("app_url", help="the stack's ApplicationURL, e.g. https://dxxxx.cloudfront.net")
    ap.add_argument("--minutes", type=float, default=20)
    ap.add_argument("--threads", type=int, default=20)
    args = ap.parse_args()
    url = args.app_url.rstrip("/") + "/login"
    stop_at = time.time() + args.minutes * 60
    stats = {"codes": Counter(), "servers": Counter()}
    lock = threading.Lock()
    for _ in range(args.threads):
        threading.Thread(target=worker, args=(url, stop_at, stats, lock), daemon=True).start()

    print(f"Sending load to {url} with {args.threads} threads for {args.minutes:g} minutes. Ctrl+C to stop.")
    last_total = 0
    try:
        while time.time() < stop_at:
            interval = max(1.0, min(30.0, stop_at - time.time()))
            time.sleep(interval)
            with lock:
                total = sum(stats["codes"].values())
                codes = dict(stats["codes"])
                servers = dict(stats["servers"])
                stats["servers"].clear()
            rate = (total - last_total) / interval
            last_total = total
            print(f"{time.strftime('%H:%M:%S')}  {rate * 60:,.0f} requests/min  "
                  f"responses so far {codes}  servers since last line: {len(servers)} {sorted(servers)}")
    except KeyboardInterrupt:
        print("Stopped.")
    with lock:
        print(f"Total responses: {dict(stats['codes'])}")


if __name__ == "__main__":
    main()
