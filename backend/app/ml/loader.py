import os
from ai_edge_litert.interpreter import Interpreter
from app.config import settings

_interpreters = {}


def _load_one(name: str):
    if name in _interpreters:
        return _interpreters[name]

    path = settings.MODEL_7CLASS if name == "7class" else settings.MODEL_BINARY
    if not os.path.exists(path):
        raise RuntimeError(f"Model not found: {path}")

    interp = Interpreter(model_path=path)
    interp.allocate_tensors()   # required before any inference
    _interpreters[name] = {
        "interpreter": interp,
        "input": interp.get_input_details(),
        "output": interp.get_output_details(),
    }
    return _interpreters[name]


def load_models():
    """Just verify the files exist — lazy load on first request."""
    for name, p in [("7class", settings.MODEL_7CLASS),
                    ("binary", settings.MODEL_BINARY)]:
        print(f"[loader] {name}: {'OK' if os.path.exists(p) else 'MISSING'} {p}")


def get_model(name: str):
    return _load_one(name)