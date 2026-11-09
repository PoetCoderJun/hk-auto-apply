#!/usr/bin/env python3
"""Operational pacing, 429 backoff, and domain cooldown helpers (offline-deterministic)."""

from __future__ import annotations

import argparse
import json
import random
import sys
from copy import deepcopy
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from pathlib import Path
from typing import Any


OPERATIONAL_DEFAULTS: dict[str, Any] = {
    "min_top_level_gap_sec": 15,
    "guest_rolling_window_sec": 600,
    "guest_max_requests_per_window": 20,
    "min_gap_between_keywords_sec": 60,
    "ui_action_min_gap_sec": 3,
    "backoff_steps_sec": [30, 60, 120],
    "backoff_jitter_max_sec": 5,
    "max_retries_per_request": 2,
    "domain_cooldown_sec": 1800,
    "consecutive_429_for_circuit": 3,
    "_note": "Conservative operational defaults — not official site limits or guarantees.",
}


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


def parse_iso(ts: str | None) -> datetime | None:
    if not ts:
        return None
    if ts.endswith("Z"):
        ts = ts[:-1] + "+00:00"
    return datetime.fromisoformat(ts)


def fmt_iso(dt: datetime) -> str:
    return dt.astimezone(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


def parse_retry_after(header: str | None) -> datetime | None:
    if not header:
        return None
    header = header.strip()
    if header.isdigit():
        return utc_now() + timedelta(seconds=int(header))
    try:
        return parsedate_to_datetime(header)
    except (TypeError, ValueError, OverflowError):
        return None


def new_domain_state(domain: str) -> dict[str, Any]:
    return {
        "domain": domain,
        "next_allowed_at": None,
        "domain_cooldown_until": None,
        "consecutive_429_count": 0,
        "last_request_at": None,
        "guest_request_times": [],
        "pending_retries": {},
    }


def load_state(path: Path) -> dict[str, Any]:
    if not path.exists():
        return {"domains": {}, "defaults": deepcopy(OPERATIONAL_DEFAULTS)}
    data = json.loads(path.read_text(encoding="utf-8"))
    if "defaults" not in data:
        data["defaults"] = deepcopy(OPERATIONAL_DEFAULTS)
    return data


def save_state(path: Path, data: dict[str, Any]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def domain_bucket(state: dict[str, Any], domain: str) -> dict[str, Any]:
    state.setdefault("domains", {})
    if domain not in state["domains"]:
        state["domains"][domain] = new_domain_state(domain)
    return state["domains"][domain]


def prune_guest_window(bucket: dict[str, Any], cfg: dict[str, Any], now: datetime) -> None:
    window = timedelta(seconds=int(cfg["guest_rolling_window_sec"]))
    times = [parse_iso(t) for t in bucket.get("guest_request_times", [])]
    times = [t for t in times if t and now - t <= window]
    bucket["guest_request_times"] = [fmt_iso(t) for t in times]


def next_allowed_after_gap(last_at: datetime | None, gap_sec: int) -> datetime:
    if last_at is None:
        return utc_now()
    return last_at + timedelta(seconds=gap_sec)


def can_issue_top_level(
    state: dict[str, Any], domain: str, now: datetime | None = None, kind: str = "generic"
) -> tuple[bool, str, datetime | None]:
    now = now or utc_now()
    cfg = state.get("defaults", OPERATIONAL_DEFAULTS)
    bucket = domain_bucket(state, domain)
    cooldown_until = parse_iso(bucket.get("domain_cooldown_until"))
    if cooldown_until and now < cooldown_until:
        return False, "domain_cooldown", cooldown_until
    next_allowed = parse_iso(bucket.get("next_allowed_at"))
    if next_allowed and now < next_allowed:
        return False, "gap_not_elapsed", next_allowed
    if kind == "guest":
        prune_guest_window(bucket, cfg, now)
        if len(bucket["guest_request_times"]) >= int(cfg["guest_max_requests_per_window"]):
            oldest = parse_iso(bucket["guest_request_times"][0])
            window = timedelta(seconds=int(cfg["guest_rolling_window_sec"]))
            retry_at = (oldest + window) if oldest else now
            return False, "guest_window_full", retry_at
    return True, "ok", None


def record_top_level_success(
    state: dict[str, Any], domain: str, now: datetime | None = None, kind: str = "generic"
) -> datetime:
    now = now or utc_now()
    cfg = state.get("defaults", OPERATIONAL_DEFAULTS)
    bucket = domain_bucket(state, domain)
    gap = int(cfg["min_top_level_gap_sec"])
    bucket["last_request_at"] = fmt_iso(now)
    bucket["consecutive_429_count"] = 0
    bucket["next_allowed_at"] = fmt_iso(now + timedelta(seconds=gap))
    if kind == "guest":
        prune_guest_window(bucket, cfg, now)
        bucket["guest_request_times"].append(fmt_iso(now))
    return parse_iso(bucket["next_allowed_at"]) or now


def record_http_429(
    state: dict[str, Any],
    domain: str,
    request_key: str,
    retry_after_header: str | None = None,
    now: datetime | None = None,
) -> dict[str, Any]:
    now = now or utc_now()
    cfg = state.get("defaults", OPERATIONAL_DEFAULTS)
    bucket = domain_bucket(state, domain)
    bucket["consecutive_429_count"] = int(bucket.get("consecutive_429_count", 0)) + 1
    pending = bucket.setdefault("pending_retries", {})
    entry = pending.get(request_key, {"attempts": 0, "next_retry_at": None})
    entry["attempts"] += 1

    retry_at = parse_retry_after(retry_after_header)
    used_header = retry_at is not None
    if not retry_at:
        steps = cfg.get("backoff_steps_sec") or [30, 60, 120]
        idx = min(entry["attempts"] - 1, len(steps) - 1)
        jitter = random.uniform(0, float(cfg.get("backoff_jitter_max_sec", 5)))
        retry_at = now + timedelta(seconds=float(steps[idx]) + jitter)

    entry["next_retry_at"] = fmt_iso(retry_at)
    entry["retry_after_header_present"] = used_header
    pending[request_key] = entry

    max_retries = int(cfg.get("max_retries_per_request", 2))
    circuit_n = int(cfg.get("consecutive_429_for_circuit", 3))
    cooldown_sec = int(cfg.get("domain_cooldown_sec", 1800))

    domain_cooldown = False
    if entry["attempts"] > max_retries or bucket["consecutive_429_count"] >= circuit_n:
        domain_cooldown = True
        cooldown_until = now + timedelta(seconds=cooldown_sec)
        bucket["domain_cooldown_until"] = fmt_iso(cooldown_until)
        bucket["next_allowed_at"] = bucket["domain_cooldown_until"]
    else:
        bucket["next_allowed_at"] = entry["next_retry_at"]

    return {
        "request_key": request_key,
        "attempts": entry["attempts"],
        "next_retry_at": entry["next_retry_at"],
        "retry_after_header_present": used_header,
        "domain_cooldown": domain_cooldown,
        "consecutive_429_count": bucket["consecutive_429_count"],
    }


def coverage_resume_cursor(partition: dict[str, Any]) -> int:
    """Return the start offset to retry — never skip an unverified page."""
    if partition.get("next_cursor") is not None:
        return int(partition["next_cursor"])
    if partition.get("last_error") and partition.get("last_success_start") is not None:
        return int(partition["last_success_start"])
    return int(partition.get("next_cursor", 0))


def cmd_self_check() -> int:
    errors: list[str] = []
    state: dict[str, Any] = {"domains": {}, "defaults": deepcopy(OPERATIONAL_DEFAULTS)}
    domain = "www.linkedin.com"
    t0 = datetime(2026, 1, 1, 0, 0, 0, tzinfo=timezone.utc)

    ok, reason, _ = can_issue_top_level(state, domain, t0, kind="guest")
    if not ok:
        errors.append(f"expected first guest request allowed, got {reason}")

    record_top_level_success(state, domain, t0, kind="guest")
    ok, reason, wake = can_issue_top_level(state, domain, t0 + timedelta(seconds=5), kind="guest")
    if ok or reason != "gap_not_elapsed":
        errors.append("expected gap block before min_top_level_gap_sec")

    info = record_http_429(state, domain, "kw|start=0", None, t0 + timedelta(seconds=20))
    if info["retry_after_header_present"]:
        errors.append("expected no Retry-After header path")
    if info["attempts"] != 1:
        errors.append("expected first 429 attempt count 1")

    record_http_429(state, domain, "kw|start=0", "120", t0 + timedelta(seconds=25))
    pending = state["domains"][domain]["pending_retries"]["kw|start=0"]
    if not pending["retry_after_header_present"]:
        errors.append("expected Retry-After honored")
    retry = parse_iso(pending["next_retry_at"])
    if not retry or (retry - (t0 + timedelta(seconds=25))).total_seconds() < 119:
        errors.append("Retry-After should push next_retry_at by ~120s")

    for _ in range(3):
        record_http_429(state, domain, "other", None, t0 + timedelta(seconds=30))
    if not state["domains"][domain].get("domain_cooldown_until"):
        errors.append("expected circuit breaker cooldown after 3 consecutive 429")

    part_fail_page0 = {"last_success_start": 0, "last_error": {"code": 429}, "next_cursor": None}
    if coverage_resume_cursor(part_fail_page0) != 0:
        errors.append("page-0 429 must resume at start=0")

    part_fail_page20 = {"next_cursor": 20, "last_success_start": 10}
    if coverage_resume_cursor(part_fail_page20) != 20:
        errors.append("must resume at next_cursor not last_success+10")

    if errors:
        for err in errors:
            print(f"FAIL: {err}", file=sys.stderr)
        return 1
    print("pacing_gate self-check: OK")
    return 0


def cmd_plan_next(args: argparse.Namespace) -> int:
    path = Path(args.state)
    state = load_state(path)
    now = utc_now()
    ok, reason, wake = can_issue_top_level(state, args.domain, now, kind=args.kind)
    out = {"ok": ok, "reason": reason, "next_retry_at": fmt_iso(wake) if wake else None}
    json.dump(out, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0 if ok else 2


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    sub.add_parser("self-check", help="Run offline deterministic checks")

    plan = sub.add_parser("plan-next", help="Whether a top-level request may run now")
    plan.add_argument("--state", required=True, help="rate_limit_state.json path")
    plan.add_argument("--domain", required=True)
    plan.add_argument("--kind", default="generic", choices=["generic", "guest"])

    args = parser.parse_args(argv)
    if args.cmd == "self-check":
        return cmd_self_check()
    if args.cmd == "plan-next":
        return cmd_plan_next(args)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
