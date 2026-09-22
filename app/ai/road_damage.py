from ultralytics import YOLO
import os


# =========================================================
# MODEL
# =========================================================

MODEL_URL = (
    "https://huggingface.co/vinothvikas1987/"
    "pothole-detection-yolov8/resolve/main/best.pt"
)

_model = None


# =========================================================
# LOAD MODEL
# =========================================================

def get_model():

    global _model

    if _model is None:
        print("Loading PaveSense road damage AI model...")

        _model = YOLO(MODEL_URL)

        print("Road damage AI model loaded successfully.")

    return _model


# =========================================================
# DAMAGE LABELS
# =========================================================

DAMAGE_LABELS = {
    0: "Longitudinal Crack",
    1: "Transverse Crack",
    2: "Alligator Crack",
    3: "Pothole",
    4: "Other"
}


# =========================================================
# SEVERITY
# =========================================================

def calculate_severity(damage_type, confidence, area_ratio):

    damage = damage_type.lower()

    # Potholes are generally more significant
    if "pothole" in damage:

        if area_ratio >= 0.20 or confidence >= 0.85:
            return "HIGH"

        elif area_ratio >= 0.08 or confidence >= 0.60:
            return "MEDIUM"

        else:
            return "LOW"

    # Alligator cracks indicate more extensive damage
    if "alligator" in damage:

        if area_ratio >= 0.15 or confidence >= 0.85:
            return "HIGH"

        elif area_ratio >= 0.05 or confidence >= 0.60:
            return "MEDIUM"

        return "LOW"

    # Normal cracks
    if "crack" in damage:

        if area_ratio >= 0.15 or confidence >= 0.85:
            return "HIGH"

        elif area_ratio >= 0.05 or confidence >= 0.60:
            return "MEDIUM"

        return "LOW"

    # Other
    if confidence >= 0.80:
        return "MEDIUM"

    return "LOW"


# =========================================================
# ANALYZE IMAGE
# =========================================================

def analyze_road_image(image_path):

    if not image_path:
        return {
            "damage_type": "No image",
            "severity": "Not analyzed",
            "confidence": 0,
            "detections": []
        }

    if not os.path.exists(image_path):

        return {
            "damage_type": "Image not found",
            "severity": "Not analyzed",
            "confidence": 0,
            "detections": []
        }

    model = get_model()

    print(
        "Analysing road image:",
        image_path
    )

    results = model.predict(
        source=image_path,
        conf=0.25,
        imgsz=640,
        device="cpu",
        verbose=False
    )

    result = results[0]

    detections = []

    image_width = result.orig_shape[1]
    image_height = result.orig_shape[0]

    image_area = image_width * image_height

    if result.boxes is None or len(result.boxes) == 0:

        return {
            "damage_type": "No road damage detected",
            "severity": "LOW",
            "confidence": 0,
            "detections": []
        }

    for box in result.boxes:

        class_id = int(
            box.cls[0].item()
        )

        confidence = float(
            box.conf[0].item()
        )

        x1, y1, x2, y2 = (
            box.xyxy[0].tolist()
        )

        box_area = max(
            0,
            x2 - x1
        ) * max(
            0,
            y2 - y1
        )

        area_ratio = (
            box_area / image_area
            if image_area > 0
            else 0
        )

        damage_type = DAMAGE_LABELS.get(
            class_id,
            "Road Damage"
        )

        severity = calculate_severity(
            damage_type,
            confidence,
            area_ratio
        )

        detections.append({

            "damage_type": damage_type,

            "confidence": round(
                confidence * 100,
                2
            ),

            "severity": severity,

            "area_ratio": round(
                area_ratio * 100,
                2
            )

        })

    # Highest-confidence detection
    best_detection = max(
        detections,
        key=lambda x: x["confidence"]
    )

    return {

        "damage_type":
            best_detection["damage_type"],

        "severity":
            best_detection["severity"],

        "confidence":
            best_detection["confidence"],

        "detections":
            detections
    }