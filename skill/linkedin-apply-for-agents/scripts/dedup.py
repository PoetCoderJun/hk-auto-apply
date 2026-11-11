#!/usr/bin/env python3
"""Mark JobsDB / LinkedIn jobs that duplicate an existing tracker row."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse, urlunparse


COMPANY_SUFFIXES = re.compile(
    r"\b(limited|ltd|inc|llc|co|company|holdings?|holding|group|plc|sa|ag|"
    r"kk|gmbh|pte|pty|bhd|nv|oyj|ab|se)\b",
    re.I,
)
COMPANY_SUFFIXES_CJK = re.compile(r"(有限公司|有限責任公司|有限责任公司|集團|集团|股份有限公司)")
PUNCT = re.compile(r"[^\w\s+&/-]+", re.UNICODE)
WS = re.compile(r"\s+")

TITLE_PHRASES = (
    (re.compile(r"\basst\.?\s*relationship\s+manager\b"), "assistant relationship manager"),
    (re.compile(r"\bassistant\s+rm\b"), "assistant relationship manager"),
    (re.compile(r"\bsenior\s+relationship\s+manager\b"), "senior relationship manager"),
    (re.compile(r"\bsenior\s+rm\b"), "senior relationship manager"),
    (re.compile(r"\brelationship\s+manager\b"), "relationship manager"),
)
TITLE_TOKENS = {
    "arm": "assistant relationship manager",
    "srm": "senior relationship manager",
}


def normalize_company(value: str) -> str:
    text = (value or "").lower().replace("&", " and ")
    text = COMPANY_SUFFIXES_CJK.sub(" ", text)
    text = COMPANY_SUFFIXES.sub(" ", text)
    text = PUNCT.sub(" ", text)
    return WS.sub(" ", text).strip()


def normalize_title(value: str) -> str:
    text = (value or "").lower().replace("&", " and ")
    text = PUNCT.sub(" ", text)
    text = WS.sub(" ", text).strip()
    for pattern, replacement in TITLE_PHRASES:
        text = pattern.sub(replacement, text)
    tokens = []
    for token in text.split():
        tokens.append(TITLE_TOKENS.get(token, token))
    return WS.sub(" ", " ".join(tokens)).strip()


def canonicalize_url(url: str) -> str:
    raw = (url or "").strip()
    if not raw:
        return ""
    linkedin = re.search(r"linkedin\.com/jobs/view/(\d+)", raw, re.I)
    if linkedin:
        return f"linkedin:job:{linkedin.group(1)}"
    current = re.search(r"[?&]currentJobId=(\d+)", raw, re.I)
    if current:
        return f"linkedin:job:{current.group(1)}"
    jobsdb = re.search(r"jobsdb\.com/job/(\d+)", raw, re.I)
    if jobsdb:
        return f"jobsdb:job:{jobsdb.group(1)}"
    parsed = urlparse(raw)
    query = parse_qs(parsed.query, keep_blank_values=False)
    kept = {
        key: values
        for key, values in query.items()
        if not key.lower().startswith("utm_") and key.lower() not in {"trk", "refId", "trackingId"}
    }
    # flatten back to a stable query string
    pairs = []
    for key in sorted(kept):
        for value in kept[key]:
            pairs.append(f"{key}={value}")
    cleaned = parsed._replace(query="&".join(pairs), fragment="")
    normalized = urlunparse(cleaned).rstrip("/").lower()
    return normalized


def titles_similar(left: str, right: str) -> bool:
    a = normalize_title(left)
    b = normalize_title(right)
    if not a or not b:
        return False
    if a == b:
        return True
    shorter, longer = sorted((a, b), key=len)
    if len(shorter) >= 12 and shorter in longer:
        return True
    sa, sb = set(a.split()), set(b.split())
    if not sa or not sb:
        return False
    overlap = len(sa & sb) / len(sa | sb)
    return overlap >= 0.75


def duplicate_reason(job: dict, record: dict) -> str | None:
    job_url = canonicalize_url(job.get("url") or "")
    record_url = canonicalize_url(record.get("url") or "")
    if job_url and record_url and job_url == record_url:
        return "same_url"
    same_company = normalize_company(job.get("company") or "") and (
        normalize_company(job.get("company") or "") == normalize_company(record.get("company") or "")
    )
    if same_company and titles_similar(job.get("title") or "", record.get("title") or ""):
        return "same_company_and_title"
    return None


def find_duplicate(job: dict, tracker: list[dict]) -> dict | None:
    for record in tracker:
        reason = duplicate_reason(job, record)
        if reason:
            return {"reason": reason, "match": record}
    return None


def annotate(jobs: list[dict], tracker: list[dict]) -> list[dict]:
    annotated = []
    for job in jobs:
        hit = find_duplicate(job, tracker)
        row = dict(job)
        row["duplicate"] = bool(hit)
        row["reason"] = hit["reason"] if hit else None
        row["match"] = hit["match"] if hit else None
        annotated.append(row)
    return annotated


def load_json(path: str) -> list:
    data = json.loads(Path(path).read_text(encoding="utf-8"))
    if not isinstance(data, list):
        raise SystemExit(f"{path} must contain a JSON array")
    return data


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--jobs", required=True, help="JSON array of jobs to check")
    parser.add_argument("--tracker", required=True, help="JSON array of existing tracker rows")
    args = parser.parse_args(argv)
    result = annotate(load_json(args.jobs), load_json(args.tracker))
    json.dump(result, sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
