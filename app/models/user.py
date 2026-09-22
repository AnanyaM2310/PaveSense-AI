from werkzeug.security import generate_password_hash, check_password_hash
from app.database.db import db
from datetime import datetime


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)

    # --------------------------------
    # Basic User Information
    # --------------------------------

    name = db.Column(
        db.String(120),
        nullable=False
    )

    email = db.Column(
        db.String(120),
        unique=True,
        nullable=False
    )

    phone = db.Column(
        db.String(20),
        nullable=True
    )

    # --------------------------------
    # Password / Google Login
    # --------------------------------

    # Nullable because Google users may not have a password
    password_hash = db.Column(
        db.String(255),
        nullable=True
    )

    # Google account ID
    google_id = db.Column(
        db.String(255),
        unique=True,
        nullable=True
    )

    # --------------------------------
    # Profile Information
    # --------------------------------

    country = db.Column(
        db.String(80),
        nullable=True
    )

    state = db.Column(
        db.String(80),
        nullable=True
    )

    district = db.Column(
        db.String(80),
        nullable=True
    )

    address = db.Column(
        db.String(255),
        nullable=True
    )

    # --------------------------------
    # Account Creation
    # --------------------------------

    created_at = db.Column(
        db.DateTime,
        default=datetime.utcnow
    )

    # --------------------------------
    # Relationship with Complaints
    # --------------------------------

    complaints = db.relationship(
        "Complaint",
        backref="user",
        lazy=True
    )

    # --------------------------------
    # Password Functions
    # --------------------------------

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        if not self.password_hash:
            return False

        return check_password_hash(
            self.password_hash,
            password
        )