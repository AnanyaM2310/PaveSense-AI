from ultralytics import YOLO
import os


# =========================================================
# LOAD SECOND MODEL
# =========================================================

MODEL_PATH = os.path.join(
    "weights",
    "best.pt"
)

print("\nLoading second road-damage model...")

model = YOLO(MODEL_PATH)

print("Model loaded successfully.")
print("Classes:", model.names)


# =========================================================
# TEST IMAGES
# =========================================================

images = [
    "pothhole.jpg",
    "pothole.jpg",
    "pothole1.jpg",
    "pothole2.jpg",
    "pothole3.jpg"
]


# =========================================================
# RUN TEST
# =========================================================

print("\n")
print("=" * 65)
print("       PAVESENSE AI - SECOND MODEL TEST")
print("=" * 65)


for image_path in images:

    print("\n")
    print("-" * 65)
    print("IMAGE:", image_path)
    print("-" * 65)


    if not os.path.exists(image_path):

        print("Image file not found.")

        continue


    try:

        results = model.predict(
            source=image_path,
            conf=0.25,
            imgsz=640,
            device="cpu",
            verbose=False
        )


        result = results[0]


        # -------------------------------------------------
        # NO DETECTIONS
        # -------------------------------------------------

        if result.boxes is None or len(result.boxes) == 0:

            print("No road damage detected.")

            continue


        # -------------------------------------------------
        # DETECTIONS
        # -------------------------------------------------

        detections = []


        for box in result.boxes:

            class_id = int(
                box.cls[0].item()
            )

            confidence = float(
                box.conf[0].item()
            )

            class_name = model.names.get(
                class_id,
                "Unknown"
            )


            x1, y1, x2, y2 = (
                box.xyxy[0].tolist()
            )


            image_width = result.orig_shape[1]
            image_height = result.orig_shape[0]

            image_area = (
                image_width * image_height
            )


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


            detections.append({

                "damage_type": class_name,

                "confidence": confidence * 100,

                "area_ratio": area_ratio * 100

            })


        # -------------------------------------------------
        # SORT BY CONFIDENCE
        # -------------------------------------------------

        detections.sort(
            key=lambda x: x["confidence"],
            reverse=True
        )


        # -------------------------------------------------
        # PRINT RESULTS
        # -------------------------------------------------

        best = detections[0]


        print(
            "Best Detection   :",
            best["damage_type"]
        )

        print(
            "Confidence       :",
            f'{best["confidence"]:.2f}%'
        )

        print(
            "Area Ratio       :",
            f'{best["area_ratio"]:.2f}%'
        )

        print(
            "Detection Count  :",
            len(detections)
        )


        print("\nAll detections:")


        for i, detection in enumerate(
            detections,
            start=1
        ):

            print(
                f"  {i}. "
                f'{detection["damage_type"]} | '
                f'Confidence: '
                f'{detection["confidence"]:.2f}% | '
                f'Area: '
                f'{detection["area_ratio"]:.2f}%'
            )


    except Exception as e:

        print(
            "ERROR:",
            str(e)
        )


print("\n")
print("=" * 65)
print("                 TEST COMPLETE")
print("=" * 65)