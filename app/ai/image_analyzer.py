import os
from ultralytics import YOLO


# ============================================================
# PAVESENSE AI - IMAGE ANALYZER
# ============================================================
#
# Primary model:
#   weights/best.pt
#
# Fallback model:
#   weights/yolo12s_RDD2022_best.pt
#
# The primary model is used first.
#
# If:
#   1. No damage is detected, OR
#   2. Primary model predicts "Other"
#
# then the fallback RDD2022 model is used.
#
# Low-confidence detections are NOT automatically treated
# as highly severe. They require user confirmation.
# ============================================================


# ------------------------------------------------------------
# PROJECT ROOT
# ------------------------------------------------------------

BASE_DIR = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "..", "..")
)


# ------------------------------------------------------------
# MODEL PATHS
# ------------------------------------------------------------

PRIMARY_MODEL_PATH = os.path.join(
    BASE_DIR,
    "weights",
    "best.pt"
)

FALLBACK_MODEL_PATH = os.path.join(
    BASE_DIR,
    "weights",
    "yolo12s_RDD2022_best.pt"
)


# ------------------------------------------------------------
# CONFIDENCE SETTINGS
# ------------------------------------------------------------

# Normal detection threshold
PRIMARY_CONFIDENCE = 0.40

# Lower threshold for fallback detection
FALLBACK_CONFIDENCE = 0.10

# Anything below this confidence is considered uncertain
LOW_CONFIDENCE_THRESHOLD = 0.30


# ------------------------------------------------------------
# MODEL CACHE
# ------------------------------------------------------------

_primary_model = None
_fallback_model = None


# ============================================================
# PRIMARY MODEL LOADER
# ============================================================

def load_primary_model():
    """
    Load the main PaveSense road-damage model.

    The model is loaded only once and then reused.
    """

    global _primary_model

    if _primary_model is None:

        print("Loading PaveSense road damage model...")

        if not os.path.exists(PRIMARY_MODEL_PATH):
            raise FileNotFoundError(
                f"Primary model not found:\n{PRIMARY_MODEL_PATH}"
            )

        _primary_model = YOLO(PRIMARY_MODEL_PATH)

        print("PaveSense road damage model loaded.")

    return _primary_model


# ============================================================
# FALLBACK MODEL LOADER
# ============================================================

def load_fallback_model():
    """
    Load the RDD2022 fallback model.

    The fallback model is used when:
        - primary model detects nothing
        - primary model predicts 'Other'
    """

    global _fallback_model

    if _fallback_model is None:

        print("Loading fallback road damage model...")

        if not os.path.exists(FALLBACK_MODEL_PATH):
            raise FileNotFoundError(
                f"Fallback model not found:\n{FALLBACK_MODEL_PATH}"
            )

        _fallback_model = YOLO(FALLBACK_MODEL_PATH)

        print("Fallback road damage model loaded.")

    return _fallback_model


# ============================================================
# CLASS NAME NORMALIZATION
# ============================================================

def normalize_damage_type(class_name):
    """
    Convert model-specific class names into PaveSense names.

    Primary model:
        Longitudinal Crack
        Transverse Crack
        Alligator Crack
        Pothole
        Other

    RDD2022 fallback model:
        D00
        D10
        D20
        D40
        Repair
    """

    if class_name is None:
        return "Other"

    name = str(class_name).strip()

    # --------------------------------------------------------
    # RDD2022 CLASS MAPPING
    # --------------------------------------------------------

    fallback_mapping = {
        "D00": "Longitudinal Crack",
        "D10": "Transverse Crack",
        "D20": "Alligator Crack",
        "D40": "Pothole",
        "Repair": "Other",
    }

    if name in fallback_mapping:
        return fallback_mapping[name]

    # --------------------------------------------------------
    # NORMALIZE COMMON PRIMARY MODEL NAMES
    # --------------------------------------------------------

    normalized = name.lower()

    if normalized in [
        "longitudinal crack",
        "longitudinal_crack",
        "longitudinal",
    ]:
        return "Longitudinal Crack"

    if normalized in [
        "transverse crack",
        "transverse_crack",
        "transverse",
    ]:
        return "Transverse Crack"

    if normalized in [
        "alligator crack",
        "alligator_crack",
        "alligator",
    ]:
        return "Alligator Crack"

    if normalized in [
        "pothole",
        "potholes",
        "pot hole",
    ]:
        return "Pothole"

    if normalized in [
        "other",
        "repair",
    ]:
        return "Other"

    # If the model gives something unknown,
    # don't expose the raw model class to the application.
    return "Other"


# ============================================================
# SEVERITY CALCULATION
# ============================================================

def calculate_severity(confidence, area_ratio):
    """
    Estimate road-damage severity.

    IMPORTANT:
    Confidence is checked FIRST.

    A very low-confidence AI prediction must not automatically
    become HIGH severity simply because of another calculation.

    Rules:

        Confidence < 30%
            -> LOW

        Confidence >= 30% and area < 5%
            -> LOW

        Confidence >= 30% and area 5% to <15%
            -> MEDIUM

        Confidence >= 30% and area >=15%
            -> HIGH
    """

    # Convert NumPy values safely into normal Python floats.
    try:
        confidence = float(confidence)
    except (TypeError, ValueError):
        confidence = 0.0

    try:
        area_ratio = float(area_ratio)
    except (TypeError, ValueError):
        area_ratio = 0.0

    # --------------------------------------------------------
    # LOW CONFIDENCE ALWAYS MEANS LOW INITIAL SEVERITY
    # --------------------------------------------------------

    if confidence < (LOW_CONFIDENCE_THRESHOLD * 100):
        return "LOW"

    # --------------------------------------------------------
    # HIGH-CONFIDENCE DETECTION
    # --------------------------------------------------------

    if area_ratio >= 15.0:
        return "HIGH"

    if area_ratio >= 5.0:
        return "MEDIUM"

    return "LOW"


# ============================================================
# BOUNDING BOX AREA CALCULATION
# ============================================================

def calculate_bbox_area_ratio(box, image_width, image_height):
    """
    Calculate how much of the image is occupied by the
    detected bounding box.

    Returns percentage.
    """

    try:

        x1, y1, x2, y2 = box.xyxy[0].tolist()

        box_width = max(0.0, float(x2) - float(x1))
        box_height = max(0.0, float(y2) - float(y1))

        bbox_area = box_width * box_height

        image_area = float(image_width * image_height)

        if image_area <= 0:
            return 0.0

        ratio = (bbox_area / image_area) * 100.0

        return round(float(ratio), 2)

    except Exception:
        return 0.0


# ============================================================
# PROCESS YOLO RESULT
# ============================================================

def process_result(
    result,
    model,
    image_width,
    image_height
):
    """
    Convert an Ultralytics YOLO result into a PaveSense
    detection list.

    Returns:

        {
            "detections": [...],
            "best_detection": {...} or None
        }
    """

    detections = []

    # No boxes
    if result is None:
        return {
            "detections": [],
            "best_detection": None
        }

    if result.boxes is None:
        return {
            "detections": [],
            "best_detection": None
        }

    if len(result.boxes) == 0:
        return {
            "detections": [],
            "best_detection": None
        }

    # --------------------------------------------------------
    # PROCESS EVERY DETECTION
    # --------------------------------------------------------

    for box in result.boxes:

        # -----------------------------
        # CLASS ID
        # -----------------------------

        try:
            class_id = int(box.cls[0].item())
        except Exception:
            continue

        # -----------------------------
        # CONFIDENCE
        # -----------------------------

        try:
            confidence = float(box.conf[0].item())
        except Exception:
            confidence = 0.0

        confidence_percent = round(
            confidence * 100.0,
            2
        )

        # -----------------------------
        # MODEL CLASS NAME
        # -----------------------------

        try:
            raw_class_name = model.names[class_id]
        except Exception:
            raw_class_name = "Other"

        # -----------------------------
        # PAVESENSE DAMAGE TYPE
        # -----------------------------

        damage_type = normalize_damage_type(
            raw_class_name
        )

        # -----------------------------
        # BOUNDING BOX AREA
        # -----------------------------

        bbox_area_ratio = calculate_bbox_area_ratio(
            box,
            image_width,
            image_height
        )

        # For this project, detected area is represented
        # by the bounding-box area.
        area_ratio = bbox_area_ratio

        detection = {
            "damage_type": damage_type,
            "confidence": confidence_percent,
            "area_ratio": area_ratio,
            "bbox_area_ratio": bbox_area_ratio
        }

        detections.append(detection)

    # --------------------------------------------------------
    # NO VALID DETECTIONS
    # --------------------------------------------------------

    if not detections:

        return {
            "detections": [],
            "best_detection": None
        }

    # --------------------------------------------------------
    # BEST DETECTION
    #
    # Select the detection with the highest confidence.
    # --------------------------------------------------------

    best_detection = max(
        detections,
        key=lambda item: item["confidence"]
    )

    return {
        "detections": detections,
        "best_detection": best_detection
    }


# ============================================================
# RUN MODEL
# ============================================================

def run_model(
    model,
    image_path,
    confidence_threshold
):
    """
    Run a YOLO model and return processed detection data.
    """

    results = model.predict(
        source=image_path,
        conf=confidence_threshold,
        verbose=False
    )

    if not results:
        return {
            "detections": [],
            "best_detection": None
        }

    result = results[0]

    # --------------------------------------------------------
    # GET IMAGE SIZE FROM YOLO RESULT
    # --------------------------------------------------------

    image_height = 0
    image_width = 0

    try:

        if result.orig_img is not None:

            image_height = int(
                result.orig_img.shape[0]
            )

            image_width = int(
                result.orig_img.shape[1]
            )

    except Exception:
        pass

    # --------------------------------------------------------
    # SAFETY FALLBACK
    # --------------------------------------------------------

    if image_width <= 0:
        image_width = 1

    if image_height <= 0:
        image_height = 1

    return process_result(
        result,
        model,
        image_width,
        image_height
    )


# ============================================================
# FALLBACK ANALYSIS
# ============================================================

def run_fallback_analysis(image_path):
    """
    Run the RDD2022 fallback model.

    The fallback model is useful when the primary model
    produces 'Other' or no detection.
    """

    print("Running fallback analysis...")

    fallback_model = load_fallback_model()

    fallback_result = run_model(
        fallback_model,
        image_path,
        FALLBACK_CONFIDENCE
    )

    detections = fallback_result["detections"]
    best_detection = fallback_result["best_detection"]

    # --------------------------------------------------------
    # NO FALLBACK DETECTION
    # --------------------------------------------------------

    if best_detection is None:

        print("Fallback model also found no road damage.")

        return None

    # --------------------------------------------------------
    # BEST FALLBACK DETECTION
    # --------------------------------------------------------

    damage_type = best_detection["damage_type"]

    confidence = float(
        best_detection["confidence"]
    )

    area_ratio = float(
        best_detection["area_ratio"]
    )

    bbox_area_ratio = float(
        best_detection["bbox_area_ratio"]
    )

    detection_count = len(detections)

    # --------------------------------------------------------
    # SEVERITY
    # --------------------------------------------------------

    severity = calculate_severity(
        confidence,
        area_ratio
    )

    # --------------------------------------------------------
    # LOW CONFIDENCE
    # --------------------------------------------------------

    low_confidence = (
        confidence < (LOW_CONFIDENCE_THRESHOLD * 100)
    )

    requires_confirmation = low_confidence

    # --------------------------------------------------------
    # PRINT RESULT
    # --------------------------------------------------------

    print()
    print("========== FALLBACK DETECTION ==========")
    print(
        f"Possible Damage Type: {damage_type}"
    )
    print(
        f"YOLO Confidence: {confidence} %"
    )
    print(
        f"Area Ratio: {area_ratio} %"
    )
    print(
        f"Bounding Box Ratio: {bbox_area_ratio} %"
    )
    print(
        f"Detection Count: {detection_count}"
    )
    print(
        f"Initial Severity: {severity}"
    )
    print(
        "Detection Source: FALLBACK"
    )

    if requires_confirmation:

        print(
            "User confirmation required."
        )

    else:

        print(
            "Fallback confidence is sufficient."
        )

    print(
        "========================================"
    )

    return {
        "success": True,
        "damage_type": damage_type,
        "confidence": confidence,
        "severity": severity,
        "detection_count": detection_count,
        "area_ratio": area_ratio,
        "bbox_area_ratio": bbox_area_ratio,
        "detections": detections,
        "low_confidence": low_confidence,
        "requires_confirmation": requires_confirmation,
        "detection_source": "fallback",
        "message": (
            "A possible road-damage issue was detected "
            "with low AI confidence. Please verify the "
            "image before continuing with the complaint."
            if requires_confirmation
            else
            "Road damage successfully analyzed."
        )
    }


# ============================================================
# MAIN ANALYSIS FUNCTION
# ============================================================

def analyze_image(image_path):
    """
    Main PaveSense image-analysis function.

    Workflow:

        1. Validate image.
        2. Run primary model.
        3. If primary detects a useful damage type,
           use primary result.
        4. If primary says 'Other', run fallback.
        5. If primary finds nothing, run fallback.
        6. Calculate severity.
        7. Return structured result.
    """

    print()
    print("========== PAVESENSE AI ANALYSIS ==========")
    print("Running normal YOLO analysis...")

    # --------------------------------------------------------
    # IMAGE VALIDATION
    # --------------------------------------------------------

    if not image_path:
        return {
            "success": False,
            "message": "No image path was provided."
        }

    if not os.path.exists(image_path):

        return {
            "success": False,
            "message": (
                f"Image not found: {image_path}"
            )
        }

    try:

        # ====================================================
        # PRIMARY MODEL
        # ====================================================

        primary_model = load_primary_model()

        primary_result = run_model(
            primary_model,
            image_path,
            PRIMARY_CONFIDENCE
        )

        primary_detections = (
            primary_result["detections"]
        )

        primary_best = (
            primary_result["best_detection"]
        )

        # ====================================================
        # PRIMARY MODEL FOUND NOTHING
        # ====================================================

        if primary_best is None:

            print(
                "No damage detected at normal confidence threshold (0.4)."
            )

            print(
                "Running fallback analysis..."
            )

            fallback_result = run_fallback_analysis(
                image_path
            )

            # ------------------------------------------------
            # FALLBACK ALSO FOUND NOTHING
            # ------------------------------------------------

            if fallback_result is None:

                print(
                    "No road damage detected."
                )

                print(
                    "============================================"
                )

                return {
                    "success": False,
                    "damage_type": None,
                    "confidence": 0.0,
                    "severity": "LOW",
                    "detection_count": 0,
                    "area_ratio": 0.0,
                    "bbox_area_ratio": 0.0,
                    "detections": [],
                    "low_confidence": False,
                    "requires_confirmation": False,
                    "detection_source": "none",
                    "message": (
                        "No road damage was detected "
                        "in the uploaded image."
                    )
                }

            print(
                "============================================"
            )

            return fallback_result

        # ====================================================
        # PRIMARY MODEL FOUND SOMETHING
        # ====================================================

        primary_damage_type = (
            primary_best["damage_type"]
        )

        # ====================================================
        # PRIMARY MODEL SAYS OTHER
        #
        # This is the important part for your pothole
        # images.
        # ====================================================

        if primary_damage_type == "Other":

            print(
                "Primary model classified the damage as OTHER."
            )

            print(
                "Running fallback model to verify the damage type..."
            )

            fallback_result = run_fallback_analysis(
                image_path
            )

            # ------------------------------------------------
            # FALLBACK FOUND A MORE USEFUL CLASS
            # ------------------------------------------------

            if (
                fallback_result is not None
                and fallback_result["damage_type"] != "Other"
            ):

                print(
                    "Fallback classification is more useful "
                    f"than PRIMARY = Other."
                )

                print(
                    "============================================"
                )

                return fallback_result

            # ------------------------------------------------
            # FALLBACK DID NOT GIVE A BETTER RESULT
            # ------------------------------------------------

            print(
                "Fallback did not provide a better "
                "damage classification."
            )

        # ====================================================
        # USE PRIMARY MODEL RESULT
        # ====================================================

        damage_type = primary_best["damage_type"]

        confidence = float(
            primary_best["confidence"]
        )

        area_ratio = float(
            primary_best["area_ratio"]
        )

        bbox_area_ratio = float(
            primary_best["bbox_area_ratio"]
        )

        detection_count = len(
            primary_detections
        )

        # ----------------------------------------------------
        # SEVERITY
        # ----------------------------------------------------

        severity = calculate_severity(
            confidence,
            area_ratio
        )

        # ----------------------------------------------------
        # PRIMARY DETECTIONS ARE NORMALLY HIGH CONFIDENCE
        # because the primary threshold is 40%.
        # ----------------------------------------------------

        low_confidence = (
            confidence < (LOW_CONFIDENCE_THRESHOLD * 100)
        )

        requires_confirmation = low_confidence

        # ----------------------------------------------------
        # PRINT RESULT
        # ----------------------------------------------------

        print(
            f"Damage Type: {damage_type}"
        )

        print(
            f"YOLO Confidence: {confidence} %"
        )

        print(
            f"Area Ratio: {area_ratio} %"
        )

        print(
            f"Bounding Box Ratio: {bbox_area_ratio} %"
        )

        print(
            f"Detection Count: {detection_count}"
        )

        print(
            f"Severity: {severity}"
        )

        print(
            "Detection Source: NORMAL"
        )

        print(
            "============================================"
        )

        return {
            "success": True,
            "damage_type": damage_type,
            "confidence": confidence,
            "severity": severity,
            "detection_count": detection_count,
            "area_ratio": area_ratio,
            "bbox_area_ratio": bbox_area_ratio,
            "detections": primary_detections,
            "low_confidence": low_confidence,
            "requires_confirmation": requires_confirmation,
            "detection_source": "normal",
            "message": (
                "A possible road-damage issue was detected "
                "with low AI confidence. Please verify the "
                "image before continuing with the complaint."
                if requires_confirmation
                else
                "Road damage successfully analyzed."
            )
        }

    # ========================================================
    # ERROR HANDLING
    # ========================================================

    except Exception as e:

        print()
        print("========== PAVESENSE AI ERROR ==========")
        print(
            f"Error while analyzing image: {e}"
        )
        print(
            "========================================"
        )

        return {
            "success": False,
            "damage_type": None,
            "confidence": 0.0,
            "severity": "LOW",
            "detection_count": 0,
            "area_ratio": 0.0,
            "bbox_area_ratio": 0.0,
            "detections": [],
            "low_confidence": False,
            "requires_confirmation": False,
            "detection_source": "error",
            "message": (
                "An error occurred while analyzing "
                f"the image: {str(e)}"
            )
        }


# ============================================================
# OPTIONAL DIRECT TEST
# ============================================================

if __name__ == "__main__":

    print()
    print("PaveSense Image Analyzer")
    print("-------------------------")
    print()
    print(
        "This module is normally called through "
        "analyze_image(image_path)."
    )