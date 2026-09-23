import base64
import cv2
import numpy as np
import tensorflow as tf
from app.config import settings
from app.ml.loader import get_model
from app.ml.uncertainty import uncertainty_report


def preprocess(image_path):
    raw = cv2.imread(image_path)
    if raw is None:
        raise ValueError(f"Cannot read image: {image_path}")
    raw = cv2.cvtColor(raw, cv2.COLOR_BGR2RGB)
    raw = cv2.resize(raw, (settings.IMG_SIZE, settings.IMG_SIZE))
    arr = raw.astype(np.float32)
    arr = tf.keras.applications.densenet.preprocess_input(arr)
    return raw, np.expand_dims(arr, axis=0)


def predict_7class(image_path):
    model = get_model("7class")
    raw, arr = preprocess(image_path)
    probs = model.predict(arr, verbose=0)[0]
    cls_idx = int(np.argmax(probs))
    predicted = settings.CLASS_NAMES_7[cls_idx]
    unc = uncertainty_report(probs)

    return {
        "predicted_class": predicted,
        "confidence": float(probs[cls_idx]),
        "probabilities": {c: float(probs[i])
                          for i, c in enumerate(settings.CLASS_NAMES_7)},
        **unc,
    }


def predict_binary(image_path):
    model = get_model("binary")
    raw, arr = preprocess(image_path)
    probs = model.predict(arr, verbose=0)[0]
    cls_idx = int(np.argmax(probs))
    label = ["Benign", "Malignant"][cls_idx]

    return {
        "predicted_class": label,
        "confidence": float(probs[cls_idx]),
        "probabilities": {"Benign": float(probs[0]),
                          "Malignant": float(probs[1])},
    }


def occlusion_sensitivity(image_path, patch=32, stride=16, model_name="7class"):
    model = get_model(model_name)
    raw, arr = preprocess(image_path)
    base_pred = model.predict(arr, verbose=0)[0]
    pred_class = int(np.argmax(base_pred))
    base_p = base_pred[pred_class]

    h, w = arr.shape[1:3]
    sal = np.zeros((h, w), dtype=np.float32)

    for y in range(0, h - patch + 1, stride):
        for x in range(0, w - patch + 1, stride):
            occl = arr.copy()
            occl[0, y:y+patch, x:x+patch] = 0.0
            p = model.predict(occl, verbose=0)[0][pred_class]
            sal[y:y+patch, x:x+patch] = base_p - p

    sal = np.maximum(sal, 0)
    sal = sal / (sal.max() + 1e-8)

    hm = cv2.resize(sal, (raw.shape[1], raw.shape[0]))
    hm = np.uint8(255 * hm)
    hm_color = cv2.applyColorMap(hm, cv2.COLORMAP_JET)
    hm_color = cv2.cvtColor(hm_color, cv2.COLOR_BGR2RGB)
    overlay = cv2.addWeighted(raw, 0.6, hm_color, 0.4, 0)

    _, buf = cv2.imencode(".png", cv2.cvtColor(overlay, cv2.COLOR_RGB2BGR))
    b64 = base64.b64encode(buf).decode()

    return {
        "saliency_png_b64": b64,
        "predicted_class_idx": pred_class,
        "base_confidence": float(base_p),
    }