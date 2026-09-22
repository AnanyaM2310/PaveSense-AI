import sqlite3
import os


BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DB_PATH = os.path.join(
    BASE_DIR,
    "pavesense.db"
)


def add_column_if_missing(cursor, table, column, definition):

    columns = [
        row[1]
        for row in cursor.execute(
            f"PRAGMA table_info({table})"
        ).fetchall()
    ]

    if column not in columns:

        cursor.execute(
            f"ALTER TABLE {table} "
            f"ADD COLUMN {column} {definition}"
        )

        print(f"Added column: {table}.{column}")

    else:

        print(f"Already exists: {table}.{column}")


connection = sqlite3.connect(DB_PATH)

cursor = connection.cursor()


# =========================
# COMPLAINT TABLE
# =========================

add_column_if_missing(
    cursor,
    "complaint",
    "english_description",
    "TEXT"
)

add_column_if_missing(
    cursor,
    "complaint",
    "user_id",
    "INTEGER"
)


# =========================
# USER TABLE
# =========================

add_column_if_missing(
    cursor,
    "user",
    "country",
    "TEXT"
)

add_column_if_missing(
    cursor,
    "user",
    "state",
    "TEXT"
)

add_column_if_missing(
    cursor,
    "user",
    "district",
    "TEXT"
)

add_column_if_missing(
    cursor,
    "user",
    "address",
    "TEXT"
)

add_column_if_missing(
    cursor,
    "user",
    "google_id",
    "VARCHAR(255)"
)

add_column_if_missing(
    cursor,
    "complaint",
    "nh_number",
    "VARCHAR(20)"
)

add_column_if_missing(
    cursor,
    "complaint",
    "highway_state",
    "VARCHAR(80)"
)

add_column_if_missing(
    cursor,
    "complaint",
    "sh_number",
    "VARCHAR(20)"
)
# Incident Details
add_column_if_missing(
    cursor,
    "complaint",
    "incident_date",
    "DATE"
)

add_column_if_missing(
    cursor,
    "complaint",
    "incident_time",
    "TIME"
)

add_column_if_missing(
    cursor,
    "complaint",
    "damage_type",
    "VARCHAR(100)"
)

add_column_if_missing(
    cursor,
    "complaint",
    "severity",
    "VARCHAR(20)"
)

add_column_if_missing(
    cursor,
    "complaint",
    "ai_confidence",
    "FLOAT"
)


connection.commit()

connection.close()

print("Database migration completed successfully.")