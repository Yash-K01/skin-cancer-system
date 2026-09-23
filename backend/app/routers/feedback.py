from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import Prediction, Feedback, User
from app.schemas import FeedbackIn
from app.routers.auth import get_current_user

router = APIRouter(prefix="/feedback", tags=["feedback"])


@router.post("/")
def submit_feedback(payload: FeedbackIn,
                    db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
    pred = db.query(Prediction).filter(Prediction.id == payload.prediction_id).first()
    if not pred:
        raise HTTPException(404, "Prediction not found")
    if pred.user_id != user.id:
        raise HTTPException(403, "Not your prediction")

    existing = db.query(Feedback).filter(Feedback.prediction_id == pred.id).first()
    if existing:
        existing.doctor_label = payload.doctor_label
        existing.agrees = payload.agrees
        existing.notes = payload.notes
    else:
        db.add(Feedback(
            prediction_id=pred.id,
            doctor_label=payload.doctor_label,
            agrees=payload.agrees,
            notes=payload.notes,
        ))
    db.commit()
    return {"status": "recorded", "prediction_id": pred.id}


@router.get("/my")
def my_feedback(db: Session = Depends(get_db),
                user: User = Depends(get_current_user)):
    items = (db.query(Feedback)
               .join(Prediction, Feedback.prediction_id == Prediction.id)
               .filter(Prediction.user_id == user.id)
               .all())
    return [{"id": f.id, "prediction_id": f.prediction_id,
             "doctor_label": f.doctor_label, "agrees": f.agrees,
             "notes": f.notes, "created_at": f.created_at}
            for f in items]