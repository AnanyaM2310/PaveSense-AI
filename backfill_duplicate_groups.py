
from app import create_app
from app.database.db import db
from app.models.complaint import Complaint
from app.services.duplicate_grouping import group_duplicate_complaint

app = create_app()

with app.app_context():
    complaints = Complaint.query.order_by(
        Complaint.id.asc()
    ).all()

    grouped = 0
    skipped = 0

    try:
        for complaint in complaints:
            if (
                not complaint.damage_type
                or complaint.latitude is None
                or complaint.longitude is None
            ):
                skipped += 1
                continue

            previous_group = complaint.duplicate_group_id

            group_id = group_duplicate_complaint(complaint)

            if group_id:
                grouped += 1
                print(
                    f"Complaint #{complaint.id}: "
                    f"group={group_id}"
                )
            else:
                print(
                    f"Complaint #{complaint.id}: "
                    "no nearby compatible duplicate"
                )

        db.session.commit()

        print("\nBackfill completed.")
        print(f"Complaints assigned to groups: {grouped}")
        print(f"Complaints skipped: {skipped}")

    except Exception:
        db.session.rollback()
        raise
