from sqlalchemy import inspect, text
from app import create_app
from app.database.db import db


app = create_app()

with app.app_context():
    inspector = inspect(db.engine)

    if "complaint" not in inspector.get_table_names():
        raise RuntimeError(
            "The complaint table does not exist. "
            "Check your database configuration."
        )

    columns = {
        column["name"]
        for column in inspector.get_columns("complaint")
    }

    with db.engine.begin() as connection:
        if "recommended_authority" not in columns:
            connection.execute(text(
                "ALTER TABLE complaint "
                "ADD COLUMN recommended_authority VARCHAR(150)"
            ))
            print("Added recommended_authority")

        if "authority_note" not in columns:
            connection.execute(text(
                "ALTER TABLE complaint "
                "ADD COLUMN authority_note VARCHAR(255)"
            ))
            print("Added authority_note")

    print("Authority migration completed.")