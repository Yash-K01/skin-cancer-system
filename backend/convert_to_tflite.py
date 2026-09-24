# convert_to_tflite.py
import tensorflow as tf
import os

MODELS_DIR = "models"

def convert(keras_path, tflite_path):
    print(f"Loading {keras_path}...")
    model = tf.keras.models.load_model(keras_path, compile=False)

    converter = tf.lite.TFLiteConverter.from_keras_model(model)
    # Optional: keep float32 precision (no quantization for highest accuracy)
    converter.optimizations = []
    # Enable TF ops if any custom layers are present
    converter.target_spec.supported_ops = [
        tf.lite.OpsSet.TFLITE_BUILTINS,
        tf.lite.OpsSet.SELECT_TF_OPS,
    ]

    print(f"Converting {keras_path} -> {tflite_path}...")
    tflite_model = converter.convert()

    with open(tflite_path, "wb") as f:
        f.write(tflite_model)
    print(f"Saved: {tflite_path} ({len(tflite_model)/1024/1024:.2f} MB)")

convert(
    os.path.join(MODELS_DIR, "densenet121_7class.keras"),
    os.path.join(MODELS_DIR, "densenet121_7class.tflite"),
)
convert(
    os.path.join(MODELS_DIR, "densenet201_binary.keras"),
    os.path.join(MODELS_DIR, "densenet201_binary.tflite"),
)

print("Done.")