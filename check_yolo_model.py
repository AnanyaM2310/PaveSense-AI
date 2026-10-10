from pathlib import Path
from ultralytics import YOLO

model_path = Path("weights/yolo12s_RDD2022_best.pt")

if not model_path.exists():
    raise FileNotFoundError(f"Model weights not found: {model_path.resolve()}")

model = YOLO(str(model_path))

print("\nModel loaded successfully.")
print("Model path:", model_path.resolve())
print("Task:", model.task)
print("Number of classes:", len(model.names))
print("Class names:")

for class_id, class_name in model.names.items():
    print(f"  {class_id}: {class_name}")