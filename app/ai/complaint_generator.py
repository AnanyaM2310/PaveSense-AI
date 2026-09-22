import re


def clean_text(value):
    """Safely convert database values into usable text."""
    if value is None:
        return ""

    return str(value).strip()


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
    Generate a factual road-damage complaint.

    Important:
    This function deliberately does not allow a language model
    to invent factual information.
    """

    damage_type = clean_text(damage_type) or "road damage"
    severity = clean_text(severity) or "Not assessed"
    applicant_name = clean_text(applicant_name) or "Applicant"

    state = clean_text(state)
    district = clean_text(district)
    road_type = clean_text(road_type)

    # ---------------------------------------------------------
    # LOCATION
    # ---------------------------------------------------------

    location_parts = []

    if road_type:
        location_parts.append(road_type)

    if district:
        location_parts.append(district)

    if state:
        location_parts.append(state)

    location = ", ".join(location_parts)

    if not location:
        location = "the reported location"

    # ---------------------------------------------------------
    # GPS
    # ---------------------------------------------------------

    gps_text = ""

    if latitude is not None and longitude is not None:
        gps_text = (
            f"Latitude: {latitude}\n"
            f"Longitude: {longitude}"
        )

    # ---------------------------------------------------------
    # CONFIDENCE
    # ---------------------------------------------------------

    confidence_text = ""

    if confidence is not None:
        try:
            confidence_value = float(confidence)
            confidence_text = (
                f"with an AI confidence score of "
                f"{confidence_value:.2f}%"
            )
        except (ValueError, TypeError):
            confidence_text = ""

    # ---------------------------------------------------------
    # INCIDENT INFORMATION
    # ---------------------------------------------------------

    incident_text = ""

    if incident_date:
        incident_text = (
            f"The incident date provided by the applicant is "
            f"{incident_date}"
        )

        if incident_time:
            incident_text += f" at {incident_time}"

        incident_text += "."

    # ---------------------------------------------------------
    # APPLICANT DESCRIPTION
    # ---------------------------------------------------------

    description_text = ""

    if description:
        description_text = clean_text(description)

    # ---------------------------------------------------------
    # COMPLAINT
    # ---------------------------------------------------------

    complaint_parts = []

    complaint_parts.append(
        f"Subject: Request for Inspection and Repair of "
        f"{damage_type}"
    )

    complaint_parts.append(
        "Dear Sir/Madam,"
    )

    complaint_parts.append(
        f"I am writing to report {damage_type.lower()} "
        f"detected by PaveSense AI on {location}."
    )

    severity_sentence = (
        f"The AI analysis identified the damage as "
        f"{damage_type.lower()} with a severity level of "
        f"{severity.lower()}"
    )

    if confidence_text:
        severity_sentence += f" and {confidence_text}"

    severity_sentence += "."

    complaint_parts.append(
        severity_sentence
    )

    if gps_text:
        complaint_parts.append(
            "The available GPS location information is:\n"
            + gps_text
        )

    if incident_text:
        complaint_parts.append(
            incident_text
        )

    if description_text:
        complaint_parts.append(
            f"The applicant's description is: "
            f"{description_text}"
        )

    complaint_parts.append(
        "I kindly request the concerned road authority "
        "to inspect the reported location and take the "
        "necessary action for repair of the damaged road "
        "section."
    )

    complaint_parts.append(
        "Timely inspection and necessary maintenance "
        "will help address the reported road damage."
    )

    complaint_parts.append(
        "Regards,"
    )

    complaint_parts.append(
        applicant_name
    )

    return "\n\n".join(complaint_parts)