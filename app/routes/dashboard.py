from flask import Blueprint, render_template, redirect, url_for, session

from app.models.complaint import Complaint


dashboard = Blueprint(
    "dashboard",
    __name__
)


# =========================================================
# DASHBOARD
# =========================================================

@dashboard.route("/dashboard")
def home():

    user_id = session.get("user_id")

    # User must be logged in
    if not user_id:
        return redirect(
            url_for("auth.login")
        )

    return render_template(
        "dashboard/index.html"
    )


# =========================================================
# COMPLAINT HISTORY
# =========================================================

@dashboard.route("/complaint-history")
def history():

    user_id = session.get("user_id")

    # User must be logged in
    if not user_id:
        return redirect(
            url_for("auth.login")
        )

    # Get only complaints belonging to this user
    complaints = Complaint.query.filter_by(
        user_id=user_id
    ).order_by(
        Complaint.created_at.desc()
    ).all()

    return render_template(
        "dashboard/history.html",
        complaints=complaints
    )


# =========================================================
# COMPLAINT DETAILS
# =========================================================

@dashboard.route("/complaint/<int:complaint_id>")
def complaint_details(complaint_id):

    user_id = session.get("user_id")

    # User must be logged in
    if not user_id:
        return redirect(
            url_for("auth.login")
        )

    # IMPORTANT:
    # Only allow the logged-in user to view their own complaint
    complaint_record = Complaint.query.filter_by(
        id=complaint_id,
        user_id=user_id
    ).first_or_404()

    return render_template(
        "dashboard/complaint_details.html",
        complaint=complaint_record
    )