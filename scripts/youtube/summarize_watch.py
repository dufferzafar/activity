#!/usr/bin/env python3

import argparse
import json
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Summarize YouTube/YouTube Music Watch History by date. "
            "Input is a JSON array of activity items with 'header', 'time', and 'titleUrl' fields. "
            "Outputs two JSON files: youtube.watch.summary.json and ytmusic.watch.summary.json, "
            "each an array of {date, count} objects sorted by date. Only items whose titleUrl contains 'watch' are counted."
        )
    )
    parser.add_argument(
        "input",
        help="Path to Google Takeout watch-history.json (array of records)",
    )
    parser.add_argument(
        "--outdir",
        help="Directory to write output files (defaults to the input file's directory)",
        default=None,
    )
    return parser.parse_args()


def load_items(input_path: Path) -> Iterable[Dict[str, Any]]:
    with input_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    if not isinstance(data, list):
        raise ValueError("Expected top-level JSON array of activity items")
    return data


def extract_date_utc_iso(activity_time: str) -> str:
    """
    Convert an ISO 8601 timestamp like '2025-08-17T03:38:49.437Z' to date string '2025-08-17' (UTC).
    """
    if not activity_time:
        raise ValueError("Missing time field on activity item")
    normalized = activity_time.replace("Z", "+00:00") if activity_time.endswith("Z") else activity_time
    dt = datetime.fromisoformat(normalized)
    return dt.date().isoformat()


def summarize_watch_by_date(items: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    counts: Counter[str] = Counter()
    for item in items:
        time_str = item.get("time")
        title_url = item.get("titleUrl")
        if not time_str or not title_url:
            # Skip items missing required fields
            continue
        # Only count items that are actual watch URLs; skip posts and others
        if "watch" not in title_url:
            continue
        try:
            date_iso = extract_date_utc_iso(time_str)
        except Exception:
            # Skip malformed timestamps
            continue
        counts[date_iso] += 1

    summary = [{"date": d, "count": counts[d]} for d in sorted(counts.keys())]
    return summary


def write_summary(output_path: Path, summary: List[Dict[str, Any]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    outdir = Path(args.outdir) if args.outdir else input_path.parent

    items = load_items(input_path)
    ytmusic_items = [it for it in items if it.get("header") == "YouTube Music"]
    youtube_items = [it for it in items if it.get("header") == "YouTube"]

    ytmusic_summary = summarize_watch_by_date(ytmusic_items)
    youtube_summary = summarize_watch_by_date(youtube_items)

    ytmusic_path = outdir / "ytmusic.watch.summary.json"
    youtube_path = outdir / "youtube.watch.summary.json"

    write_summary(ytmusic_path, ytmusic_summary)
    write_summary(youtube_path, youtube_summary)

    print(
        f"Wrote {len(ytmusic_summary)} dates to {ytmusic_path}; "
        f"{len(youtube_summary)} dates to {youtube_path}"
    )


if __name__ == "__main__":
    main()


