#!/usr/bin/env python3

import argparse
import json
from collections import defaultdict
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Iterable, List, Optional, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Summarize YouTube/YouTube Music Search History by date with queries. "
            "Input is a JSON array of activity items with 'header', 'title' and 'time' fields. "
            "Outputs two JSON files with arrays of {date, queries} objects sorted by date."
        )
    )
    parser.add_argument(
        "input",
        help="Path to Google Takeout search-history.json (array of records)",
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


def parse_timestamp(activity_time: str) -> datetime:
    if not activity_time:
        raise ValueError("Missing time field on activity item")
    normalized = activity_time.replace("Z", "+00:00") if activity_time.endswith("Z") else activity_time
    return datetime.fromisoformat(normalized)


def extract_query_from_title(title: Optional[str]) -> Optional[str]:
    if not title:
        return None
    prefix = "Searched for "
    if title.startswith(prefix):
        return title[len(prefix) :].strip()
    return None


def summarize_queries_by_date(items: Iterable[Dict[str, Any]]) -> List[Dict[str, Any]]:
    # Map date -> list of (timestamp, query)
    date_to_time_and_queries: Dict[str, List[Tuple[datetime, str]]] = defaultdict(list)

    for item in items:
        time_str = item.get("time")
        title = item.get("title")
        query = extract_query_from_title(title)
        if not time_str or not query:
            # Skip items without needed fields or non-search titles
            continue
        try:
            dt = parse_timestamp(time_str)
            date_iso = extract_date_utc_iso(time_str)
        except Exception:
            # Skip malformed timestamps
            continue
        date_to_time_and_queries[date_iso].append((dt, query))

    summary: List[Dict[str, Any]] = []
    for date_iso in sorted(date_to_time_and_queries.keys()):
        # Sort queries within a date by timestamp ascending for determinism
        time_and_queries = sorted(date_to_time_and_queries[date_iso], key=lambda t: t[0])
        queries = [q for _t, q in time_and_queries]
        summary.append({"date": date_iso, "queries": queries})
    return summary


def write_output(output_path: Path, data: List[Dict[str, Any]]) -> None:
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with output_path.open("w", encoding="utf-8") as f:
        json.dump(data, f, ensure_ascii=False, indent=2)


def main() -> None:
    args = parse_args()
    input_path = Path(args.input)
    outdir = Path(args.outdir) if args.outdir else input_path.parent

    items = load_items(input_path)
    ytmusic_items = [it for it in items if it.get("header") == "YouTube Music"]
    youtube_items = [it for it in items if it.get("header") == "YouTube"]

    ytmusic_summary = summarize_queries_by_date(ytmusic_items)
    youtube_summary = summarize_queries_by_date(youtube_items)

    ytmusic_path = outdir / "ytmusic.search.queries.json"
    youtube_path = outdir / "youtube.search.queries.json"

    write_output(ytmusic_path, ytmusic_summary)
    write_output(youtube_path, youtube_summary)

    print(
        f"Wrote {len(ytmusic_summary)} dates to {ytmusic_path}; "
        f"{len(youtube_summary)} dates to {youtube_path}"
    )


if __name__ == "__main__":
    main()


