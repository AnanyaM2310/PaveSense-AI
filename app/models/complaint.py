from datetime import datetime
from app.database.db import db


class Complaint(db.Model):

    id = db.Column(db.Integer, primary_key=True)

    user_id = db.Column(
    db.Integer,
    db.ForeignKey("user.id"),
    nullable=True
    )

    # Upload Information
    image_path = db.Column(db.String(255))
    description = db.Column(db.Text)
    english_description = db.Column(db.Text)
    language = db.Column(db.String(50))
    status = db.Column(
    db.String(30),
    default="Draft",
    nullable=False
    )

    # Applicant Details
    applicant_name = db.Column(db.String(120))
    email = db.Column(db.String(120))
    phone = db.Column(db.String(20))
    applying_for = db.Column(db.String(50))

    # Address
    country = db.Column(db.String(80))
    state = db.Column(db.String(80))
    district = db.Column(db.String(80))
    local_body = db.Column(db.String(100))
    ward = db.Column(db.String(50))
    house_no = db.Column(db.String(50))
    post_office = db.Column(db.String(80))
    pincode = db.Column(db.String(10))

    # Road Details
    road_type = db.Column(db.String(50))
    nh_number = db.Column(db.String(20))
    highway_state = db.Column(db.String(80))
    sh_number = db.Column(db.String(20))

    # Recommended road authority
    recommended_authority = db.Column(db.String(150))
    authority_note = db.Column(db.String(255))

    # Location
    latitude = db.Column(db.Float)
    longitude = db.Column(db.Float)

    # Incident Details
    incident_date = db.Column(db.Date)
    incident_time = db.Column(db.Time)

    # AI
    damage_type = db.Column(db.String(100))
    severity = db.Column(db.String(30))
    ai_confidence = db.Column(db.Float)
    complaint_text = db.Column(db.Text)

    # Tracking
    complaint_number = db.Column(db.String(50))
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

    # Duplicate complaint grouping
    duplicate_group_id = db.Column(
        db.String(36),
        nullable=True,
        index=True
    )