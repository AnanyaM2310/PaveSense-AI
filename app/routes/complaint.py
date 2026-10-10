import os
import uuid

from datetime import datetime

from flask import (
    Blueprint,
    render_template,
    request,
    redirect,
    url_for,
    current_app,
    session,
    flash,
)

from werkzeug.utils import secure_filename
from sqlalchemy import and_

from app.database.db import db
from app.models.complaint import Complaint

from app.ai.language_detector import detect_language
from app.ai.translator import translate_to_english
from app.ai.image_analyzer import analyze_image
from app.ai.complaint_generator import generate_complaint

from app.services.duplicate_grouping import group_duplicate_complaint
from app.email.email_service import send_registration_email

# =========================================================
# BLUEPRINT
# =========================================================

complaint = Blueprint(
    "complaint",
    __name__
)
def recommend_road_authority(road_type):
    """
    Recommend a likely authority from the selected road type.
    This is a recommendation, not a verified ownership lookup.
    """
    road_type = (road_type or "").strip().lower()

    recommendations = {
        "nh": (
            "NHAI / National Highway Authority",
            "Verify the highway's actual maintaining authority."
        ),
        "sh": (
            "State PWD / State Highway Division",
            "Verify the state highway's actual maintaining authority."
        ),
        "urban": (
            "Municipality / Municipal Corporation",
            "Verify whether the road is maintained by the local body or PWD."
        ),
        "rural": (
            "Gram Panchayat / Local Self Government",
            "Verify whether the road is maintained by the Panchayat or PWD."
        ),
    }

    return recommendations.get(
        road_type,
        (
            "Authority not determined",
            "Verify the road type and responsible authority."
        )
    )
def get_current_complaint():
    user_id = session.get("user_id")
    complaint_id = session.get("complaint_id")

    if not user_id or not complaint_id:
        return None

    return Complaint.query.filter_by(
        id=complaint_id,
        user_id=user_id
    ).first()

# =========================================================
# UPLOAD COMPLAINT
# =========================================================

@complaint.route(
    "/upload",
    methods=["GET", "POST"]
)
def upload():

    if request.method == "POST":

        # -------------------------------------------------
        # CHECK LOGGED-IN USER
        # -------------------------------------------------

        user_id = session.get("user_id")

        if not user_id:
            return redirect(
                url_for("auth.login")
            )

        # -------------------------------------------------
        # GET IMAGE
        # -------------------------------------------------

        image = request.files.get("image")

        # -------------------------------------------------
        # GET DESCRIPTION
        # -------------------------------------------------

        description = request.form.get(
            "description",
            ""
        ).strip()

        # -------------------------------------------------
        # GET LANGUAGE
        # -------------------------------------------------

        language = request.form.get(
            "language",
            "auto"
        )

        # -------------------------------------------------
        # DETECT LANGUAGE
        # -------------------------------------------------

        if language == "auto":

            language = detect_language(
                description
            )

        # -------------------------------------------------
        # TRANSLATE TO ENGLISH
        # -------------------------------------------------

        english_description = translate_to_english(
            description,
            language
        )

        # -------------------------------------------------
        # SAVE IMAGE
        # -------------------------------------------------

        image_path = None

        if image and image.filename != "":

            filename = (
                str(uuid.uuid4())
                + "_"
                + secure_filename(
                    image.filename
                )
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
        # CREATE COMPLAINT
        # -------------------------------------------------

        complaint_record = Complaint(

            user_id=user_id,

            image_path=image_path,

            description=description,

            english_description=english_description,

            language=language,

            status="Draft"
        )

        # -------------------------------------------------
        # SAVE
        # -------------------------------------------------

        db.session.add(
            complaint_record
        )

        db.session.commit()

        # -------------------------------------------------
        # STORE ACTIVE COMPLAINT
        # -------------------------------------------------

        session["complaint_id"] = (
            complaint_record.id
        )

        # Clear any previous AI result
        session.pop(
            "ai_result",
            None
        )

        # -------------------------------------------------
        # CONTINUE
        # -------------------------------------------------

        return redirect(
            url_for(
                "complaint.applicant"
            )
        )

    return render_template(
        "complaint/upload.html"
    )


# =========================================================
# APPLICANT DETAILS
# =========================================================

@complaint.route(
    "/applicant",
    methods=["GET", "POST"]
)
def applicant():

    complaint_id = session.get(
        "complaint_id"
    )

    if not complaint_id:

        return redirect(
            url_for(
                "complaint.upload"
            )
        )

    complaint_record = Complaint.query.get_or_404(
        complaint_id
    )

    if request.method == "POST":

        complaint_record.applicant_name = request.form.get(
            "applicant_name",
            ""
        ).strip()

        complaint_record.email = request.form.get(
            "email",
            ""
        ).strip()

        complaint_record.phone = request.form.get(
            "phone",
            ""
        ).strip()

        complaint_record.applying_for = request.form.get(
            "applying_for",
            ""
        ).strip()

        db.session.commit()

        return redirect(
            url_for(
                "complaint.address"
            )
        )

    return render_template(
        "complaint/applicant.html",
        complaint=complaint_record
    )


# =========================================================
# ADDRESS
# =========================================================

@complaint.route(
    "/address",
    methods=["GET", "POST"]
)
def address():

    complaint_id = session.get(
        "complaint_id"
    )

    if not complaint_id:

        return redirect(
            url_for(
                "complaint.upload"
            )
        )

    complaint_record = Complaint.query.get_or_404(
        complaint_id
    )

    if request.method == "POST":

        complaint_record.country = request.form.get(
            "country",
            ""
        ).strip()

        complaint_record.state = request.form.get(
            "state",
            ""
        ).strip()

        complaint_record.district = request.form.get(
            "district",
            ""
        ).strip()

        complaint_record.local_body = request.form.get(
            "local_body",
            ""
        ).strip()

        complaint_record.ward = request.form.get(
            "ward",
            ""
        ).strip()

        complaint_record.house_no = request.form.get(
            "house_no",
            ""
        ).strip()

        complaint_record.post_office = request.form.get(
            "post_office",
            ""
        ).strip()

        complaint_record.pincode = request.form.get(
            "pincode",
            ""
        ).strip()

        db.session.commit()

        return redirect(
            url_for(
                "complaint.road_details"
            )
        )

    return render_template(
        "complaint/address.html",
        complaint=complaint_record
    )


# =========================================================
# ROAD DETAILS
# =========================================================

@complaint.route(
    "/road-details",
    methods=["GET", "POST"]
)
def road_details():

    complaint_id = session.get(
        "complaint_id"
    )

    if not complaint_id:

        return redirect(
            url_for(
                "complaint.upload"
            )
        )

    complaint_record = Complaint.query.get_or_404(
        complaint_id
    )

    if request.method == "POST":

        complaint_record.road_type = request.form.get(
            "road_type",
            ""
        ).strip()

        complaint_record.nh_number = request.form.get(
            "nh_number",
            ""
        ).strip()

        complaint_record.highway_state = request.form.get(
            "highway_state",
            ""
        ).strip()

        complaint_record.sh_number = request.form.get(
            "sh_number",
            ""
        ).strip()

        authority, authority_note = recommend_road_authority(
            complaint_record.road_type
        )

        complaint_record.recommended_authority = authority
        complaint_record.authority_note = authority_note

        db.session.commit()

        return redirect(
            url_for(
                "complaint.incident"
            )
        )

    return render_template(
        "complaint/road_details.html",
        complaint=complaint_record
    )


# =========================================================
# INCIDENT DETAILS
# =========================================================

@complaint.route(
    "/incident",
    methods=["GET", "POST"]
)
def incident():

    complaint_id = session.get(
        "complaint_id"
    )

    if not complaint_id:

        return redirect(
            url_for(
                "complaint.upload"
            )
        )

    complaint_record = Complaint.query.get_or_404(
        complaint_id
    )

    if request.method == "POST":

        # -------------------------------------------------
        # INCIDENT DATE
        # -------------------------------------------------

        incident_date = request.form.get(
            "incident_date"
        )

        if incident_date:

            try:

                complaint_record.incident_date = (
                    datetime.strptime(
                        incident_date,
                        "%Y-%m-%d"
                    ).date()
                )

            except ValueError:

                complaint_record.incident_date = None

        # -------------------------------------------------
        # INCIDENT TIME
        # -------------------------------------------------

        incident_time = request.form.get(
            "incident_time"
        )

        if incident_time:

            try:

                complaint_record.incident_time = (
                    datetime.strptime(
                        incident_time,
                        "%H:%M"
                    ).time()
                )

            except ValueError:

                complaint_record.incident_time = None

        # -------------------------------------------------
        # GPS LOCATION
        # -------------------------------------------------

        # GPS LOCATION — SERVER-SIDE VALIDATION
        latitude_raw = request.form.get("latitude", "").strip()
        longitude_raw = request.form.get("longitude", "").strip()

        if not latitude_raw or not longitude_raw:
            db.session.rollback()
            flash(
                "Please select the incident location on the map "
                "or use your current location.",
                "danger"
            )
            return render_template(
                "complaint/incident.html",
                complaint=complaint_record
            )

        try:
            latitude = float(latitude_raw)
            longitude = float(longitude_raw)
        except (ValueError, TypeError):
            db.session.rollback()
            flash(
                "Invalid coordinates. Please select the location again.",
                "danger"
            )
            return render_template(
                "complaint/incident.html",
                complaint=complaint_record
            )

        if (
            not (-90 <= latitude <= 90)
            or not (-180 <= longitude <= 180)
        ):
            db.session.rollback()
            flash(
                "Coordinates are outside the valid range. "
                "Please select the location again.",
                "danger"
            )
            return render_template(
                "complaint/incident.html",
                complaint=complaint_record
            )

        complaint_record.latitude = latitude
        complaint_record.longitude = longitude

        # -------------------------------------------------
        # SAVE
        # -------------------------------------------------

        db.session.commit()

        # -------------------------------------------------
        # GO TO AI ANALYSIS
        # -------------------------------------------------

        return redirect(
            url_for(
                "complaint.analysis"
            )
        )

    return render_template(
        "complaint/incident.html",
        complaint=complaint_record
    )


# =========================================================
# HELPER FUNCTION
# GENERATE AI COMPLAINT
# =========================================================

def generate_ai_complaint(
    complaint_record,
    result
):

    generated_complaint = generate_complaint(

        damage_type=result.get(
            "damage_type"
        ),

        severity=result.get(
            "severity"
        ),

        confidence=result.get(
            "confidence"
        ),

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

    # -----------------------------------------------------
    # SAVE GENERATED COMPLAINT
    # -----------------------------------------------------

    complaint_record.complaint_text = (
        generated_complaint
    )

    db.session.commit()

    # -----------------------------------------------------
    # STORE IN AI RESULT
    # -----------------------------------------------------

    result["generated_complaint"] = (
        generated_complaint
    )

    session["ai_result"] = result

    return result


# =========================================================
# AI ANALYSIS
# =========================================================

@complaint.route(
    "/analysis"
)
def analysis():

    complaint_id = session.get(
        "complaint_id"
    )

    if not complaint_id:

        return redirect(
            url_for(
                "complaint.upload"
            )
        )

    complaint_record = Complaint.query.get_or_404(
        complaint_id
    )

    # -----------------------------------------------------
    # CHECK IMAGE
    # -----------------------------------------------------

    if not complaint_record.image_path:

        session["ai_result"] = {

            "success": False,

            "damage_type": "No image",

            "confidence": 0,

            "severity": "Not analyzed",

            "detection_count": 0,

            "area_ratio": 0,

            "message":
                "No image was uploaded."
        }

        return redirect(
            url_for(
                "complaint.preview"
            )
        )

    # -----------------------------------------------------
    # IMAGE PATH
    # -----------------------------------------------------

    upload_folder = current_app.config[
        "UPLOAD_FOLDER"
    ]

    image_path = os.path.join(
        upload_folder,
        complaint_record.image_path
    )

    # -----------------------------------------------------
    # RUN AI MODEL
    # -----------------------------------------------------

    print(
        "\n========== PAVESENSE AI ANALYSIS =========="
    )

    result = analyze_image(
        image_path
    )

    print(
        "PaveSense AI RESULT:",
        result
    )

    # =====================================================
    # SUCCESSFUL ANALYSIS
    # =====================================================

    if result.get("success"):

        
        # -------------------------------------------------
        # SAVE AI INFORMATION TO DATABASE
        # -------------------------------------------------

        complaint_record.severity = result.get(
            "severity"
        )

        complaint_record.damage_type = result.get(
            "damage_type"
        )

        complaint_record.ai_confidence = result.get(
            "confidence"
        )

        # -------------------------------------------------
        # GROUP DUPLICATE COMPLAINTS
        # -------------------------------------------------

        group_duplicate_complaint(complaint_record)

        db.session.commit()

        # -------------------------------------------------
        # STORE RESULT IN SESSION
        # -------------------------------------------------

        session["ai_result"] = result

        # =================================================
        # LOW-CONFIDENCE RESULT
        # =================================================

        if result.get(
            "requires_confirmation",
            False
        ):

            print(
                "\nLOW-CONFIDENCE RESULT."
            )

            print(
                "User confirmation required."
            )

            # IMPORTANT:
            #
            # Do NOT generate the complaint yet.
            #
            # The user must first confirm that the
            # detected road damage is actually visible.

            return redirect(
                url_for(
                    "complaint.confirm_analysis"
                )
            )

        # =================================================
        # NORMAL / HIGH-CONFIDENCE RESULT
        # =================================================

        generate_ai_complaint(
            complaint_record,
            result
        )

        return redirect(
            url_for(
                "complaint.preview"
            )
        )

    # =====================================================
    # AI ANALYSIS FAILED
    # =====================================================

    session["ai_result"] = {

        "success": False,

        "damage_type":
            "Analysis failed",

        "confidence": 0,

        "severity":
            "Not analyzed",

        "detection_count": 0,

        "area_ratio": 0,

        "message":
            result.get(
                "message",
                "AI analysis failed."
            )
    }

    return redirect(
        url_for(
            "complaint.preview"
        )
    )
    group_duplicate_complaint(complaint_record)

# =========================================================
# LOW-CONFIDENCE ANALYSIS CONFIRMATION
# =========================================================

@complaint.route(
    "/confirm-analysis",
    methods=["GET", "POST"]
)
def confirm_analysis():

    # -----------------------------------------------------
    # GET ACTIVE COMPLAINT
    # -----------------------------------------------------

    complaint_id = session.get(
        "complaint_id"
    )

    if not complaint_id:

        return redirect(
            url_for(
                "complaint.upload"
            )
        )

    complaint_record = Complaint.query.get_or_404(
        complaint_id
    )

    # -----------------------------------------------------
    # GET AI RESULT
    # -----------------------------------------------------

    result = session.get(
        "ai_result"
    )

    # -----------------------------------------------------
    # MAKE SURE AI RESULT EXISTS
    # -----------------------------------------------------

    if not result:

        flash(
            "AI analysis information is not available.",
            "warning"
        )

        return redirect(
            url_for(
                "complaint.analysis"
            )
        )

    # -----------------------------------------------------
    # IMPORTANT SECURITY / FLOW CHECK
    #
    # This page should only be shown when the AI result
    # explicitly requires user confirmation.
    # -----------------------------------------------------

    if not result.get(
        "requires_confirmation",
        False
    ):

        return redirect(
            url_for(
                "complaint.preview"
            )
        )

    # =====================================================
    # GET REQUEST
    # =====================================================

    if request.method == "GET":

        return render_template(

            "complaint/confirm_analysis.html",

            complaint=complaint_record,

            analysis=result
        )

    # =====================================================
    # USER RESPONSE
    # =====================================================

    confirmation = request.form.get(
        "confirm_detection"
    )

    # =====================================================
    # USER CONFIRMED
    # =====================================================

    if confirmation == "yes":

        print(
            "\n=========================================="
        )

        print(
            "USER CONFIRMED LOW-CONFIDENCE DETECTION"
        )

        print(
            "=========================================="
        )

        # -------------------------------------------------
        # MARK USER CONFIRMATION
        # -------------------------------------------------

        result["user_confirmed"] = True

        # -------------------------------------------------
        # SAVE THE CONFIRMED AI DETECTION
        # -------------------------------------------------

        complaint_record.damage_type = result.get(
            "damage_type"
        )

        complaint_record.severity = result.get(
            "severity"
        )

        complaint_record.ai_confidence = result.get(
            "confidence"
        )

        # -------------------------------------------------
        # GROUP ONLY AFTER USER CONFIRMATION
        # -------------------------------------------------

        group_duplicate_complaint(complaint_record)

        db.session.commit()

        # -------------------------------------------------
        # GENERATE COMPLAINT ONLY NOW
        # -------------------------------------------------

        result = generate_ai_complaint(
            complaint_record,
            result
        )

        # -------------------------------------------------
        # KEEP CONFIRMATION FLAG
        # -------------------------------------------------

        result["user_confirmed"] = True

        session["ai_result"] = result

        print(
            "Low-confidence detection confirmed by user."
        )

        print(
            "Complaint generation completed."
        )

        # -------------------------------------------------
        # GO TO PREVIEW
        # -------------------------------------------------

        return redirect(
            url_for(
                "complaint.preview"
            )
        )

    # =====================================================
    # USER REJECTED
    # =====================================================

    if confirmation == "no":

        print(
            "\n=========================================="
        )

        print(
            "USER REJECTED LOW-CONFIDENCE DETECTION"
        )

        print(
            "=========================================="
        )

        # -------------------------------------------------
        # REMOVE OLD AI RESULT
        # -------------------------------------------------

        session.pop(
            "ai_result",
            None
        )

        # -------------------------------------------------
        # CLEAR AI VALUES
        # -------------------------------------------------

        complaint_record.damage_type = None

        complaint_record.severity = None

        complaint_record.ai_confidence = None

        complaint_record.complaint_text = None

        db.session.commit()

        # -------------------------------------------------
        # INFORM USER
        # -------------------------------------------------

        flash(
            "The detected road damage was not confirmed. "
            "Please upload another image.",
            "warning"
        )

        # -------------------------------------------------
        # GO BACK TO UPLOAD
        # -------------------------------------------------

        return redirect(
            url_for(
                "complaint.upload"
            )
        )

    # =====================================================
    # INVALID RESPONSE
    # =====================================================

    flash(
        "Please confirm whether the detected road damage "
        "is visible in the image.",
        "warning"
    )

    return redirect(
        url_for(
            "complaint.confirm_analysis"
        )
    )


# =========================================================
# COMPLAINT PREVIEW
# =========================================================

@complaint.route(
    "/preview"
)
def preview():

    complaint_id = session.get(
        "complaint_id"
    )

    if not complaint_id:

        return redirect(
            url_for(
                "complaint.upload"
            )
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

            "message":
                "AI analysis has not been completed."
        }

    return render_template(

        "complaint/preview.html",

        complaint=complaint_record,

        analysis=analysis_result
    )


# =========================================================
# SAVE AS DRAFT
# =========================================================

@complaint.route(
    "/save-draft",
    methods=["POST"]
)
def save_draft():

    complaint_id = session.get(
        "complaint_id"
    )

    if not complaint_id:

        return redirect(
            url_for(
                "complaint.upload"
            )
        )

    complaint_record = Complaint.query.get_or_404(
        complaint_id
    )

    # -----------------------------------------------------
    # SET STATUS
    # -----------------------------------------------------

    complaint_record.status = "Draft"

    db.session.commit()

    # -----------------------------------------------------
    # SUCCESS PAGE
    # -----------------------------------------------------

    return redirect(
        url_for(
            "complaint.success",
            action="draft"
        )
    )


# =========================================================
# SUBMIT COMPLAINT
# =========================================================


@complaint.route("/submit", methods=["GET", "POST"])
def submit():
    complaint_id = session.get("complaint_id")

    if not complaint_id:
        return redirect(url_for("complaint.upload"))

    complaint_record = Complaint.query.get_or_404(complaint_id)

    if request.method == "GET":
        return render_template(
            "complaint/submit.html",
            complaint=complaint_record
        )

    # Avoid resending the confirmation email if already submitted.
    if complaint_record.status == "Submitted":
        return redirect(
            url_for("complaint.success", action="submitted")
        )

    complaint_record.status = "Submitted"

    try:
        db.session.commit()
    except Exception:
        db.session.rollback()
        current_app.logger.exception("Complaint submission failed.")
        flash(
            "The complaint could not be submitted. Please try again.",
            "danger"
        )
        return redirect(url_for("complaint.submit"))

    # Use the email saved from the road-reporting form,
    # not the logged-in website account.
    email_sent, email_message = send_registration_email(
        recipient=complaint_record.email,
        applicant_name=complaint_record.applicant_name,
        complaint_id=(
            complaint_record.complaint_number
            or complaint_record.id
        )
    )

    if email_sent:
        flash(
            "Your complaint has been submitted. "
            "A confirmation email has been sent to the reporting contact.",
            "success"
        )
    else:
        current_app.logger.warning(
            "Complaint #%s email notification: %s",
            complaint_record.id,
            email_message
        )
        flash(
            "Your complaint has been submitted, but the confirmation "
            "email could not be sent. Please check the reporting email address.",
            "warning"
        )

    return redirect(
        url_for("complaint.success", action="submitted")
    )


# =========================================================
# SUCCESS PAGE
# =========================================================

@complaint.route(
    "/success"
)
def success():

    action = request.args.get(
        "action",
        "submitted"
    )

    complaint_id = session.get(
        "complaint_id"
    )

    complaint_record = None

    if complaint_id:

        complaint_record = Complaint.query.get(
            complaint_id
        )

    return render_template(

        "complaint/success.html",

        action=action,

        complaint=complaint_record
    )