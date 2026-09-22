import os

from ultralytics import YOLO


# =========================================================
# MODEL CONFIGURATION
# =========================================================

MODEL_PATH = os.path.join(
    os.path.dirname(
        os.path.dirname(
            os.path.dirname(__file__)
        )
    ),
    "weights",
    "yolo12s_RDD2022_best.pt"
)

# The model will be downloaded automatically by Ultralytics
# the first time it is used.


# =========================================================
# DAMAGE LABELS
# =========================================================

DAMAGE_LABELS = {
    "d00": "Longitudinal Crack",
    "d10": "Transverse Crack",
    "d20": "Alligator Crack",
    "d40": "Pothole",
    "repair": "Repair"
}


# =========================================================
# LOAD MODEL
# =========================================================

_model = None


def get_model():

    global _model

    if _model is None:

        print("Loading PaveSense road damage model...")

        _model = YOLO(
            MODEL_PATH
        )

        print("PaveSense road damage model loaded.")

    return _model

# =========================================================
# SEVERITY CALCULATION
# =========================================================

def calculate_severity(
    damage_type,
    confidence,
    area_ratio,
    detection_count
):

    """
    Calculates an initial severity estimate.

    This is a rule-based severity layer on top of
    the object detector.

    It is NOT a medically/safety-certified severity
    prediction.
    """

    damage_type_lower = damage_type.lower()

    # -----------------------------------------------------
    # HIGH SEVERITY
    # -----------------------------------------------------

    if (

        area_ratio >= 0.20

        or detection_count >= 4

        or (
            damage_type_lower == "pothole"
            and area_ratio >= 0.10
        )

        or (
            damage_type_lower == "alligator crack"
            and area_ratio >= 0.12
        )

    ):

        return "HIGH"


    # -----------------------------------------------------
    # MEDIUM SEVERITY
    # -----------------------------------------------------

    if (

        area_ratio >= 0.05

        or detection_count >= 2

        or confidence >= 0.70

    ):

        return "MEDIUM"


    # -----------------------------------------------------
    # LOW SEVERITY
    # -----------------------------------------------------

    return "LOW"


# =========================================================
# IMAGE ANALYSIS
# =========================================================

def analyze_image(image_path):

    """
    Runs road-damage detection on one uploaded image.

    Returns a dictionary containing:

        damage_type
        confidence
        severity
        detection_count
        area_ratio
    """

    if not image_path:

        return {
            "success": False,
            "damage_type": None,
            "confidence": None,
            "severity": None,
            "detection_count": 0,
            "area_ratio": 0,
            "message": "No image was provided."
        }


    if not os.path.exists(image_path):

        return {
            "success": False,
            "damage_type": None,
            "confidence": None,
            "severity": None,
            "detection_count": 0,
            "area_ratio": 0,
            "message": "Image file was not found."
        }


    try:

        model = get_model()


        # -------------------------------------------------
        # RUN DETECTION
        # -------------------------------------------------

        results = model.predict(
            source=image_path,
            conf=0.40,
            imgsz=640,
            device="cpu",
            verbose=False
        )


        if not results:

            return {
                "success": False,
                "damage_type": None,
                "confidence": None,
                "severity": None,
                "detection_count": 0,
                "area_ratio": 0,
                "message": "No analysis result was returned."
            }


        result = results[0]


        # -------------------------------------------------
        # IMAGE SIZE
        # -------------------------------------------------

        image_height = result.orig_shape[0]
        image_width = result.orig_shape[1]

        image_area = (
            image_width * image_height
        )


        # -------------------------------------------------
        # NO DAMAGE DETECTED
        # -------------------------------------------------

        if result.boxes is None or len(result.boxes) == 0:

            return {
                "success": True,
                "damage_type": "No road damage detected",
                "confidence": 0,
                "severity": "LOW",
                "detection_count": 0,
                "area_ratio": 0,
                "message": (
                    "The AI model did not detect "
                    "a supported road-damage category."
                )
            }


        # -------------------------------------------------
        # PROCESS DETECTIONS
        # -------------------------------------------------

        detections = []


        for box in result.boxes:

            class_id = int(
                box.cls[0]
            )

            confidence = float(
                box.conf[0]
            )

            coordinates = box.xyxy[0].tolist()

            x1, y1, x2, y2 = coordinates


            box_width = max(
                0,
                x2 - x1
            )

            box_height = max(
                0,
                y2 - y1
            )

            box_area = (
                box_width * box_height
            )


            area_ratio = (
                box_area / image_area
                if image_area > 0
                else 0
            )


            raw_name = model.names.get(
                class_id,
                "Unknown"
            )


            damage_name = DAMAGE_LABELS.get(
                raw_name.lower(),
                raw_name
            )


            detections.append({

                "damage_type": damage_name,

                "confidence": round(
                    confidence * 100,
                    2
                ),

                "area_ratio": round(
                    area_ratio * 100,
                    2
                )

            })


        # -------------------------------------------------
        # SELECT PRIMARY DAMAGE
        # -------------------------------------------------

        detections.sort(
            key=lambda x: x["confidence"],
            reverse=True
        )


        primary = detections[0]

        damage_type = primary[
            "damage_type"
        ]

        # Convert percentage values back to 0–1
        # for severity calculation
        confidence = primary[
            "confidence"
        ] / 100

        area_ratio = primary[
            "area_ratio"
        ] / 100

        detection_count = len(
            detections
        )


        # -------------------------------------------------
        # CALCULATE SEVERITY
        # -------------------------------------------------

        severity = calculate_severity(

            damage_type,

            confidence,

            area_ratio,

            detection_count

        )


        return {

            "success": True,

            "damage_type": damage_type,

            "confidence": round(
                confidence * 100,
                2
            ),

            "severity": severity,

            "detection_count": detection_count,

            "area_ratio": round(
                area_ratio * 100,
                2
            ),

            "detections": detections,

            "message": (
                "Road damage successfully analyzed."
            )

        }


    except Exception as e:

        print(
            "AI IMAGE ANALYSIS ERROR:",
            e
        )


        return {

            "success": False,

            "damage_type": None,

            "confidence": None,

            "severity": None,

            "detection_count": 0,

            "area_ratio": 0,

            "message": str(e)

        }