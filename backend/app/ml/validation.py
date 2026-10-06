import os
import cv2
import numpy as np

_ood_cache = {"mean": None, "precision": None}


def _load_ood():
    if _ood_cache["mean"] is None:
        base = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
        mean_path = os.path.join(base, "models", "ood_mean.npy")
        prec_path = os.path.join(base, "models", "ood_precision.npy")
        if os.path.exists(mean_path) and os.path.exists(prec_path):
            _ood_cache["mean"] = np.load(mean_path)
            _ood_cache["precision"] = np.load(prec_path)
    return _ood_cache["mean"], _ood_cache["precision"]


def check_image_quality(path,
                        min_size=64,
                        min_sharpness=100,
                        min_brightness=40,
                        max_brightness=220):
    img = cv2.imread(path)
    if img is None:
        return False, "Cannot read image"
    h, w = img.shape[:2]
    if h < min_size or w < min_size:
        return False, f"Image too small ({w}x{h})"

    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    sharpness = cv2.Laplacian(gray, cv2.CV_64F).var()
    if sharpness < min_sharpness:
        return False, f"Image too blurry (sharpness={sharpness:.1f})"

    brightness = gray.mean()
    if brightness < min_brightness:
        return False, "Image too dark"
    if brightness > max_brightness:
        return False, "Image too bright"

    return True, "ok"


def check_skin_like_colors(path, min_skin_ratio=0.20):
    img = cv2.imread(path)
    if img is None:
        return False, "Cannot read image"
    img = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
    hsv = cv2.cvtColor(img, cv2.COLOR_RGB2HSV)

    lower = np.array([0, 30, 60], dtype=np.uint8)
    upper = np.array([35, 180, 255], dtype=np.uint8)
    mask = cv2.inRange(hsv, lower, upper)
    ratio = mask.mean() / 255.0

    if ratio < min_skin_ratio:
        return False, f"Not a skin image (skin-like pixels: {ratio*100:.1f}%)"
    return True, "ok"


def check_ood(feature_vector, threshold=6000.0):
    mean, precision = _load_ood()
    if mean is None or precision is None:
        return True, "ok (no OOD model)"
    delta = feature_vector - mean
    score = float(np.einsum("i,ij,j->", delta, precision, delta))
    if score > threshold:
        return False, f"Out of distribution (score={score:.0f} > {threshold:.0f})"
    return True, "ok"


def validate_image(path):
    """Gates 1 and 2 only (no feature vector available at this point)."""
    ok, msg = check_image_quality(path)
    if not ok:
        return False, "quality", msg

    ok, msg = check_skin_like_colors(path)
    if not ok:
        return False, "not_skin", msg

    return True, "accepted", ""