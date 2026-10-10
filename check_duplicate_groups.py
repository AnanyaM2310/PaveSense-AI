
from app import create_app
from app.models.complaint import Complaint

app = create_app()

with app.app_context():
    complaints = Complaint.query.order_by(
        Complaint.id
    ).all()

    for c in complaints:
        print(
            f"ID={c.id} | "
            f"Damage={c.damage_type!r} | "
            f"Lat={c.latitude} | "
            f"Lon={c.longitude} | "
            f"Group={c.duplicate_group_id}"
        )
