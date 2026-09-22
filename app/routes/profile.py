from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    session,
    flash
)

from app.database.db import db
from app.models.user import User
from app.models.complaint import Complaint


profile = Blueprint(
    "profile",
    __name__
)


@profile.route("/profile", methods=["GET", "POST"])
def home():

    # Check if user is logged in
    user_id = session.get("user_id")

    if not user_id:
        return redirect(
            url_for("auth.login")
        )

    # Get logged-in user
    user = User.query.get(user_id)

    if user is None:
        session.clear()

        return redirect(
            url_for("auth.login")
        )

    # =========================
    # SAVE PROFILE CHANGES
    # =========================

    if request.method == "POST":

        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip()
        phone = request.form.get("phone", "").strip()
        country = request.form.get("country", "").strip()
        state = request.form.get("state", "").strip()
        district = request.form.get("district", "").strip()
        address = request.form.get("address", "").strip()

        # Basic validation
        if not name or not email or not phone:

            flash(
                "Name, email and phone number are required.",
                "error"
            )

            return redirect(
                url_for("profile.home")
            )

        # Check whether email belongs to another user
        existing_user = User.query.filter(
            User.email == email,
            User.id != user.id
        ).first()

        if existing_user:

            flash(
                "This email is already being used by another account.",
                "error"
            )

            return redirect(
                url_for("profile.home")
            )

        # Update user information
        user.name = name
        user.email = email
        user.phone = phone
        user.country = country
        user.state = state
        user.district = district
        user.address = address

        db.session.commit()

        # Update session information
        session["user_name"] = user.name
        session["user_email"] = user.email

        flash(
            "Profile updated successfully.",
            "success"
        )

        return redirect(
            url_for("profile.home")
        )

    # =========================
    # COMPLAINT STATISTICS
    # =========================

    complaints = Complaint.query.filter_by(
        user_id=user.id
    ).all()

    total_complaints = len(complaints)

    resolved_complaints = sum(
        1
        for complaint in complaints
        if complaint.status == "Resolved"
    )

    pending_complaints = sum(
        1
        for complaint in complaints
        if complaint.status in [
            "Draft",
            "Submitted",
            "Under Review"
        ]
    )

    return render_template(
        "profile/index.html",
        user=user,
        total_complaints=total_complaints,
        resolved_complaints=resolved_complaints,
        pending_complaints=pending_complaints
    )