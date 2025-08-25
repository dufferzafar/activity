"""
Extract energy burned, steps, and walking distance from an Apple Health
SQLite database (Health Secure), converting Apple epoch to a single local date
per record derived from START_DATE.

Outputs JSON rows with fields:
  - date (YYYY-MM-DD, local)
  - energy_burned_kcal (float)
  - steps (int)
  - walk_distance_meters (float)

Optional filters: inclusive date range on start date (local) using --from/--to.
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from typing import Any, Dict, List, Optional, Sequence, Tuple


def build_query(date_from: Optional[str], date_to: Optional[str]) -> Tuple[str, Sequence[Any]]:
    """Build the SQL query with optional inclusive date filters on start datetime."""
    where_clauses: List[str] = []
    params: List[Any] = []

    if date_from is not None:
        where_clauses.append(
            "date(datetime(SAMPLES.START_DATE + 978307200, 'unixepoch', 'localtime')) >= ?"
        )
        params.append(date_from)
    if date_to is not None:
        where_clauses.append(
            "date(datetime(SAMPLES.START_DATE + 978307200, 'unixepoch', 'localtime')) <= ?"
        )
        params.append(date_to)

    where_sql = (" WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

    query = f"""
        SELECT
            date(datetime(SAMPLES.START_DATE + 978307200, 'unixepoch', 'localtime')) AS date,
            AC.energy_burned AS energy_burned_kcal,
            AC.steps AS steps,
            AC.walk_distance AS walk_distance_meters
        FROM
            activity_caches AC
            LEFT JOIN SAMPLES ON SAMPLES.DATA_ID = AC.data_id{where_sql}
        ORDER BY date
    """

    return query, params


def query_db(db_path: str, date_from: Optional[str], date_to: Optional[str]) -> List[Dict[str, Any]]:
    query, params = build_query(date_from=date_from, date_to=date_to)

    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
    except sqlite3.Error as exc:
        raise SystemExit(f"Failed to open database '{db_path}': {exc}")

    try:
        with conn:
            cursor = conn.execute(query, params)
            rows = cursor.fetchall()
    except sqlite3.Error as exc:
        raise SystemExit(f"SQL execution failed: {exc}")
    finally:
        conn.close()

    results: List[Dict[str, Any]] = []
    for row in rows:
        if row["energy_burned_kcal"] == 0.0:
            continue
        results.append(
            {
                "date": row["date"],
                "energy_burned_kcal": int(row["energy_burned_kcal"]),
                "steps": int(row["steps"]),
                "walk_distance_meters": int(row["walk_distance_meters"]),
            }
        )

    return results


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extract activity energy burned (kcal), steps, and walk distance from Apple Health DB"
        )
    )
    parser.add_argument(
        "--db",
        dest="db_path",
        required=True,
        help="Path to Health database (e.g., health_secure.sqlite)",
    )
    parser.add_argument(
        "--output",
        dest="output_path",
        default=None,
        help="Optional output file path for JSON (defaults to stdout)",
    )
    parser.add_argument(
        "--pretty",
        dest="pretty",
        action="store_true",
        help="Pretty-print JSON with indentation",
    )
    parser.add_argument(
        "--from",
        dest="date_from",
        metavar="YYYY-MM-DD",
        default=None,
        help="Inclusive start date (local) to filter by START_DATE",
    )
    parser.add_argument(
        "--to",
        dest="date_to",
        metavar="YYYY-MM-DD",
        default=None,
        help="Inclusive end date (local) to filter by START_DATE",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = parse_args(argv)

    db_path = os.path.expanduser(args.db_path)
    if not os.path.exists(db_path):
        raise SystemExit(f"Database not found: {db_path}")

    results = query_db(
        db_path=db_path,
        date_from=args.date_from,
        date_to=args.date_to,
    )

    indent = 2 if args.pretty else None
    separators = (",", ":") if not args.pretty else None
    payload = json.dumps(results, ensure_ascii=False, indent=indent, separators=separators)

    if args.output_path:
        out_path = os.path.expanduser(args.output_path)
        try:
            with open(out_path, "w", encoding="utf-8") as f:
                f.write(payload)
        except OSError as exc:
            raise SystemExit(f"Failed to write JSON to '{out_path}': {exc}")
    else:
        sys.stdout.write(payload + ("\n" if not payload.endswith("\n") else ""))


if __name__ == "__main__":
    main()
