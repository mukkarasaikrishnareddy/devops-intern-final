#!/usr/bin/env python3
"""
send_logs.py – Push a log entry to Loki and query it back.

This script uses ONLY Python standard-library modules.
It demonstrates the complete Loki log ingestion and retrieval cycle
using the Loki HTTP push API and query API.

Prerequisites:
  Loki must be running locally on port 3100.

  Start Loki with Docker:
    docker run -d --name loki -p 3100:3100 \\
      grafana/loki:latest \\
      -config.file=/etc/loki/local-config.yaml

  Wait for Loki to be ready:
    curl http://localhost:3100/ready   # should return: ready

Usage:
  python monitoring/send_logs.py

Exit codes:
  0  – Push and query both succeeded; log entry was found in Loki.
  1  – Push failed, query failed, or log entry was not found.
"""

import json
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from datetime import datetime, timezone

LOKI_BASE = "http://localhost:3100"
PUSH_URL  = f"{LOKI_BASE}/loki/api/v1/push"
QUERY_URL = f"{LOKI_BASE}/loki/api/v1/query_range"
READY_URL = f"{LOKI_BASE}/ready"

JOB_LABEL = "devops-hello"
LOG_LINE   = "DevOps application running on port 8080 [send_logs.py test]"


# ──────────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────────

def ts_ns() -> str:
    """Return current UTC time as a Unix nanosecond timestamp string."""
    return str(int(time.time() * 1_000_000_000))


def http_get(url: str) -> tuple[int, str]:
    try:
        with urllib.request.urlopen(url, timeout=5) as resp:
            return resp.status, resp.read().decode("utf-8")
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")
    except Exception as e:
        return 0, str(e)


def http_post_json(url: str, payload: dict) -> tuple[int, str]:
    data = json.dumps(payload).encode("utf-8")
    req  = urllib.request.Request(
        url,
        data=data,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=5) as resp:
            body = resp.read().decode("utf-8")
            return resp.status, body
    except urllib.error.HTTPError as e:
        return e.code, e.read().decode("utf-8")
    except Exception as e:
        return 0, str(e)


# ──────────────────────────────────────────────────────────────────
# Steps
# ──────────────────────────────────────────────────────────────────

def check_loki_ready() -> bool:
    print(f"\n[1/3] Checking Loki readiness at {READY_URL} ...")
    for attempt in range(1, 16):
        status, body = http_get(READY_URL)
        body_str = body.strip()
        if status == 200 and body_str == "ready":
            print(f"      OK – Loki is ready (HTTP {status}, body='{body_str}')")
            return True
        print(f"      Waiting for Loki readiness (attempt {attempt}/15, status={status}, body='{body_str}')...")
        time.sleep(2)

    print(f"      FAIL – Loki did not become ready in 30 seconds.")
    print("      Make sure Loki is running:")
    print("        docker run -d --name loki -p 3100:3100 \\")
    print("          grafana/loki:latest \\")
    print("          -config.file=/etc/loki/local-config.yaml")
    return False


def push_log() -> str | None:
    """Push a single log line. Returns the timestamp used, or None on failure."""
    timestamp = ts_ns()
    print(f"\n[2/3] Pushing log to Loki at {PUSH_URL} ...")
    print(f"      Stream : {{job: \"{JOB_LABEL}\"}}")
    print(f"      Message: {LOG_LINE}")
    print(f"      Time   : {timestamp} ns")

    payload = {
        "streams": [
            {
                "stream": {"job": JOB_LABEL},
                "values": [[timestamp, LOG_LINE]],
            }
        ]
    }

    status, body = http_post_json(PUSH_URL, payload)
    if status == 204:
        print(f"      OK – Loki accepted the log (HTTP {status} No Content)")
        return timestamp
    else:
        print(f"      FAIL – HTTP {status}, body='{body}'")
        return None


def query_log(pushed_at_ns: str) -> bool:
    """Query Loki for the log line we just pushed."""
    # Give Loki a moment to index the entry
    time.sleep(2)

    # Search from 60 s before the push to now
    start_ns = str(int(pushed_at_ns) - 60 * 1_000_000_000)
    end_ns   = str(int(time.time() * 1_000_000_000) + 5 * 1_000_000_000)

    params = urllib.parse.urlencode({
        "query": f'{{job="{JOB_LABEL}"}}',
        "start": start_ns,
        "end":   end_ns,
        "limit": "10",
    })
    url = f"{QUERY_URL}?{params}"

    print(f"\n[3/3] Querying Loki: job=\"{JOB_LABEL}\" ...")
    print(f"      URL: {url}")

    status, body = http_get(url)
    if status != 200:
        print(f"      FAIL – HTTP {status}, body='{body}'")
        return False

    try:
        data = json.loads(body)
    except json.JSONDecodeError as e:
        print(f"      FAIL – could not parse JSON: {e}")
        return False

    print("\n      Raw Loki response:")
    print("      " + json.dumps(data, indent=2).replace("\n", "\n      "))

    results = data.get("data", {}).get("result", [])
    if not results:
        print("\n      FAIL – query returned no log streams")
        return False

    found = False
    for stream in results:
        for ts, line in stream.get("values", []):
            if LOG_LINE in line:
                found = True
                ts_human = datetime.fromtimestamp(
                    int(ts) / 1_000_000_000, tz=timezone.utc
                ).isoformat()
                print(f"\n      FOUND log entry:")
                print(f"        Timestamp : {ts_human}")
                print(f"        Message   : {line}")
                break

    if found:
        print("\n      OK – Log entry confirmed in Loki.")
    else:
        print("\n      FAIL – Log line not found in query results.")

    return found


# ──────────────────────────────────────────────────────────────────
# Main
# ──────────────────────────────────────────────────────────────────

def main():
    print("=" * 60)
    print("  Loki Log Push & Query Demo – DevOps Assessment")
    print(f"  {datetime.now(timezone.utc).isoformat()}")
    print("=" * 60)

    if not check_loki_ready():
        print("\nABORTED – Loki is not available.")
        sys.exit(1)

    pushed_at = push_log()
    if pushed_at is None:
        print("\nABORTED – Push failed.")
        sys.exit(1)

    success = query_log(pushed_at)

    print("\n" + "=" * 60)
    if success:
        print("  RESULT: SUCCESS – Log was pushed to and retrieved from Loki.")
        print("=" * 60)
        sys.exit(0)
    else:
        print("  RESULT: FAIL – Log was not confirmed in Loki query.")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()
