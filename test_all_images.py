from app.ai.image_analyzer import analyze_image


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
# RUN ANALYSIS
# =========================================================

print("\n")
print("=" * 60)
print("        PAVESENSE AI - MULTI IMAGE TEST")
print("=" * 60)


for image in images:

    print("\n")
    print("-" * 60)
    print(f"IMAGE: {image}")
    print("-" * 60)

    result = analyze_image(image)

    if not result["success"]:

        print("Analysis failed.")
        print("Message:", result["message"])
        continue


    print(
        "Damage Type      :",
        result["damage_type"]
    )

    print(
        "YOLO Confidence  :",
        f'{result["confidence"]:.2f}%'
    )

    print(
        "Severity         :",
        result["severity"]
    )

    print(
        "Detection Count  :",
        result["detection_count"]
    )

    print(
        "Area Ratio       :",
        f'{result["area_ratio"]:.2f}%'
    )

    print("\nIndividual detections:")

    for i, detection in enumerate(
        result.get("detections", []),
        start=1
    ):

        print(
            f"  {i}. "
            f'{detection["damage_type"]} | '
            f'Confidence: {detection["confidence"]:.2f}% | '
            f'Area: {detection["area_ratio"]:.2f}%'
        )


print("\n")
print("=" * 60)
print("                 TEST COMPLETE")
print("=" * 60)
print("\n")