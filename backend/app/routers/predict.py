import os
import uuid
import shutil
from fastapi import APIRouter, UploadFile, File, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Prediction, User
from app.ml.inference import predict_7class, predict_binary, occlusion_sensitivity
from app.routers.auth import get_current_user
from app.config import settings

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
        result = predict_7class(path)
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