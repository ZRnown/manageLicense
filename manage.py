#!/usr/bin/env python3
import argparse
import datetime
import os
import sqlite3
import sys
import uuid
from typing import List


DEFAULT_DB = os.environ.get("LICENSE_DB", "licenses.db")


def init_db(conn: sqlite3.Connection) -> None:
    cursor = conn.cursor()
    cursor.execute(
        """CREATE TABLE IF NOT EXISTS licenses (
            key_str TEXT PRIMARY KEY,
            is_used INTEGER DEFAULT 0,
            hwid TEXT,
            created_at TEXT,
            valid_days INTEGER,
            activated_at TEXT,
            note TEXT
        )"""
    )
    conn.commit()


def generate_keys(db_path: str, count: int, days: int, note: str) -> List[str]:
    conn = sqlite3.connect(db_path)
    init_db(conn)
    cursor = conn.cursor()
    keys: List[str] = []
    for _ in range(count):
        key = str(uuid.uuid4()).upper()
        now = datetime.datetime.now().isoformat()
        cursor.execute(
            "INSERT INTO licenses (key_str, valid_days, created_at, note) VALUES (?, ?, ?, ?)",
            (key, days, now, note),
        )
        keys.append(key)
    conn.commit()
    conn.close()
    return keys


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description="License server management utilities.")
    subparsers = parser.add_subparsers(dest="command", required=True)

    gen = subparsers.add_parser("gen", help="Generate license keys.")
    gen.add_argument(
        "-n",
        "--count",
        type=int,
        default=1,
        help="Number of keys to generate (1-100).",
    )
    gen.add_argument(
        "-d",
        "--days",
        type=int,
        default=-1,
        help="Validity days (-1 for permanent).",
    )
    gen.add_argument(
        "-m",
        "--note",
        default="",
        help="Optional note to store with each key.",
    )
    gen.add_argument(
        "--db",
        default=DEFAULT_DB,
        help="SQLite database path (default: licenses.db).",
    )

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()

    if args.command == "gen":
        if args.count < 1 or args.count > 100:
            print("Error: --count must be between 1 and 100.", file=sys.stderr)
            return 1
        if args.days != -1 and args.days <= 0:
            print("Error: --days must be -1 or a positive integer.", file=sys.stderr)
            return 1

        keys = generate_keys(args.db, args.count, args.days, args.note)
        print("\n".join(keys))
        return 0

    parser.print_help()
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
