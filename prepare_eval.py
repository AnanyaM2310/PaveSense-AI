from pathlib import Path
import shutil

ROOT = Path(__file__).resolve().parent
SOURCE = ROOT / "datasets" / "rdd2022_india" / "test"
OUTPUT = ROOT / "datasets" / "rdd2022_eval"

# Dataset class ID -> model class ID
CLASS_MAP = {0: 0, 3: 1, 5: 2, 6: 3}
IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

if not SOURCE.exists():
    raise FileNotFoundError(f"Test directory not found: {SOURCE}")

images_out = OUTPUT / "images" / "test"
labels_out = OUTPUT / "labels" / "test"
images_out.mkdir(parents=True, exist_ok=True)
labels_out.mkdir(parents=True, exist_ok=True)

included = 0
skipped = 0

for image in SOURCE.iterdir():
    if image.suffix.lower() not in IMAGE_EXTS:
        continue

    label = image.with_suffix(".txt")
    if not label.exists():
        skipped += 1
        continue

    lines = label.read_text(encoding="utf-8").splitlines()
    remapped = []
    valid_image = True

    for line in lines:
        if not line.strip():
            continue

        parts = line.split()
        if len(parts) != 5:
            valid_image = False
            break

        try:
            class_id = int(parts[0])
            values = [float(v) for v in parts[1:]]
        except ValueError:
            valid_image = False
            break

        if class_id not in CLASS_MAP:
            valid_image = False
            break

        if not all(0 <= v <= 1 for v in values):
            valid_image = False
            break

        remapped.append(
            f"{CLASS_MAP[class_id]} " + " ".join(parts[1:])
        )

    if not valid_image:
        skipped += 1
        continue

    shutil.copy2(image, images_out / image.name)
    (labels_out / label.name).write_text(
        "\n".join(remapped) + ("\n" if remapped else ""),
        encoding="utf-8",
    )
    included += 1

yaml_path = OUTPUT / "data.yaml"
yaml_path.write_text(
    f"path: {OUTPUT.as_posix()}\n"
    "train: images/test\n"
    "val: images/test\n"
    "test: images/test\n"
    "names:\n"
    "  0: D00\n"
    "  1: D10\n"
    "  2: D20\n"
    "  3: D40\n"
    "  4: Repair\n",
    encoding="utf-8",
)

print(f"Included test images: {included}")
print(f"Skipped images: {skipped}")
print(f"Evaluation config: {yaml_path}")
print("Original dataset unchanged.")