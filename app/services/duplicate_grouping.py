
import math
import uuid

from app.database.db import db
from app.models.complaint import Complaint


DUPLICATE_DISTANCE_METRES = 20

DAMAGE_ALIASES = {
    "pothole": "pothole",
    "potholes": "pothole",
    "longitudinal crack": "longitudinal_crack",
    "longitudinal cracks": "longitudinal_crack",
    "transverse crack": "transverse_crack",
    "transverse cracks": "transverse_crack",
    "alligator crack": "alligator_crack",
    "alligator cracks": "alligator_crack",
    "waterlogging": "waterlogging",
    "missing manhole cover": "missing_manhole_cover",
    "broken streetlight": "broken_streetlight",
    "damaged road divider": "damaged_road_divider",
}


def normalize_damage_type(value):
    value = (value or "").strip().lower()
    return DAMAGE_ALIASES.get(
        value,
        value.replace(" ", "_")
    )


def gps_distance_metres(lat1, lon1, lat2, lon2):
    """Calculate great-circle distance between two GPS coordinates."""
    earth_radius = 6_371_000

    lat1, lon1, lat2, lon2 = map(
        math.radians,
        [lat1, lon1, lat2, lon2]
    )

    dlat = lat2 - lat1
    dlon = lon2 - lon1

    a = (
        math.sin(dlat / 2) ** 2
        + math.cos(lat1)
        * math.cos(lat2)
        * math.sin(dlon / 2) ** 2
    )

    return 2 * earth_radius * math.asin(
        min(1.0, math.sqrt(a))
    )


def group_duplicate_complaint(complaint_record):
    """
    Group a saved complaint with nearby reports of the same
    normalized damage type. Original complaints are preserved.
    """
    if complaint_record.id is None:
        raise ValueError("Save the complaint before grouping it.")

    lat = complaint_record.latitude
    lon = complaint_record.longitude

    if lat is None or lon is None:
        return None

    if not (
        -90 <= lat <= 90
        and -180 <= lon <= 180
    ):
        return None

    damage_type = normalize_damage_type(
        complaint_record.damage_type
    )

    if not damage_type:
        return None

    candidates = Complaint.query.filter(
        Complaint.id != complaint_record.id,
        Complaint.latitude.isnot(None),
        Complaint.longitude.isnot(None),
        Complaint.damage_type.isnot(None),
    ).all()

    matches = []

    for candidate in candidates:
        if not (
            -90 <= candidate.latitude <= 90
            and -180 <= candidate.longitude <= 180
        ):
            continue

        if normalize_damage_type(
            candidate.damage_type
        ) != damage_type:
            continue

        distance = gps_distance_metres(
            lat,
            lon,
            candidate.latitude,
            candidate.longitude,
        )

        if distance <= DUPLICATE_DISTANCE_METRES:
            matches.append((distance, candidate))

    if not matches:
        return None

    matches.sort(key=lambda item: item[0])

    # Prefer the closest existing group, if one exists.
    group_id = next(
        (
            candidate.duplicate_group_id
            for _, candidate in matches
            if candidate.duplicate_group_id
        ),
        None,
    )

    if not group_id:
        group_id = str(uuid.uuid4())

    # Merge groups when this report connects existing groups.
    old_group_ids = {
        candidate.duplicate_group_id
        for _, candidate in matches
        if candidate.duplicate_group_id
    }

    old_group_ids.discard(group_id)

    for old_group_id in old_group_ids:
        Complaint.query.filter_by(
            duplicate_group_id=old_group_id
        ).update(
            {"duplicate_group_id": group_id},
            synchronize_session=False,
        )

    # Attach every matching report to the selected group.
    for _, candidate in matches:
        candidate.duplicate_group_id = group_id

    complaint_record.duplicate_group_id = group_id

    # The caller commits this together with its other changes.
    db.session.flush()

    return group_id



def get_duplicate_count(group_id):
    if not group_id:
        return 0

    return Complaint.query.filter_by(
        duplicate_group_id=group_id,
        status="Submitted"
    ).count()
