import os
import uuid
import shutil
import numpy as np
import traceback
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Prediction, User
from app.ml.inference import (predict_7class_with_gate, predict_binary,
                              occlusion_sensitivity)
from app.routers.auth import get_current_user
from app.config import settings
from app.ml.prescription import generate_prescription

router = APIRouter(prefix="/predict", tags=["predict"])


def _save_upload(file: UploadFile) -> str:
    ext = os.path.splitext(file.filename)[1].lower() or ".jpg"
    name = f"{uuid.uuid4().hex}{ext}"
    path = os.path.join(settings.UPLOAD_DIR, name)
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)
    return path


@router.post("/7class")
def classify_7class(file: UploadFile = File(...),
                    db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
    path = _save_upload(file)
    try:
        result = predict_7class_with_gate(path)
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"Inference failed: {e}")

    p = Prediction(
        user_id=user.id,
        image_path=path,
        model_used="7class",
        predicted_class=result.get("predicted_class"),
        confidence=result.get("confidence"),
        probabilities=result.get("probabilities"),
        status=result.get("status"),
        reason=result.get("reason"),
        entropy=result.get("entropy"),
        margin=result.get("margin"),
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return {"prediction_id": p.id, **result}


@router.post("/binary")
def classify_binary(file: UploadFile = File(...),
                    db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
    path = _save_upload(file)
    result = predict_binary(path)

    p = Prediction(
        user_id=user.id,
        image_path=path,
        model_used="binary",
        predicted_class=result.get("predicted_class"),
        confidence=result.get("confidence"),
        probabilities=result.get("probabilities"),
        status="ok",
        reason="binary_only",
    )
    db.add(p)
    db.commit()
    db.refresh(p)
    return {"prediction_id": p.id, **result}


@router.post("/7class/explain")
def explain_7class(file: UploadFile = File(...),
                   user: User = Depends(get_current_user)):
    path = _save_upload(file)
    return occlusion_sensitivity(path, model_name="7class")


@router.post("/prescription")
def get_prescription(prediction_id: int,
                     db: Session = Depends(get_db),
                     user: User = Depends(get_current_user)):
    pred = db.query(Prediction).filter(Prediction.id == prediction_id).first()
    if not pred:
        raise HTTPException(404, "Prediction not found")
    if pred.user_id != user.id:
        raise HTTPException(403, "Not your prediction")

    MALIGNANT = {"mel", "bcc", "akiec"}
    binary_label = "Malignant" if pred.predicted_class in MALIGNANT else "Benign"
    binary_conf = pred.confidence or 0.0

    try:
        text = generate_prescription(
            predicted_class=pred.predicted_class,
            confidence=pred.confidence or 0.0,
            binary_label=binary_label,
            binary_confidence=binary_conf,
        )
    except Exception as e:
        print("=" * 60)
        print("[PRESCRIPTION ERROR]", repr(e))
        traceback.print_exc()
        print("=" * 60)
        raise HTTPException(500, f"Prescription generation failed: {e}")
    return {"prediction_id": pred.id, "prescription": text}


@router.post("/debug/validate")
def debug_validate(file: UploadFile = File(...)):
    from app.ml.validation import check_image_quality, check_skin_like_colors, check_ood
    from app.ml.inference import _preprocess, _run
    from app.ml.loader import get_model

    ext = os.path.splitext(file.filename)[1].lower() or ".jpg"
    name = f"debug_{uuid.uuid4().hex}{ext}"
    path = os.path.join(settings.UPLOAD_DIR, name)
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    ok1, msg1 = check_image_quality(path)
    ok2, msg2 = check_skin_like_colors(path)

    data = get_model("7class")
    _, arr = _preprocess(path)
    probs, feat = _run(data, arr)

    ood_result = None
    if feat is not None:
        from app.ml.validation import _load_ood
        mean, prec = _load_ood()
        if mean is not None:
            delta = feat - mean
            score = float(np.einsum("i,ij,j->", delta, prec, delta))
            ok3, msg3 = check_ood(feat)
            ood_result = {
                "score": score,
                "ok": ok3,
                "msg": msg3,
                "threshold": 6000.0,
            }
        else:
            ood_result = {"error": "ood_mean.npy / ood_precision.npy not found"}
    else:
        ood_result = {"error": "feat_out is None — old single-output tflite deployed"}

    return {
        "quality": {"ok": ok1, "msg": msg1},
        "skin_tone": {"ok": ok2, "msg": msg2},
        "ood": ood_result,
        "prediction": {
            "class": settings.CLASS_NAMES_7[int(np.argmax(probs))],
            "confidence": float(probs.max()),
        },
    }