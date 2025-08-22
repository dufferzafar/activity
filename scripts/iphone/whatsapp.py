#!/usr/bin/env python3
import argparse
import json
import sqlite3
from typing import Any, Dict, List, Optional


def build_query(scope: str, start_date: Optional[str], end_date: Optional[str]) -> tuple[str, List[Any]]:
    """
    Build a SQL query that returns daily counts of sent/received messages.

    Columns: date (YYYY-MM-DD), msgs_sent, msgs_recvd

    - scope: one of {"all", "direct", "groups"}
    - start_date/end_date: inclusive bounds in YYYY-MM-DD (applied after converting Apple epoch)
    """
    params: List[Any] = []

    # Base query over ZWAMESSAGE with a join to ZWACHATSESSION (to allow filtering by session type)
    # Convert Apple epoch (seconds since 2001-01-01) to Unix epoch with + 978307200
    base = [
        "SELECT",
        "  date(datetime(m.ZMESSAGEDATE + 978307200, 'unixepoch')) AS date,",
        "  SUM(CASE WHEN m.ZISFROMME = 1 THEN 1 ELSE 0 END) AS msgs_sent,",
        "  SUM(CASE WHEN m.ZISFROMME = 0 THEN 1 ELSE 0 END) AS msgs_recvd",
        "FROM ZWAMESSAGE m",
        "LEFT JOIN ZWACHATSESSION s ON s.Z_PK = m.ZCHATSESSION",
    ]

    conditions = []

    # Exclude system/group membership events; keep real message/media types.
    # On iOS, 6 is group_event in many builds. Safeguard with NULL handling.
    conditions.append("(m.ZMESSAGETYPE IS NULL OR m.ZMESSAGETYPE <> 6)")

    if scope == "direct":
        conditions.append("s.ZSESSIONTYPE = 0")  # 0 = one-to-one chats
    elif scope == "groups":
        conditions.append("s.ZSESSIONTYPE = 1")  # 1 = groups
    # else: all chats (no condition)

    # Date range filter (inclusive) on the converted date
    if start_date is not None:
        conditions.append("date(datetime(m.ZMESSAGEDATE + 978307200, 'unixepoch')) >= ?")
        params.append(start_date)
    if end_date is not None:
        conditions.append("date(datetime(m.ZMESSAGEDATE + 978307200, 'unixepoch')) <= ?")
        params.append(end_date)

    if conditions:
        base.append("WHERE " + " AND ".join(conditions))

    base.append("GROUP BY date")
    base.append("ORDER BY date")

    query = "\n".join(base)
    return query, params


def fetch_daily_counts(db_path: str, scope: str, start_date: Optional[str], end_date: Optional[str]) -> List[Dict[str, Any]]:
    query, params = build_query(scope, start_date, end_date)
    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        cur.execute(query, params)
        rows = cur.fetchall()
        result = [
            {
                "date": r[0],
                "msgs_sent": int(r[1]) if r[1] is not None else 0,
                "msgs_recvd": int(r[2]) if r[2] is not None else 0,
            }
            for r in rows
        ]
        return result
    finally:
        conn.close()


def main() -> None:
    parser = argparse.ArgumentParser(description="Daily WhatsApp message counts (sent vs received) from ChatStorage.sqlite")
    parser.add_argument("db", help="Path to WhatsApp ChatStorage.sqlite (iOS backup extract)")
    parser.add_argument(
        "--scope",
        choices=["all", "direct", "groups"],
        default="all",
        help="Filter to direct (one-to-one) chats, group chats, or all (default)",
    )
    parser.add_argument(
        "--start-date",
        dest="start_date",
        help="Inclusive start date (YYYY-MM-DD). Applied after Apple→Unix time conversion.",
    )
    parser.add_argument(
        "--end-date",
        dest="end_date",
        help="Inclusive end date (YYYY-MM-DD). Applied after Apple→Unix time conversion.",
    )
    parser.add_argument(
        "--out",
        dest="out_path",
        help="Optional output file path for JSON. If omitted, prints to stdout.",
    )

    args = parser.parse_args()

    data = fetch_daily_counts(args.db, args.scope, args.start_date, args.end_date)

    if args.out_path:
        with open(args.out_path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
    else:
        print(json.dumps(data, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()


