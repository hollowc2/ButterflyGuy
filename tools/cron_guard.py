"""Run a cron job and post one Discord alert if it fails.

The scheduled Discord jobs (daily report card, live performance page,
realized-vs-implied) once failed silently for two weeks: a deploy edited
configs/config.yaml in the /opt/butterflyguy checkout while the checkout code
lagged behind, so every job died in load_config() and only the log knew.

This wrapper passes the job's output through unchanged (cron still appends it to
the job's log) and, on a non-zero exit, posts the job name, exit code and last
output lines to DISCORD_WEBHOOK_URL (environment first, then .env). It uses only
the standard library plus python-dotenv, so it still alerts when the
butterfly_guy package itself cannot import.

Usage (from the repo root):
  .venv/bin/python tools/cron_guard.py --job daily_report_card -- \
      .venv/bin/python tools/send_daily_report_card.py
"""

from __future__ import annotations

import argparse
import collections
import json
import os
import socket
import subprocess
import sys
import urllib.request
from pathlib import Path

from dotenv import dotenv_values

ROOT = Path(__file__).parent.parent
TAIL_LINES = 8
DISCORD_LIMIT = 2000


def run(command: list[str]) -> tuple[int, list[str]]:
    """Run ``command``, echo its combined output, return exit code and tail."""
    tail: collections.deque[str] = collections.deque(maxlen=TAIL_LINES)
    try:
        proc = subprocess.Popen(
            command,
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            errors="replace",
        )
    except OSError as exc:
        message = f"cron_guard: could not start {command[0]}: {exc}"
        print(message, flush=True)
        return 127, [message]
    assert proc.stdout is not None
    for line in proc.stdout:
        sys.stdout.write(line)
        tail.append(line.rstrip("\n"))
    sys.stdout.flush()
    return proc.wait(), list(tail)


def format_alert(job: str, returncode: int, tail: list[str]) -> str:
    header = f"⚠️ Cron job `{job}` failed on {socket.gethostname()} (exit {returncode})"
    body = "\n".join(tail)
    room = DISCORD_LIMIT - len(header) - len("\n```\n\n```")
    if len(body) > room:
        body = "…" + body[-(room - 1) :]
    return f"{header}\n```\n{body}\n```" if body else header


def webhook_url() -> str | None:
    return os.environ.get("DISCORD_WEBHOOK_URL") or dotenv_values(ROOT / ".env").get(
        "DISCORD_WEBHOOK_URL"
    )


def post(url: str, content: str) -> bool:
    request = urllib.request.Request(
        url,
        data=json.dumps({"content": content}).encode(),
        headers={"Content-Type": "application/json", "User-Agent": "butterflyguy-cron-guard"},
    )
    try:
        with urllib.request.urlopen(request, timeout=10) as response:
            return 200 <= response.status < 300
    except Exception as exc:
        print(f"cron_guard: Discord alert failed: {exc}", flush=True)
        return False


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--job", required=True, help="Name shown in the alert")
    parser.add_argument("command", nargs=argparse.REMAINDER, help="-- command to run")
    args = parser.parse_args(argv)
    command = args.command[1:] if args.command[:1] == ["--"] else args.command
    if not command:
        parser.error("no command given")

    returncode, tail = run(command)
    if returncode != 0:
        url = webhook_url()
        if url:
            post(url, format_alert(args.job, returncode, tail))
        else:
            print("cron_guard: DISCORD_WEBHOOK_URL not set; no alert sent", flush=True)
    return returncode


if __name__ == "__main__":
    raise SystemExit(main())
