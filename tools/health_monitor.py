#!/usr/bin/env python3
"""Health monitor for ButterflyGuy trading services.

Polls /health endpoints on all three services (SPX, NDX, XSP) and sends
Discord webhook alerts on failure / recovery.

Usage:
    python tools/health_monitor.py                  # daemon mode (runs forever)
    python tools/health_monitor.py --once            # single check cycle
    python tools/health_monitor.py --config path     # read config from YAML

Configuration via environment variables (or YAML):
    HEALTH_CHECK_URLS     - comma-separated health endpoints
    DISCORD_WEBHOOK_URL   - Discord webhook URL for alerts
    CHECK_INTERVAL        - seconds between checks (default: 300)
    FAILURE_THRESHOLD     - consecutive failures before alerting (default: 2)
"""

from __future__ import annotations

import argparse
import json
import os
import signal
import sys
import time
import urllib.error
import urllib.request

try:
    import yaml
except ImportError:  # pragma: no cover
    yaml = None  # type: ignore[assignment]


DEFAULT_CHECK_URLS = (
    "http://localhost:8000/health,"
    "http://localhost:8001/health,"
    "http://localhost:8002/health,"
    "http://localhost:8003/health"
)
DEFAULT_CHECK_INTERVAL = 300  # 5 minutes
DEFAULT_FAILURE_THRESHOLD = 2

# Per-service state
_health_state: dict[str, dict] = {}
_shutdown = False


def _now_et() -> str:
    """Return current time as Eastern Time, handling DST correctly."""
    from datetime import datetime, timezone, timedelta

    now = datetime.now(timezone.utc)
    year = now.year

    # Compute second Sunday of March (DST start: 2am ET = 7am UTC)
    march_1 = datetime(year, 3, 1, tzinfo=timezone.utc)
    first_sun = march_1 + timedelta(days=(6 - march_1.weekday()))
    dst_start = first_sun + timedelta(days=7)
    dst_start = dst_start.replace(hour=7, minute=0, second=0, microsecond=0)

    # Compute first Sunday of November (DST end: 2am ET -> 1am ET = 6am UTC)
    nov_1 = datetime(year, 11, 1, tzinfo=timezone.utc)
    dst_end = nov_1 + timedelta(days=(6 - nov_1.weekday()))
    dst_end = dst_end.replace(hour=6, minute=0, second=0, microsecond=0)

    offset = timedelta(hours=-4) if dst_start <= now < dst_end else timedelta(hours=-5)
    et = now + offset
    return et.strftime("%Y-%m-%d %H:%M:%S")


def load_config(config_path: str | None) -> dict:
    """Load configuration from YAML file, falling back to env vars."""
    cfg: dict = {}

    if config_path and yaml is not None:
        with open(config_path) as f:
            cfg = yaml.safe_load(f) or {}

    # Env vars override YAML
    def _env_or(key: str, default: str) -> str:
        env_key = key.upper()
        return os.environ.get(env_key, cfg.get(key, default))

    urls_str = _env_or("health_check_urls", DEFAULT_CHECK_URLS)
    urls = [u.strip() for u in urls_str.split(",") if u.strip()]

    return {
        "urls": urls,
        "discord_webhook": os.environ.get("DISCORD_WEBHOOK_URL", cfg.get("discord_webhook_url", "")),
        "check_interval": int(os.environ.get("CHECK_INTERVAL", cfg.get("check_interval", DEFAULT_CHECK_INTERVAL))),
        "failure_threshold": int(os.environ.get("FAILURE_THRESHOLD", cfg.get("failure_threshold", DEFAULT_FAILURE_THRESHOLD))),
    }


def check_endpoint(url: str) -> dict:
    """GET a health URL and return result dict with status, error, etc."""
    result: dict = {"url": url, "healthy": False, "error": None, "data": None}
    req = urllib.request.Request(url, method="GET", headers={"Accept": "application/json"})
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        body = resp.read().decode("utf-8")
        if resp.status == 200:
            data = json.loads(body)
            if isinstance(data, dict) and data.get("status") == "ok":
                result["healthy"] = True
                result["data"] = data
            else:
                result["error"] = f"Unexpected health body: {body[:200]}"
        else:
            result["error"] = f"HTTP {resp.status}: {body[:200]}"
    except json.JSONDecodeError as e:
        result["error"] = f"Invalid JSON: {e}"
    except urllib.error.HTTPError as e:
        result["error"] = f"HTTP {e.code}"
    except urllib.error.URLError as e:
        result["error"] = f"Connection failed: {e.reason}"
    except TimeoutError:
        result["error"] = "Timeout after 10s"
    except OSError as e:
        result["error"] = f"OS error: {e}"
    return result


def extract_service_name(url: str, result: dict | None = None) -> str:
    """Derive a human-readable service name from a health URL.

    Prefers the ``service`` field returned by the /health endpoint when
    available; falls back to port-based lookup for unreachable services.
    """
    # If the endpoint responded, use the name it reports
    if result and result.get("data") and isinstance(result["data"], dict):
        reported = result["data"].get("service")
        if reported:
            return str(reported)

    # Fallback: port-based guess for down/unreachable endpoints
    port_map = {"8000": "SPX", "8001": "NDX", "8002": "SPX-2", "8003": "XSP"}
    for port, name in port_map.items():
        if f":{port}" in url:
            return name
    # Last resort: host:port part
    parts = url.split("://", 1)[-1].split("/")[0]
    return parts


def send_discord_alert(webhook_url: str, message: str) -> None:
    """Post a message to Discord webhook."""
    if not webhook_url:
        return
    payload = json.dumps({"content": message}).encode("utf-8")
    req = urllib.request.Request(
        webhook_url,
        data=payload,
        method="POST",
        headers={"Content-Type": "application/json"},
    )
    try:
        resp = urllib.request.urlopen(req, timeout=10)
        if resp.status not in (200, 204):
            print(f"[WARN] Discord webhook returned {resp.status}", file=sys.stderr)
    except Exception as e:
        print(f"[WARN] Discord webhook failed: {e}", file=sys.stderr)


def run_check_cycle(cfg: dict) -> list[dict]:
    """Run one full check cycle across all URLs. Returns list of results."""
    results = []
    for url in cfg["urls"]:
        result = check_endpoint(url)
        service_name = extract_service_name(url, result)
        key = service_name

        # Initialize state for this service if not tracked
        if key not in _health_state:
            _health_state[key] = {"was_healthy": True, "fail_count": 0, "last_down_time": None}

        state = _health_state[key]

        if result["healthy"]:
            if not state["was_healthy"]:
                # Recovery!
                downtime = "unknown"
                if state["last_down_time"]:
                    downtime_secs = int(time.time() - state["last_down_time"])
                    mins = downtime_secs // 60
                    downtime = f"~{mins} min" if mins < 120 else f"~{mins // 60}h {mins % 60}m"
                msg = (
                    f"✅ **ButterflyGuy Service Recovered**\n"
                    f"**Service:** {service_name} ({url})\n"
                    f"**Downtime:** {downtime}\n"
                    f"**Time:** {_now_et()} ET"
                )
                send_discord_alert(cfg["discord_webhook"], msg)
                print(f"[RECOVERY] {key} is back up")
            state["was_healthy"] = True
            state["fail_count"] = 0
            result["service"] = service_name
        else:
            state["fail_count"] += 1
            result["service"] = service_name
            if state["fail_count"] >= cfg["failure_threshold"] and state["was_healthy"]:
                # Transition: healthy → unhealthy at threshold
                state["was_healthy"] = False
                state["last_down_time"] = time.time()
                msg = (
                    f"🚨 **ButterflyGuy Service Down**\n"
                    f"**Service:** {service_name} ({url})\n"
                    f"**Status:** {result['error']}\n"
                    f"**Time:** {_now_et()} ET\n"
                    f"**Failures:** {state['fail_count']} consecutive"
                )
                send_discord_alert(cfg["discord_webhook"], msg)
                print(f"[ALERT] {key} is DOWN: {result['error']}")
            elif not state["was_healthy"]:
                # Already down — just log, don't re-alert
                print(f"[DOWN] {key} still down ({state['fail_count']} consecutive): {result['error']}")
            else:
                # Below threshold, not alerting yet
                print(f"[WARN] {key} failed ({state['fail_count']}/{cfg['failure_threshold']}): {result['error']}")

        results.append(result)
    return results


def signal_handler(signum: int, frame: object) -> None:
    """Handle SIGTERM/SIGINT for graceful shutdown."""
    global _shutdown
    _shutdown = True
    print(f"\n[SHUTDOWN] Signal {signum} received, exiting...", file=sys.stderr)


def main() -> None:
    parser = argparse.ArgumentParser(description="ButterflyGuy health monitor")
    parser.add_argument("--once", action="store_true", help="Run one check cycle and exit")
    parser.add_argument("--daemon", action="store_true", help="Run continuously (default)")
    parser.add_argument("--config", type=str, default=None, help="Path to YAML config file")
    args = parser.parse_args()

    cfg = load_config(args.config)

    if not cfg["urls"]:
        print("[ERROR] No health check URLs configured", file=sys.stderr)
        sys.exit(1)

    print(f"[START] Health monitor — {len(cfg['urls'])} endpoints, "
          f"interval={cfg['check_interval']}s, "
          f"threshold={cfg['failure_threshold']}")

    # Register signal handlers
    signal.signal(signal.SIGTERM, signal_handler)
    signal.signal(signal.SIGINT, signal_handler)

    if args.once:
        run_check_cycle(cfg)
        return

    # Daemon mode
    while not _shutdown:
        run_check_cycle(cfg)
        # Sleep in small increments to allow responsive shutdown
        for _ in range(cfg["check_interval"]):
            if _shutdown:
                break
            time.sleep(1)

    print("[SHUTDOWN] Health monitor stopped cleanly")


if __name__ == "__main__":
    main()