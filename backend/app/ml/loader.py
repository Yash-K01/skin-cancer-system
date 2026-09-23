import os
import tensorflow as tf
from app.config import settings

_models = {}


def load_models():
    if os.path.exists(settings.MODEL_7CLASS):
        _models["7class"] = tf.keras.models.load_model(
            settings.MODEL_7CLASS, compile=False)
        print(f"[loader] Loaded 7-class: {settings.MODEL_7CLASS}")
    else:
        print(f"[loader] WARNING: {settings.MODEL_7CLASS} not found")

    if os.path.exists(settings.MODEL_BINARY):
        _models["binary"] = tf.keras.models.load_model(
            settings.MODEL_BINARY, compile=False)
        print(f"[loader] Loaded binary: {settings.MODEL_BINARY}")
    else:
        print(f"[loader] WARNING: {settings.MODEL_BINARY} not found")

    return _models


def get_model(name: str):
    if name not in _models:
        raise RuntimeError(f"Model '{name}' not loaded.")
    return _models[name]