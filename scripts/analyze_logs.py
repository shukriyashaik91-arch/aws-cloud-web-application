#!/usr/bin/env python3
"""
analyze_logs.py — Web Access Log Analyzer
AWS Cloud Web Application — Internship Project

Reads dataset/web-access-logs.csv and calculates:
  1. Total requests
  2. Top 5 requested pages
  3. Number of 4xx errors
  4. Number of 5xx errors
  5. Peak traffic hour
  6. Number of unique visitor IPs
  7. Most common HTTP method
  8. Average response size (bytes)

Usage:
    python scripts/analyze_logs.py
    python scripts/analyze_logs.py --csv path/to/custom.csv
    python scripts/analyze_logs.py --json       (output as JSON)

Requirements: Python 3.9+  (no external libraries needed — stdlib only)
Note: Python 3.9+ is required because the code uses PEP 585 built-in
      generic types (list[dict], tuple[X, Y], dict[X, Y]).
      Ubuntu 22.04 LTS ships Python 3.10 — fully compatible.
"""

import csv
import json
import sys
import argparse
from collections import Counter
from datetime import datetime
from pathlib import Path


# ── Colour helpers (no external libs) ──────────────────────────────────────
def _c(code: str, text: str, enabled: bool = True) -> str:
    """Wrap text in an ANSI colour code when running in a terminal."""
    if not enabled or not sys.stdout.isatty():
        return text
    codes = {
        "bold":   "\033[1m",
        "orange": "\033[33m",
        "green":  "\033[92m",
        "blue":   "\033[94m",
        "red":    "\033[91m",
        "cyan":   "\033[96m",
        "dim":    "\033[2m",
        "reset":  "\033[0m",
    }
    return f"{codes.get(code, '')}{text}{codes['reset']}"


# ── CSV loader ──────────────────────────────────────────────────────────────
def load_logs(csv_path: Path) -> list[dict]:
    """
    Load the web-access-log CSV.

    Expected columns:
        timestamp, ip, method, path, status, bytes, user_agent

    Returns a list of row dicts.  Rows with missing/invalid data are skipped
    with a warning so a single bad line does not abort the whole analysis.
    """
    required_columns = {"timestamp", "ip", "method", "path", "status", "bytes"}
    records = []
    skipped = 0

    if not csv_path.exists():
        print(f"ERROR: CSV file not found: {csv_path}", file=sys.stderr)
        sys.exit(1)

    with open(csv_path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)

        # Validate columns
        if reader.fieldnames is None:
            print("ERROR: CSV file is empty.", file=sys.stderr)
            sys.exit(1)

        actual_cols = {c.strip() for c in reader.fieldnames}
        missing = required_columns - actual_cols
        if missing:
            print(
                f"ERROR: CSV is missing columns: {', '.join(sorted(missing))}",
                file=sys.stderr,
            )
            sys.exit(1)

        for line_num, row in enumerate(reader, start=2):
            try:
                # Normalise keys (strip whitespace)
                row = {k.strip(): v.strip() for k, v in row.items() if k}

                # Parse timestamp
                row["_dt"] = datetime.strptime(row["timestamp"], "%Y-%m-%d %H:%M:%S")

                # Parse status code
                row["_status"] = int(row["status"])

                # Parse bytes (use 0 for missing/non-numeric)
                raw_bytes = row.get("bytes", "0") or "0"
                row["_bytes"] = int(raw_bytes) if raw_bytes.isdigit() else 0

                records.append(row)
            except (ValueError, KeyError) as exc:
                skipped += 1
                if skipped <= 5:          # only print first 5 warnings
                    print(f"  WARNING: Skipping line {line_num}: {exc}", file=sys.stderr)

    if skipped > 5:
        print(f"  WARNING: {skipped} lines skipped in total.", file=sys.stderr)

    return records


# ── Analysis functions ──────────────────────────────────────────────────────
def total_requests(records: list[dict]) -> int:
    return len(records)


def top_pages(records: list[dict], n: int = 5) -> list[tuple[str, int]]:
    counter = Counter(r["path"] for r in records)
    return counter.most_common(n)


def error_counts(records: list[dict]) -> tuple[int, int]:
    """Return (4xx_count, 5xx_count)."""
    errors_4xx = sum(1 for r in records if 400 <= r["_status"] < 500)
    errors_5xx = sum(1 for r in records if 500 <= r["_status"] < 600)
    return errors_4xx, errors_5xx


def peak_hour(records: list[dict]) -> tuple[int, int]:
    """Return (hour_0_to_23, request_count)."""
    hour_counter = Counter(r["_dt"].hour for r in records)
    return hour_counter.most_common(1)[0]  # (hour, count)


def unique_ips(records: list[dict]) -> int:
    return len({r["ip"] for r in records})


def most_common_method(records: list[dict]) -> tuple[str, int]:
    counter = Counter(r["method"].upper() for r in records)
    return counter.most_common(1)[0]  # (method, count)


def average_response_size(records: list[dict]) -> float:
    if not records:
        return 0.0
    return sum(r["_bytes"] for r in records) / len(records)


def status_distribution(records: list[dict]) -> dict[str, int]:
    buckets = {"1xx": 0, "2xx": 0, "3xx": 0, "4xx": 0, "5xx": 0}
    for r in records:
        s = r["_status"]
        if 100 <= s < 200:
            buckets["1xx"] += 1
        elif 200 <= s < 300:
            buckets["2xx"] += 1
        elif 300 <= s < 400:
            buckets["3xx"] += 1
        elif 400 <= s < 500:
            buckets["4xx"] += 1
        elif 500 <= s < 600:
            buckets["5xx"] += 1
    return buckets


def hourly_traffic(records: list[dict]) -> dict[int, int]:
    counter: dict[int, int] = {h: 0 for h in range(24)}
    for r in records:
        counter[r["_dt"].hour] += 1
    return counter


# ── Report renderer ─────────────────────────────────────────────────────────
def render_text_report(records: list[dict], csv_path: Path) -> None:
    colour = sys.stdout.isatty()

    # Run all analyses
    total   = total_requests(records)
    pages   = top_pages(records, 5)
    e4, e5  = error_counts(records)
    ph, phc = peak_hour(records)
    uniq    = unique_ips(records)
    method, mc = most_common_method(records)
    avg_sz  = average_response_size(records)
    dist    = status_distribution(records)
    hourly  = hourly_traffic(records)

    SEP  = _c("dim", "─" * 62, colour)
    DSEP = _c("dim", "═" * 62, colour)

    print()
    print(DSEP)
    print(_c("bold", _c("orange", "  AWS Cloud Web Application — Log Analysis Report", colour), colour))
    print(_c("dim",  f"  Dataset : {csv_path}", colour))
    print(_c("dim",  f"  Records : {total:,}", colour))
    print(DSEP)

    # ── 1. Total requests ──────────────────────────────────
    print()
    print(_c("cyan", "  1. TOTAL REQUESTS", colour))
    print(SEP)
    print(f"     {_c('bold', f'{total:,}', colour)} HTTP requests in dataset")

    # ── 2. Top requested pages ─────────────────────────────
    print()
    print(_c("cyan", "  2. TOP 5 REQUESTED PAGES", colour))
    print(SEP)
    for rank, (path, count) in enumerate(pages, 1):
        bar_len = int(count / max(pages[0][1], 1) * 30)
        bar = _c("green", "█" * bar_len, colour) + _c("dim", "░" * (30 - bar_len), colour)
        pct = count / total * 100
        print(f"  {rank:2}. {path:<30} {bar}  {count:>5,}  ({pct:4.1f}%)")

    # ── 3 & 4. Errors ─────────────────────────────────────
    print()
    print(_c("cyan", "  3 & 4. ERROR SUMMARY", colour))
    print(SEP)
    print(f"     4xx Client Errors : {_c('orange', str(e4), colour):>8}")
    print(f"     5xx Server Errors : {_c('red',    str(e5), colour):>8}")
    print()
    print("     Status Code Distribution:")
    for code, cnt in dist.items():
        colour_fn = "green" if code == "2xx" else ("orange" if code == "4xx" else ("red" if code == "5xx" else "dim"))
        pct = cnt / total * 100 if total else 0
        print(f"       {code}  {_c(colour_fn, f'{cnt:>5,}', colour)}  ({pct:5.1f}%)")

    # ── 5. Peak traffic hour ───────────────────────────────
    print()
    print(_c("cyan", "  5. PEAK TRAFFIC HOUR", colour))
    print(SEP)
    print(f"     Peak hour : {_c('bold', f'{ph:02d}:00 – {ph:02d}:59 UTC', colour)}")
    print(f"     Requests  : {_c('bold', str(phc), colour)}")
    print()
    print("     Hourly traffic chart (UTC):")
    max_h = max(hourly.values()) or 1
    for h in range(24):
        cnt  = hourly[h]
        bar  = _c("blue", "█" * int(cnt / max_h * 20), colour)
        mark = _c("orange", " ◀ PEAK", colour) if h == ph else ""
        print(f"     {h:02d}h  {bar:<20}  {cnt:>4}{mark}")

    # ── 6. Unique IPs ──────────────────────────────────────
    print()
    print(_c("cyan", "  6. UNIQUE VISITOR IPs", colour))
    print(SEP)
    print(f"     {_c('bold', str(uniq), colour)} unique IP addresses")

    # ── 7. Most common method ──────────────────────────────
    print()
    print(_c("cyan", "  7. MOST COMMON HTTP METHOD", colour))
    print(SEP)
    method_counter = Counter(r["method"].upper() for r in records)
    for m, cnt in method_counter.most_common():
        indicator = _c("orange", " ◀ MOST COMMON", colour) if m == method else ""
        pct = cnt / total * 100
        print(f"     {m:<8}  {cnt:>5,}  ({pct:5.1f}%){indicator}")

    # ── 8. Average response size ───────────────────────────
    print()
    print(_c("cyan", "  8. AVERAGE RESPONSE SIZE", colour))
    print(SEP)
    print(f"     Average : {_c('bold', f'{avg_sz:,.0f} bytes  ({avg_sz/1024:.2f} KB)', colour)}")

    # ── Footer ─────────────────────────────────────────────
    print()
    print(DSEP)
    print(_c("dim", "  Analysis complete — no sensitive data in this output", colour))
    print(DSEP)
    print()


def render_json_report(records: list[dict], csv_path: Path) -> None:
    total   = total_requests(records)
    pages   = top_pages(records, 5)
    e4, e5  = error_counts(records)
    ph, phc = peak_hour(records)
    uniq    = unique_ips(records)
    method, mc = most_common_method(records)
    avg_sz  = average_response_size(records)
    dist    = status_distribution(records)

    report = {
        "dataset": str(csv_path),
        "total_requests": total,
        "top_pages": [{"path": p, "count": c} for p, c in pages],
        "errors_4xx": e4,
        "errors_5xx": e5,
        "peak_traffic_hour": ph,
        "peak_hour_request_count": phc,
        "unique_visitor_ips": uniq,
        "most_common_method": method,
        "most_common_method_count": mc,
        "average_response_size_bytes": round(avg_sz, 2),
        "status_distribution": dist,
    }
    print(json.dumps(report, indent=2))


# ── CLI entry point ─────────────────────────────────────────────────────────
def parse_args() -> argparse.Namespace:
    # Resolve default CSV path relative to this script's location
    script_dir = Path(__file__).parent.parent  # project root
    default_csv = script_dir / "dataset" / "web-access-logs.csv"

    parser = argparse.ArgumentParser(
        description="Analyze web access logs and print a summary report.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python scripts/analyze_logs.py
  python scripts/analyze_logs.py --csv /var/log/nginx/access.log.csv
  python scripts/analyze_logs.py --json
        """,
    )
    parser.add_argument(
        "--csv",
        type=Path,
        default=default_csv,
        help=f"Path to the CSV log file (default: {default_csv})",
    )
    parser.add_argument(
        "--json",
        action="store_true",
        help="Output results as JSON instead of a formatted report",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()

    # Load data
    records = load_logs(args.csv)

    if not records:
        print("ERROR: No valid records found in the CSV.", file=sys.stderr)
        sys.exit(1)

    # Render chosen output format
    if args.json:
        render_json_report(records, args.csv)
    else:
        render_text_report(records, args.csv)


if __name__ == "__main__":
    main()
