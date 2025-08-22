"""
Extract daily incoming/outgoing call counts and seconds from an iOS
call history SQLite database and output JSON.

The query converts CFAbsoluteTime (`ZDATE`) to local-date using
`DATE(ZDATE + 978307200, 'unixepoch', 'localtime')` and aggregates by day.

Fields in output per row:
  - date (YYYY-MM-DD)
  - incoming_count (int)
  - outgoing_count (int)
  - incoming_seconds (int, rounded)
  - outgoing_seconds (int, rounded)

Optionally filter by date range and/or include only connected calls
(duration > 0).

Reference for `ZCALLRECORD` semantics: "Hello! Who is on the Line?"
https://metadataperspective.com/2025/02/05/hello-who-is-on-the-line/
"""

from __future__ import annotations

import argparse
import json
import os
import sqlite3
import sys
from typing import Any, Dict, List, Optional, Sequence, Tuple


def build_query(connected_only: bool, date_from: Optional[str], date_to: Optional[str]) -> Tuple[str, Sequence[Any]]:
    """Build the SQL query and parameters based on filters.

    - connected_only: include only rows with duration > 0
    - date_from/date_to: filter inclusive on computed local date (YYYY-MM-DD)
    """

    # Use a CTE to avoid repeating the DATE() conversion in WHERE/GROUP BY
    cte_filters: List[str] = []
    params: List[Any] = []

    if connected_only:
        # `ZANSWERED = 1` is also indicative, but duration > 0 is more universal
        cte_filters.append("ZDURATION > 0")

    cte_where = (" WHERE " + " AND ".join(cte_filters)) if cte_filters else ""

    outer_filters: List[str] = []
    if date_from is not None:
        outer_filters.append("date >= ?")
        params.append(date_from)
    if date_to is not None:
        outer_filters.append("date <= ?")
        params.append(date_to)

    outer_where = (" WHERE " + " AND ".join(outer_filters)) if outer_filters else ""

    query = f"""
        WITH calls AS (
            SELECT
                DATE(ZDATE + 978307200, 'unixepoch', 'localtime') AS date,
                ZORIGINATED AS originated,
                COALESCE(ZDURATION, 0) AS duration
            FROM ZCALLRECORD{cte_where}
        )
        SELECT
            date,
            SUM(CASE WHEN originated = 0 THEN 1 ELSE 0 END) AS incoming_count,
            SUM(CASE WHEN originated = 1 THEN 1 ELSE 0 END) AS outgoing_count,
            ROUND(SUM(CASE WHEN originated = 0 THEN duration ELSE 0 END)) AS incoming_seconds,
            ROUND(SUM(CASE WHEN originated = 1 THEN duration ELSE 0 END)) AS outgoing_seconds
        FROM calls{outer_where}
        GROUP BY date
        ORDER BY date;
    """

    return query, params


def query_db(db_path: str, connected_only: bool, date_from: Optional[str], date_to: Optional[str]) -> List[Dict[str, Any]]:
    query, params = build_query(connected_only=connected_only, date_from=date_from, date_to=date_to)

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
        results.append(
            {
                "date": row["date"],
                "incoming_count": int(row["incoming_count"] or 0),
                "outgoing_count": int(row["outgoing_count"] or 0),
                "incoming_seconds": int(row["incoming_seconds"] or 0),
                "outgoing_seconds": int(row["outgoing_seconds"] or 0),
            }
        )

    return results


def parse_args(argv: Optional[Sequence[str]] = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Aggregate daily incoming/outgoing call counts and seconds from an iOS call history DB"
        )
    )
    parser.add_argument(
        "--db",
        dest="db_path",
        required=True,
        help="Path to SQLite database (e.g., CallHistory.storedata or call_history.db)",
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
        "--connected-only",
        dest="connected_only",
        action="store_true",
        help="Include only connected calls (duration > 0)",
    )
    parser.add_argument(
        "--from",
        dest="date_from",
        metavar="YYYY-MM-DD",
        default=None,
        help="Inclusive start date (local) to filter results",
    )
    parser.add_argument(
        "--to",
        dest="date_to",
        metavar="YYYY-MM-DD",
        default=None,
        help="Inclusive end date (local) to filter results",
    )
    return parser.parse_args(argv)


def main(argv: Optional[Sequence[str]] = None) -> None:
    args = parse_args(argv)

    db_path = os.path.expanduser(args.db_path)
    if not os.path.exists(db_path):
        raise SystemExit(f"Database not found: {db_path}")

    results = query_db(
        db_path=db_path,
        connected_only=args.connected_only,
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


