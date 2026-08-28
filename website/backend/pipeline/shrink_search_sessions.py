#!/usr/bin/env python3
"""
One-off migration: shrink existing search_sessions.results rows.

Historically every search stored the full candidate object (name, headline,
skills, experiences, education, ...) for every result - ~7 kB per candidate,
duplicated across every search that returned that person. A single row was
often 0.5-3.5 MB and the column had grown to ~330 MB.

This script rewrites each row's `results` array in place, keeping only the
primary key (linkedin_url) plus search-specific metadata (match, scores,
fit_description). The backend reconstructs the full objects on read by joining
the candidates table (see save_search.hydrate_results).

Rows that are already slim are skipped, so this is safe to re-run.

Usage:
    cd website/backend
    python pipeline/shrink_search_sessions.py            # apply
    python pipeline/shrink_search_sessions.py --dry-run  # report only

After running, reclaim disk space (needs an exclusive lock, run off-peak):
    VACUUM FULL search_sessions;
"""
import argparse
import json
import os
import sys
import urllib.parse

import psycopg2

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))
from save_search import REFERENCE_FIELDS  # noqa: E402

from dotenv import load_dotenv  # noqa: E402

BATCH_SIZE = 200


def get_connection():
    load_dotenv(os.path.join(os.path.dirname(__file__), '..', '..', '.env'))
    supabase_url = os.getenv('SUPABASE_URL')
    db_password = os.getenv('SUPABASE_DB_PASSWORD')
    if not supabase_url or not db_password:
        raise SystemExit("Missing SUPABASE_URL or SUPABASE_DB_PASSWORD in .env")
    project_ref = supabase_url.replace('https://', '').replace('.supabase.co', '')
    encoded_password = urllib.parse.quote_plus(db_password)
    conn_string = (
        f"postgresql://postgres.{project_ref}:{encoded_password}"
        f"@aws-1-us-east-2.pooler.supabase.com:6543/postgres"
    )
    return psycopg2.connect(conn_string)


def is_slim(results):
    """A row is already slim if no element carries full candidate data."""
    return not any(
        isinstance(item, dict) and ("name" in item or "experiences" in item)
        for item in (results or [])
    )


def slim_row(results):
    slim = []
    for candidate in results or []:
        if not isinstance(candidate, dict) or not candidate.get("linkedin_url"):
            continue
        slim.append({k: candidate[k] for k in REFERENCE_FIELDS if k in candidate})
    return slim


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--dry-run', action='store_true', help="report without writing")
    args = parser.parse_args()

    conn = get_connection()
    conn.autocommit = False
    cursor = conn.cursor()

    cursor.execute("SELECT count(*) FROM search_sessions WHERE jsonb_typeof(results) = 'array'")
    total = cursor.fetchone()[0]
    print(f"Scanning {total} search_sessions rows (batch size {BATCH_SIZE})...")

    cursor.execute("""
        SELECT id, results
        FROM search_sessions
        WHERE jsonb_typeof(results) = 'array'
        ORDER BY id
    """)

    scanned = already_slim = shrunk = 0
    bytes_before = bytes_after = 0

    while True:
        rows = cursor.fetchmany(BATCH_SIZE)
        if not rows:
            break

        updates = []
        for row_id, results in rows:
            scanned += 1
            if is_slim(results):
                already_slim += 1
                continue
            slim = slim_row(results)
            bytes_before += len(json.dumps(results))
            bytes_after += len(json.dumps(slim))
            updates.append((json.dumps(slim), len(slim), str(row_id)))

        if updates and not args.dry_run:
            write_cur = conn.cursor()
            write_cur.executemany(
                "UPDATE search_sessions SET results = %s, total_results = %s WHERE id = %s",
                updates,
            )
            write_cur.close()
            conn.commit()

        shrunk += len(updates)
        print(f"  scanned={scanned}/{total}  shrunk={shrunk}  already_slim={already_slim}")

    cursor.close()
    conn.close()

    mb = 1024 * 1024
    print("\n" + "=" * 60)
    print(f"{'DRY RUN - ' if args.dry_run else ''}Done.")
    print(f"  rows scanned:      {scanned}")
    print(f"  rows shrunk:       {shrunk}")
    print(f"  rows already slim: {already_slim}")
    print(f"  results JSON size: {bytes_before / mb:.1f} MB -> {bytes_after / mb:.1f} MB")
    if not args.dry_run and shrunk:
        print("\nNext: reclaim disk space with  VACUUM FULL search_sessions;")
    print("=" * 60)


if __name__ == '__main__':
    main()
