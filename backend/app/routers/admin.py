from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import NewCaseCandidate, RetrainingQueue, User
from app.routers.auth import get_current_user

router = APIRouter(prefix="/admin", tags=["admin"])


def _require_admin(user: User):
    if user.role != "admin":
        raise HTTPException(403, "Admin only")


@router.get("/pending_cases")
def list_pending(db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)):
    _require_admin(user)
    cases = db.query(NewCaseCandidate).filter(
        NewCaseCandidate.approved_for_train == False).all()
    return [{"id": c.id, "label": c.lab_confirmed_label,
             "image": c.image_path, "created_at": c.created_at}
            for c in cases]


@router.post("/approve_case/{case_id}")
def approve_case(case_id: int,
                 db: Session = Depends(get_db),
                 user: User = Depends(get_current_user)):
    _require_admin(user)
    case = db.query(NewCaseCandidate).filter(NewCaseCandidate.id == case_id).first()
    if not case:
        raise HTTPException(404, "Case not found")
    if not case.lab_confirmed:
        raise HTTPException(400, "Case is not lab-confirmed")

    case.approved_for_train = True
    db.add(RetrainingQueue(case_id=case.id))
    db.commit()
    return {"status": "approved", "case_id": case.id}


@router.get("/retraining_queue")
def queue_list(db: Session = Depends(get_db),
               user: User = Depends(get_current_user)):
    _require_admin(user)
    items = db.query(RetrainingQueue).filter(RetrainingQueue.consumed == False).all()
    return [{"queue_id": q.id, "case_id": q.case_id, "added_at": q.added_at}
            for q in items]


@router.post("/trigger_retrain")
def trigger_retrain(db: Session = Depends(get_db),
                    user: User = Depends(get_current_user)):
    _require_admin(user)
    n = db.query(RetrainingQueue).filter(RetrainingQueue.consumed == False).count()
    return {"ready_for_retrain": n,
            "message": "Run offline training with these cases."}