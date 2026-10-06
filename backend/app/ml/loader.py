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
    interp.allocate_tensors()

    inputs  = interp.get_input_details()
    outputs = interp.get_output_details()

    pred_out = None
    feat_out = None

    for o in outputs:
        last_dim = int(o["shape"][-1])
        if last_dim == 1024:                          # 7-class model features
            feat_out = o
        elif last_dim == len(settings.CLASS_NAMES_7): # 7-class predictions
            pred_out = o

    # Binary model has only one output (2 classes)
    if pred_out is None and len(outputs) == 1:
        pred_out = outputs[0]

    # Fallback: if nothing matched, assume output 0 is predictions
    if pred_out is None:
        pred_out = outputs[0]

    _interpreters[name] = {
        "interpreter": interp,
        "input": inputs,
        "output": outputs,
        "pred_out": pred_out,
        "feat_out": feat_out,   # None for the binary model
    }
    return _interpreters[name]


def load_models():
    for name, p in [("7class", settings.MODEL_7CLASS),
                    ("binary", settings.MODEL_BINARY)]:
        print(f"[loader] {name}: {'OK' if os.path.exists(p) else 'MISSING'} {p}")


def get_model(name: str):
    return _load_one(name)