import os
import uuid

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    current_app,
    session
)

from werkzeug.utils import secure_filename

from app.database.db import db
from app.models.complaint import Complaint

from app.ai.language_detector import detect_language
from app.ai.translator import translate_to_english
from app.ai.image_analyzer import analyze_image
from app.ai.complaint_generator import generate_complaint


complaint = Blueprint(
    "complaint",
    __name__
)


# =========================================================
# UPLOAD COMPLAINT
# =========================================================

@complaint.route("/upload", methods=["GET", "POST"])
def upload():

    if request.method == "POST":

        # -------------------------------------------------
        # Check logged-in user
        # -------------------------------------------------

        user_id = session.get("user_id")

        if not user_id:
            return redirect(
                url_for("auth.login")
            )


        # -------------------------------------------------
        # Get uploaded image
        # -------------------------------------------------

        image = request.files.get("image")


        # -------------------------------------------------
        # Get description and language
        # -------------------------------------------------

        description = request.form.get(
            "description",
            ""
        ).strip()

        language = request.form.get(
            "language",
            "auto"
        )


        # -------------------------------------------------
        # Translate Complaint
        # -------------------------------------------------

        if language == "auto":

            language = detect_language(
                description
            )


        english_description = translate_to_english(
            description,
            language
        )


        # -------------------------------------------------
        # Save Uploaded Image
        # -------------------------------------------------

        image_path = None

        if image and image.filename != "":

            filename = (
                str(uuid.uuid4())
                + "_"
                + secure_filename(image.filename)
            )

            upload_folder = current_app.config[
                "UPLOAD_FOLDER"
            ]

            os.makedirs(
                upload_folder,
                exist_ok=True
            )

            image.save(
                os.path.join(
                    upload_folder,
                    filename
                )
            )

            image_path = filename


        # -------------------------------------------------
        # Create Complaint
        # -------------------------------------------------

        complaint_record = Complaint(

            user_id=session.get("user_id"),

            image_path=image_path,

            description=description,

            english_description=english_description,

            language=language,

            status="Draft"

        )


        # -------------------------------------------------
        # Save Complaint to Database
        # -------------------------------------------------

        db.session.add(
            complaint_record
        )

        db.session.commit()


        # -------------------------------------------------
        # Store Complaint ID in Session
        # -------------------------------------------------

        session["complaint_id"] = (
            complaint_record.id
        )


        # -------------------------------------------------
        # Continue Complaint Workflow
        # -------------------------------------------------

        return redirect(
            url_for("complaint.applicant")
        )


    return render_template(
        "complaint/upload.html"
    )


# =========================================================
# APPLICANT DETAILS
# =========================================================

@complaint.route("/applicant", methods=["GET", "POST"])
def applicant():

    complaint_id = session.get("complaint_id")

    if not complaint_id:
        return redirect(url_for("complaint.upload"))

    complaint_record = Complaint.query.get_or_404(complaint_id)

    if request.method == "POST":

        complaint_record.applicant_name = request.form.get(
            "applicant_name", ""
        ).strip()

        complaint_record.email = request.form.get(
            "email", ""
        ).strip()

        complaint_record.phone = request.form.get(
            "phone", ""
        ).strip()

        complaint_record.applying_for = request.form.get(
            "applying_for", ""
        ).strip()

        db.session.commit()

        return redirect(
            url_for("complaint.address")
        )

    return render_template(
        "complaint/applicant.html",
        complaint=complaint_record
    )


# =========================================================
# ADDRESS
# =========================================================

@complaint.route("/address", methods=["GET", "POST"])
def address():

    complaint_id = session.get("complaint_id")

    if not complaint_id:
        return redirect(url_for("complaint.upload"))

    complaint_record = Complaint.query.get_or_404(complaint_id)

    if request.method == "POST":

        complaint_record.country = request.form.get(
            "country", ""
        ).strip()

        complaint_record.state = request.form.get(
            "state", ""
        ).strip()

        complaint_record.district = request.form.get(
            "district", ""
        ).strip()

        complaint_record.local_body = request.form.get(
            "local_body", ""
        ).strip()

        complaint_record.ward = request.form.get(
            "ward", ""
        ).strip()

        complaint_record.house_no = request.form.get(
            "house_no", ""
        ).strip()

        complaint_record.post_office = request.form.get(
            "post_office", ""
        ).strip()

        complaint_record.pincode = request.form.get(
            "pincode", ""
        ).strip()

        db.session.commit()

        return redirect(
            url_for("complaint.road_details")
        )

    return render_template(
        "complaint/address.html",
        complaint=complaint_record
    )


# =========================================================
# ROAD DETAILS
# =========================================================

@complaint.route("/road-details", methods=["GET", "POST"])
def road_details():

    # Get the current complaint
    complaint_id = session.get("complaint_id")

    # If there is no active complaint, go back to upload
    if not complaint_id:
        return redirect(url_for("complaint.upload"))

    # Find the complaint
    complaint_record = Complaint.query.get_or_404(complaint_id)


    # If user clicked Next
    if request.method == "POST":

        # Save road type
        complaint_record.road_type = request.form.get(
            "road_type",
            ""
        ).strip()


        # Save National Highway number
        complaint_record.nh_number = request.form.get(
            "nh_number",
            ""
        ).strip()


        # Save State Highway state
        complaint_record.highway_state = request.form.get(
            "highway_state",
            ""
        ).strip()


        # Save State Highway number
        complaint_record.sh_number = request.form.get(
            "sh_number",
            ""
        ).strip()


        # Save everything to database
        db.session.commit()


        # Move to Incident Details
        return redirect(
            url_for("complaint.incident")
        )


    # Display the page
    return render_template(
        "complaint/road_details.html",
        complaint=complaint_record
    )

# =========================================================
# INCIDENT
# =========================================================

@complaint.route("/incident", methods=["GET", "POST"])
def incident():

    complaint_id = session.get("complaint_id")

    if not complaint_id:
        return redirect(
            url_for("complaint.upload")
        )

    complaint_record = Complaint.query.get_or_404(
        complaint_id
    )


    if request.method == "POST":

        # -----------------------------
        # Incident Date
        # -----------------------------

        incident_date = request.form.get(
            "incident_date"
        )

        if incident_date:

            from datetime import datetime

            complaint_record.incident_date = (
                datetime.strptime(
                    incident_date,
                    "%Y-%m-%d"
                ).date()
            )


        # -----------------------------
        # Incident Time
        # -----------------------------

        incident_time = request.form.get(
            "incident_time"
        )

        if incident_time:

            from datetime import datetime

            complaint_record.incident_time = (
                datetime.strptime(
                    incident_time,
                    "%H:%M"
                ).time()
            )


        # -----------------------------
        # Location
        # -----------------------------

        latitude = request.form.get("latitude")

        longitude = request.form.get("longitude")


        if latitude:

            complaint_record.latitude = float(latitude)


        if longitude:

            complaint_record.longitude = float(longitude)


        # -----------------------------
        # Save
        # -----------------------------

        db.session.commit()


        # Go to AI analysis

        return redirect(
            url_for("complaint.analysis")
        )


    return render_template(
        "complaint/incident.html",
        complaint=complaint_record
    )


# =========================================================
# AI ANALYSIS
# =========================================================

@complaint.route("/analysis")
def analysis():

    complaint_id = session.get("complaint_id")

    if not complaint_id:
        return redirect(
            url_for("complaint.upload")
        )

    complaint_record = Complaint.query.get_or_404(
        complaint_id
    )

    # -------------------------------------------------
    # Get uploaded image
    # -------------------------------------------------

    if not complaint_record.image_path:

        return redirect(
            url_for("complaint.preview")
        )

    upload_folder = current_app.config[
        "UPLOAD_FOLDER"
    ]

    image_path = os.path.join(
        upload_folder,
        complaint_record.image_path
    )

    # -------------------------------------------------
    # Run AI
    # -------------------------------------------------

    result = analyze_image(
        image_path
    )

    print(
        "PaveSense AI RESULT:",
        result
    )

    # -------------------------------------------------
    # Save AI result
    # -------------------------------------------------

    if result["success"]:

        complaint_record.severity = result["severity"]

        complaint_record.damage_type = result["damage_type"]

        complaint_record.ai_confidence = result["confidence"]

    # -------------------------------------------------
    # GENERATE ACTUAL AI COMPLAINT
    # -------------------------------------------------

        generated_complaint = generate_complaint(

            damage_type=result["damage_type"],

            severity=result["severity"],

            confidence=result["confidence"],

            applicant_name=complaint_record.applicant_name,

            country=complaint_record.country,

            state=complaint_record.state,

            district=complaint_record.district,

            local_body=complaint_record.local_body,

            ward=complaint_record.ward,

            house_no=complaint_record.house_no,

            post_office=complaint_record.post_office,

            pincode=complaint_record.pincode,

            road_type=complaint_record.road_type,

            nh_number=complaint_record.nh_number,

            highway_state=complaint_record.highway_state,

            sh_number=complaint_record.sh_number,

            latitude=complaint_record.latitude,

            longitude=complaint_record.longitude,

            incident_date=complaint_record.incident_date,

            incident_time=complaint_record.incident_time,

            description=complaint_record.description
        )


    # -------------------------------------------------
    # SAVE GENERATED COMPLAINT
    # -------------------------------------------------

        complaint_record.complaint_text = generated_complaint

        db.session.commit()


    # Store analysis + generated complaint in session

        result["generated_complaint"] = (
            generated_complaint
        )

        session["ai_result"] = result

    else:

        session["ai_result"] = {
            "success": False,
            "damage_type": "Analysis failed",
            "confidence": 0,
            "severity": "Not analyzed",
            "detection_count": 0,
            "area_ratio": 0
        }

    return render_template(
        "complaint/analysis.html"
    )
# =========================================================
# COMPLAINT PREVIEW
# =========================================================

@complaint.route("/preview")
def preview():

    complaint_id = session.get(
        "complaint_id"
    )

    if not complaint_id:
        return redirect(
            url_for("complaint.upload")
        )

    complaint_record = Complaint.query.get_or_404(
        complaint_id
    )

    analysis_result = session.get(
        "ai_result"
    )

    if not analysis_result:
        analysis_result = {
            "success": False,
            "damage_type": None,
            "confidence": None,
            "severity": None,
            "detection_count": 0,
            "area_ratio": 0,
            "message": "AI analysis has not been completed."
        }

    return render_template(
        "complaint/preview.html",
        complaint=complaint_record,
        analysis=analysis_result
    )


# =========================================================
# COMPLAINT SUBMISSION
# =========================================================

@complaint.route("/submit")
def submit():

    return render_template(
        "complaint/submit.html"
    )


# =========================================================
# SUCCESS PAGE
# =========================================================

@complaint.route("/success")
def success():

    return render_template(
        "complaint/success.html"
    )