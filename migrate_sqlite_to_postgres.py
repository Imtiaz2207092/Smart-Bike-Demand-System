import sqlite3
from pathlib import Path

from sqlalchemy import text
from app.database import engine

SQLITE_PATH = (
    Path(__file__).resolve()
    / "backend"
    / "smart_bike.db"
)

# Correct the path because this script is in the project root.
SQLITE_PATH = Path(__file__).resolve().parent / "backend" / "smart_bike.db"

TABLE_COLUMNS = {
    "stations": [
        "station_id",
        "station_name",
        "latitude",
        "longitude",
        "capacity",
        "station_type",
    ],
    "station_snapshots": [
        "id",
        "station_id",
        "available_bikes",
        "available_docks",
        "recorded_at",
    ],
}


def main():
    if not SQLITE_PATH.exists():
        raise FileNotFoundError(f"SQLite database not found: {SQLITE_PATH}")

    source = sqlite3.connect(str(SQLITE_PATH))
    source.row_factory = sqlite3.Row

    try:
        rows_by_table = {}
        for table, columns in TABLE_COLUMNS.items():
            column_sql = ", ".join(f'"{c}"' for c in columns)
            rows_by_table[table] = source.execute(
                f'SELECT {column_sql} FROM "{table}"'
            ).fetchall()

        with engine.begin() as target:
            # Only insert records when the target tables are empty.
            for table in TABLE_COLUMNS:
                count = target.execute(
                    text(f'SELECT COUNT(*) FROM "{table}"')
                ).scalar_one()
                if count != 0:
                    raise RuntimeError(
                        f"Target table {table} already contains {count} rows. "
                        "Migration stopped without inserting records."
                    )

            # Copy stations before snapshots.
            for table, rows in rows_by_table.items():
                if not rows:
                    print(f"{table}: no source rows to copy")
                    continue

                columns = TABLE_COLUMNS[table]
                column_sql = ", ".join(f'"{c}"' for c in columns)
                values_sql = ", ".join(f":{c}" for c in columns)
                statement = text(
                    f'INSERT INTO "{table}" ({column_sql}) '
                    f"VALUES ({values_sql})"
                )

                records = [dict(row) for row in rows]
                target.execute(statement, records)
                print(f"{table}: copied {len(records)} rows")

        # Verify source and target counts.
        with engine.connect() as target:
            for table, rows in rows_by_table.items():
                pg_count = target.execute(
                    text(f'SELECT COUNT(*) FROM "{table}"')
                ).scalar_one()
                print(
                    f"VERIFY {table}: SQLite={len(rows)}, "
                    f"PostgreSQL={pg_count}"
                )
                if pg_count != len(rows):
                    raise RuntimeError(f"Count mismatch in {table}")

        print("Migration completed and row counts verified.")

    finally:
        source.close()


if __name__ == "__main__":
    main()
