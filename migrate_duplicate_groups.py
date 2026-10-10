
import os
import sqlite3

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DB_PATH = os.path.join(BASE_DIR, "pavesense.db")

if not os.path.exists(DB_PATH):
    raise FileNotFoundError(
        f"Database not found: {DB_PATH}"
    )

connection = sqlite3.connect(DB_PATH)

try:
    cursor = connection.cursor()

    columns = {
        row[1]
        for row in cursor.execute(
            "PRAGMA table_info(complaint)"
        ).fetchall()
    }

    if "duplicate_group_id" not in columns:
        cursor.execute(
            "ALTER TABLE complaint "
            "ADD COLUMN duplicate_group_id VARCHAR(36)"
        )
        print("Added complaint.duplicate_group_id")
    else:
        print("duplicate_group_id already exists")

    cursor.execute("""
        CREATE INDEX IF NOT EXISTS
        idx_complaint_duplicate_group_id
        ON complaint (duplicate_group_id)
    """)

    connection.commit()
    print("Duplicate grouping migration completed.")

except Exception:
    connection.rollback()
    raise

finally:
    connection.close()
