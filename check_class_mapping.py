from pathlib import Path
from collections import Counter
from ultralytics import YOLO

ROOT = Path("datasets/rdd2022_india")
WEIGHTS = Path("weights/yolo12s_RDD2022_best.pt")

dataset_classes = [
    "D00", "D01", "D0w0", "D10", "D11",
    "D20", "D40", "D43", "D44", "D50"
]

model = YOLO(str(WEIGHTS))

print("Model classes:")
for class_id, name in model.names.items():
    print(f"  {class_id}: {name}")

print("\nAnnotation class IDs found in the test split:")
counts = Counter()
invalid_lines = []

for label_file in (ROOT / "test").glob("*.txt"):
    for line_no, line in enumerate(
        label_file.read_text(encoding="utf-8").splitlines(), start=1
    ):
        if not line.strip():
            continue

        parts = line.split()
        try:
            class_id = int(parts[0])
        except (ValueError, IndexError):
            invalid_lines.append((label_file.name, line_no, line))
            continue

        counts[class_id] += 1

print(dict(sorted(counts.items())))

print("\nDataset class mapping:")
for class_id, name in enumerate(dataset_classes):
    print(f"  {class_id}: {name} — {counts[class_id]} annotations")

if invalid_lines:
    print(f"\nMalformed annotation lines: {len(invalid_lines)}")
    for item in invalid_lines[:5]:
        print(item)