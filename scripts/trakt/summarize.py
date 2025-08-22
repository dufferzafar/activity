import argparse
import json
import os
from collections import Counter, defaultdict
from typing import Any, Dict, List, Tuple


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Aggregate Trakt activity JSONL into per-day runtime and genre/subgenre counts."
    )
    parser.add_argument(
        "-i",
        "--input",
        required=True,
        help="Path to input JSONL file exported from Trakt activity",
    )
    parser.add_argument(
        "-o",
        "--output",
        required=False,
        help="Path to output JSON file with per-day summary. Defaults to <input>.summary.json",
    )
    return parser.parse_args()


def extract_date(watched_at: str) -> str:
    if not watched_at:
        return ""
    # Expecting ISO 8601 like 2025-06-29T14:58:00.000Z
    t_index = watched_at.find("T")
    if t_index == -1:
        return watched_at[:10]
    return watched_at[:t_index]


def coerce_list_of_str(value: Any) -> List[str]:
    if value is None:
        return []
    if isinstance(value, list):
        result: List[str] = []
        for item in value:
            if isinstance(item, str):
                result.append(item.strip().lower())
        return result
    if isinstance(value, str):
        return [value.strip().lower()]
    return []


def aggregate_from_record(record: Dict[str, Any]) -> Tuple[str, int, List[str], List[str]]:
    watched_at = record.get("watched_at", "")
    date_key = extract_date(watched_at)

    record_type = record.get("type")
    runtime_minutes: int = 0
    genres: List[str] = []
    subgenres: List[str] = []

    if record_type == "episode":
        episode = record.get("episode", {}) or {}
        show = record.get("show", {}) or {}
        runtime_val = episode.get("runtime")
        if isinstance(runtime_val, int):
            runtime_minutes = runtime_val
        elif isinstance(show.get("runtime"), int):
            runtime_minutes = int(show.get("runtime"))
        genres = coerce_list_of_str(show.get("genres"))
        subgenres = coerce_list_of_str(show.get("subgenres"))
    elif record_type == "movie":
        movie = record.get("movie", {}) or {}
        runtime_val = movie.get("runtime")
        if isinstance(runtime_val, int):
            runtime_minutes = runtime_val
        genres = coerce_list_of_str(movie.get("genres"))
        subgenres = coerce_list_of_str(movie.get("subgenres"))
    else:
        # Unknown type; ignore genre data but allow runtime if present at a known path
        pass

    return date_key, runtime_minutes, genres, subgenres


def summarize(input_path: str) -> List[Dict[str, Any]]:
    per_day_runtime: Dict[str, int] = defaultdict(int)
    per_day_genres: Dict[str, Counter] = defaultdict(Counter)
    per_day_subgenres: Dict[str, Counter] = defaultdict(Counter)

    with open(input_path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                record = json.loads(line)
            except json.JSONDecodeError:
                continue

            date_key, runtime_minutes, genres, subgenres = aggregate_from_record(record)
            if not date_key:
                continue

            if isinstance(runtime_minutes, int) and runtime_minutes > 0:
                per_day_runtime[date_key] += runtime_minutes

            if genres:
                per_day_genres[date_key].update(genres)
            if subgenres:
                per_day_subgenres[date_key].update(subgenres)

    # Build output list sorted by date
    output: List[Dict[str, Any]] = []
    for date_key in sorted(per_day_runtime.keys() | per_day_genres.keys() | per_day_subgenres.keys()):
        genres_counter = per_day_genres.get(date_key, Counter())
        subgenres_counter = per_day_subgenres.get(date_key, Counter())

        genres_list = [
            {"name": name, "count": count}
            for name, count in sorted(
                genres_counter.items(), key=lambda kv: (-kv[1], kv[0])
            )
        ]
        subgenres_list = [
            {"name": name, "count": count}
            for name, count in sorted(
                subgenres_counter.items(), key=lambda kv: (-kv[1], kv[0])
            )
        ]

        output.append(
            {
                "date": date_key,
                "total_runtime": per_day_runtime.get(date_key, 0),
                "genres": genres_list,
                "subgenres": subgenres_list,
            }
        )

    return output


def main() -> None:
    args = parse_args()
    input_path = args.input
    if not os.path.isfile(input_path):
        raise SystemExit(f"Input file not found: {input_path}")

    output_path = args.output
    if not output_path:
        base, _ = os.path.splitext(input_path)
        output_path = f"{base}.summary.json"

    summary = summarize(input_path)

    with open(output_path, "w", encoding="utf-8") as f:
        json.dump(summary, f, ensure_ascii=False, indent=2)

    print(f"Wrote summary to: {output_path}")


if __name__ == "__main__":
    main() 