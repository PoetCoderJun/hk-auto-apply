#!/usr/bin/env python3
"""Extract mechanical signals from a job description. Does not decide apply/skip."""

from __future__ import annotations

import argparse
import json
import re
import sys
from pathlib import Path


RANGE = re.compile(
    r"(?P<min>\d+)\s*(?:-|–|to)\s*(?P<max>\d+)\s*(?:\+)?\s*(?:years?|yrs?)\s+"
    r"(?:of\s+)?(?:relevant\s+)?(?:experience|exp\b)",
    re.I,
)
MINIMUM = re.compile(
    r"(?:minimum|min\.?|at\s+least|no\s+less\s+than|atleast)\s+(?P<min>\d+)\s*\+?\s*(?:years?|yrs?)",
    re.I,
)
PLUS = re.compile(
    r"(?P<min>\d+)\s*\+\s*(?:years?|yrs?)\s+(?:of\s+)?(?:relevant\s+)?(?:experience|exp\b)",
    re.I,
)
PLAIN = re.compile(
    r"(?P<min>\d+)\s*(?:years?|yrs?)\s+(?:of\s+)?(?:relevant\s+)?(?:working\s+)?experience",
    re.I,
)
PLAN = re.compile(r"\b\d+\s*[- ]\s*year\s+(?:strategic\s+)?plan\b", re.I)
HISTORY = re.compile(
    r"(?:over|more\s+than|nearly|almost|for)\s+\d+\s*(?:years?|yrs?).{0,60}"
    r"(?:history|established|founded|operating|serving|in\s+business|heritage|since)",
    re.I,
)
HISTORY_FRONT = re.compile(
    r"(?:history|established|founded|operating|serving|in\s+business|heritage|award-winning).{0,40}"
    r"(?:over|more\s+than|nearly|almost|for)?\s*\d+\s*(?:years?|yrs?)",
    re.I,
)
CANTONESE = re.compile(r"(cantonese|粤语|粵語|广东话|廣東話)", re.I)
NATIVE = re.compile(r"(native|mother\s*tongue|母语|母語|必须|必須|required|mandatory|must)", re.I)
PREFERRED = re.compile(r"(preferred|preference|advantage|plus|an\s+asset|加分|优先|優先|佳)", re.I)
INTERN = re.compile(r"\b(intern(ship)?|summer intern|实习|實習)\b", re.I)
GRADUATE = re.compile(r"\b(graduate|analyst|associate|manager|officer|full[- ]time|全职|全職)\b", re.I)


def _is_ignored(span_text: str, full: str, start: int) -> str | None:
    window = full[max(0, start - 80) : start + len(span_text) + 80]
    if PLAN.search(window):
        return "plan"
    if HISTORY.search(window) or HISTORY_FRONT.search(window):
        return "company_history"
    years = re.search(r"(\d+)", span_text)
    if years and int(years.group(1)) >= 15 and re.search(r"\b(over|more than)\b", window, re.I):
        return "company_history"
    return None


def extract_year_mentions(text: str) -> tuple[list[dict], int | None, int | None]:
    mentions = []
    required_min = None
    required_max = None
    seen_spans = set()
    patterns = (RANGE, MINIMUM, PLUS, PLAIN)
    for pattern in patterns:
        for match in pattern.finditer(text or ""):
            span = (match.start(), match.end())
            if span in seen_spans:
                continue
            seen_spans.add(span)
            raw = match.group(0)
            reason = _is_ignored(raw, text or "", match.start())
            item = {
                "raw": raw,
                "min": int(match.group("min")),
                "max": int(match.group("max")) if "max" in match.groupdict() and match.group("max") else None,
                "ignored": bool(reason),
                "ignore_reason": reason,
            }
            mentions.append(item)
            if reason:
                continue
            required_min = item["min"] if required_min is None else min(required_min, item["min"])
            if item["max"] is not None:
                required_max = item["max"] if required_max is None else max(required_max, item["max"])
    return mentions, required_min, required_max


def cantonese_flags(text: str) -> tuple[bool, bool]:
    native = False
    preferred = False
    for match in CANTONESE.finditer(text or ""):
        window = (text or "")[max(0, match.start() - 48) : match.end() + 48]
        if NATIVE.search(window) and not PREFERRED.search(window):
            native = True
        elif PREFERRED.search(window) or not NATIVE.search(window):
            preferred = True
    if native:
        preferred = False
    return native, preferred


def internship_only(text: str) -> bool:
    body = text or ""
    if not INTERN.search(body):
        return False
    return not GRADUATE.search(body)


def extract_flags(text: str) -> dict:
    mentions, required_min, required_max = extract_year_mentions(text)
    native, preferred = cantonese_flags(text)
    return {
        "required_years_min": required_min,
        "required_years_max": required_max,
        "year_mentions": mentions,
        "native_cantonese": native,
        "cantonese_preferred": preferred,
        "internship_only": internship_only(text),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--text", help="JD text")
    group.add_argument("--file", help="Path to a UTF-8 JD file")
    args = parser.parse_args(argv)
    text = args.text if args.text is not None else Path(args.file).read_text(encoding="utf-8")
    json.dump(extract_flags(text), sys.stdout, ensure_ascii=False, indent=2)
    sys.stdout.write("\n")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
