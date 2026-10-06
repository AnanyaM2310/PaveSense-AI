def clean_text(value):
    """Safely convert database values into usable text."""
    if value is None:
        return ""

    return str(value).strip()


def format_confidence(confidence):
    """
    Format AI confidence safely.
    """

    if confidence is None:
        return ""

    try:
        confidence_value = float(confidence)

        return (
            f"with an AI confidence score of "
            f"{confidence_value:.2f}%"
        )

    except (ValueError, TypeError):

        return ""


def generate_location(
    country=None,
    state=None,
    district=None,
    local_body=None,
    ward=None,
    house_no=None,
    post_office=None,
    pincode=None,
    road_type=None,
    latitude=None,
    longitude=None
):
    """
    Build location information using ONLY values supplied
    by the complaint form.

    No locations are invented.
    """

    country = clean_text(country)
    state = clean_text(state)
    district = clean_text(district)
    local_body = clean_text(local_body)
    ward = clean_text(ward)
    house_no = clean_text(house_no)
    post_office = clean_text(post_office)
    pincode = clean_text(pincode)
    road_type = clean_text(road_type)

    location_parts = []

    if road_type:
        location_parts.append(road_type)

    if house_no:
        location_parts.append(
            f"House No. {house_no}"
        )

    if ward:
        location_parts.append(
            f"Ward {ward}"
        )

    if local_body:
        location_parts.append(
            local_body
        )

    if post_office:
        location_parts.append(
            f"Post Office: {post_office}"
        )

    if pincode:
        location_parts.append(
            f"Pincode: {pincode}"
        )

    if district:
        location_parts.append(
            district
        )

    if state:
        location_parts.append(
            state
        )

    if country:
        location_parts.append(
            country
        )

    return ", ".join(location_parts)


def generate_gps_text(latitude, longitude):
    """
    Generate GPS information only when both coordinates
    are available.
    """

    if latitude is None or longitude is None:
        return ""

    return (
        "The available GPS location information is:\n"
        f"Latitude: {latitude}\n"
        f"Longitude: {longitude}"
    )


def generate_incident_text(
    incident_date=None,
    incident_time=None
):
    """
    Include date/time only when actually supplied.
    """

    if not incident_date:
        return ""

    date_text = clean_text(
        incident_date
    )

    time_text = ""

    if incident_time:
        time_text = (
            f" at {clean_text(incident_time)}"
        )

    return (
        f"The date provided for the road damage is "
        f"{date_text}{time_text}."
    )


def generate_complaint(
    damage_type,
    severity,
    confidence,
    applicant_name,
    country=None,
    state=None,
    district=None,
    local_body=None,
    ward=None,
    house_no=None,
    post_office=None,
    pincode=None,
    road_type=None,
    nh_number=None,
    highway_state=None,
    sh_number=None,
    latitude=None,
    longitude=None,
    incident_date=None,
    incident_time=None,
    description=None
):
    """
    Generate a factual government-style road damage
    complaint.

    IMPORTANT:

    This function does NOT invent information.

    It only uses information supplied by the user,
    database, GPS system, or AI analysis.
    """

    # =====================================================
    # BASIC VALUES
    # =====================================================

    damage_type = (
        clean_text(damage_type)
        or "road damage"
    )

    severity = (
        clean_text(severity)
        or "Not assessed"
    )

    applicant_name = (
        clean_text(applicant_name)
        or "Applicant"
    )

    road_type = clean_text(
        road_type
    )

    # =====================================================
    # LOCATION
    # =====================================================

    location = generate_location(

        country=country,

        state=state,

        district=district,

        local_body=local_body,

        ward=ward,

        house_no=house_no,

        post_office=post_office,

        pincode=pincode,

        road_type=road_type,

        latitude=latitude,

        longitude=longitude

    )

    if not location:

        location = "the reported location"

    # =====================================================
    # GPS
    # =====================================================

    gps_text = generate_gps_text(

        latitude,

        longitude

    )

    # =====================================================
    # CONFIDENCE
    # =====================================================

    confidence_text = format_confidence(
        confidence
    )

    # =====================================================
    # DATE / TIME
    # =====================================================

    incident_text = generate_incident_text(

        incident_date,

        incident_time

    )

    # =====================================================
    # DESCRIPTION
    # =====================================================

    description = clean_text(
        description
    )

    # =====================================================
    # COMPLAINT
    # =====================================================

    complaint_parts = []

    # -----------------------------------------------------
    # SUBJECT
    # -----------------------------------------------------

    complaint_parts.append(

        f"Subject: Request for Inspection and Repair "
        f"of {damage_type}"

    )

    # -----------------------------------------------------
    # GREETING
    # -----------------------------------------------------

    complaint_parts.append(
        "Dear Sir/Madam,"
    )

    # -----------------------------------------------------
    # INTRODUCTION
    # -----------------------------------------------------

    complaint_parts.append(

        f"I am writing to report {damage_type.lower()} "
        f"detected by PaveSense AI at {location}."

    )

    # -----------------------------------------------------
    # AI ANALYSIS
    # -----------------------------------------------------

    ai_sentence = (

        f"The AI analysis identified the damage as "
        f"{damage_type.lower()} with a severity level "
        f"of {severity.lower()}"

    )

    if confidence_text:

        ai_sentence += (
            f" and {confidence_text}"
        )

    ai_sentence += "."

    complaint_parts.append(
        ai_sentence
    )

    # -----------------------------------------------------
    # GPS
    # -----------------------------------------------------

    if gps_text:

        complaint_parts.append(
            gps_text
        )

    # -----------------------------------------------------
    # DATE / TIME
    # -----------------------------------------------------

    if incident_text:

        complaint_parts.append(
            incident_text
        )

    # -----------------------------------------------------
    # USER DESCRIPTION
    # -----------------------------------------------------

    if description:

        complaint_parts.append(

            f"The applicant provided the following "
            f"description: {description}"

        )

    # -----------------------------------------------------
    # REQUEST
    # -----------------------------------------------------

    complaint_parts.append(

        "I kindly request the concerned road authority "
        "to inspect the reported location and take the "
        "necessary action for repair of the damaged road "
        "section."

    )

    # -----------------------------------------------------
    # CLOSING
    # -----------------------------------------------------

    complaint_parts.append(
        "Regards,"
    )

    complaint_parts.append(
        applicant_name
    )

    # =====================================================
    # FINAL LETTER
    # =====================================================

    return "\n\n".join(
        complaint_parts
    )