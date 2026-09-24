import base64
import cv2
import numpy as np
from app.config import settings
from app.ml.loader import get_model
from app.ml.uncertainty import uncertainty_report


def _preprocess(image_path):
    raw = cv2.imread(image_path)
    if raw is None:
        raise ValueError(f"Cannot read image: {image_path}")
    raw = cv2.cvtColor(raw, cv2.COLOR_BGR2RGB)
    raw = cv2.resize(raw, (settings.IMG_SIZE, settings.IMG_SIZE))
    arr = raw.astype(np.float32)
    # DenseNet preprocessing: scale to [-1, 1] via keras.applications.densenet
    # For TFLite we reproduce it manually: (x / 127.5) - 1
    arr = (arr / 127.5) - 1.0
    return raw, np.expand_dims(arr, axis=0).astype(np.float32)


def _run(interp_data, arr):
    interp = interp_data["interpreter"]
    inp = interp_data["input"][0]
    out = interp_data["output"][0]
    interp.set_tensor(inp["index"], arr)
    interp.invoke()
    return interp.get_tensor(out["index"])[0]


def predict_7class(image_path):
    data = get_model("7class")
    raw, arr = _preprocess(image_path)
    probs = _run(data, arr)

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
    data = get_model("binary")
    raw, arr = _preprocess(image_path)
    probs = _run(data, arr)

    cls_idx = int(np.argmax(probs))
    label = ["Benign", "Malignant"][cls_idx]

    return {
        "predicted_class": label,
        "confidence": float(probs[cls_idx]),
        "probabilities": {"Benign": float(probs[0]),
                          "Malignant": float(probs[1])},
    }


def occlusion_sensitivity(image_path, patch=32, stride=16, model_name="7class"):
    data = get_model(model_name)
    raw, arr = _preprocess(image_path)
    base_pred = _run(data, arr)
    pred_class = int(np.argmax(base_pred))
    base_p = base_pred[pred_class]

    h, w = arr.shape[1:3]
    sal = np.zeros((h, w), dtype=np.float32)

    for y in range(0, h - patch + 1, stride):
        for x in range(0, w - patch + 1, stride):
            occl = arr.copy()
            occl[0, y:y+patch, x:x+patch] = 0.0
            p = _run(data, occl)[pred_class]
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