
from pathlib import Path
from ultralytics import YOLO

for path in [
    Path("weights/yolo12s_RDD2022_best.pt"),
    Path("weights/best.pt"),
]:
    print(f"\n{'=' * 55}")
    print("Weights:", path)

    if not path.exists():
        print("File not found")
        continue

    model = YOLO(str(path))
    print("Task:", model.task)
    print("Number of classes:", len(model.names))
    print("Class names:", model.names)

    checkpoint = getattr(model, "ckpt", None)
    if isinstance(checkpoint, dict):
        print("Training arguments:")
        args = checkpoint.get("train_args", {})
        for key in ("data", "model", "epochs", "imgsz"):
            print(f"  {key}: {args.get(key, 'not recorded')}")
