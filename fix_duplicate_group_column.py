
from app import create_app
from app.database.db import db
from sqlalchemy import text

app = create_app()

with app.app_context():
    columns = {
        row[1]
        for row in db.session.execute(
            text("PRAGMA table_info(complaint)")
        ).fetchall()
    }

    if "duplicate_group_id" not in columns:
        db.session.execute(
            text(
                "ALTER TABLE complaint "
                "ADD COLUMN duplicate_group_id VARCHAR(36)"
            )
        )
        print("Added duplicate_group_id to the active database.")
    else:
        print("duplicate_group_id already exists.")

    db.session.execute(
        text("""
            CREATE INDEX IF NOT EXISTS
            idx_complaint_duplicate_group_id
            ON complaint (duplicate_group_id)
        """)
    )

    db.session.commit()

    columns = {
        row[1]
        for row in db.session.execute(
            text("PRAGMA table_info(complaint)")
        ).fetchall()
    }

    print(
        "Verification:",
        "duplicate_group_id" in columns
    )
    print(
        "Database:",
        db.engine.url.render_as_string(hide_password=True)
    )
