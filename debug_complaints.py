
from app import create_app
from app.models.complaint import Complaint
from app.services.duplicate_grouping import get_duplicate_count

app = create_app()

with app.app_context():
    for c in Complaint.query.order_by(Complaint.id.desc()).limit(15).all():
        print(
            f"ID={c.id} | User ID={c.user_id} | "
            f"Email={c.email} | Status={c.status} | "
            f"Damage={c.damage_type} | "
            f"Lat={c.latitude} | Lon={c.longitude} | "
            f"Group={c.duplicate_group_id} | "
            f"Related={get_duplicate_count(c.duplicate_group_id)}"
        )
