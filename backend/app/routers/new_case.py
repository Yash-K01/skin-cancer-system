import os
import uuid
import shutil
from fastapi import APIRouter, UploadFile, File, Form, Depends
from sqlalchemy.orm import Session
from app.database import get_db
from app.models import NewCaseCandidate, User
from app.routers.auth import get_current_user
from app.config import settings

router = APIRouter(prefix="/new_case", tags=["new_case"])


@router.post("/submit")
async def submit_new_case(
    file: UploadFile = File(...),
    lab_confirmed_label: str = Form(...),
    patient_age: int = Form(None),
    patient_sex: str = Form(None),
    lesion_site: str = Form(None),
    clinical_notes: str = Form(None),
    db: Session = Depends(get_db),
    user: User = Depends(get_current_user),
):
    ext = os.path.splitext(file.filename)[1].lower() or ".jpg"
    name = f"newcase_{uuid.uuid4().hex}{ext}"
    path = os.path.join(settings.UPLOAD_DIR, name)
    with open(path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    case = NewCaseCandidate(
        user_id=user.id,
        image_path=path,
        lab_confirmed_label=lab_confirmed_label,
        patient_age=patient_age,
        patient_sex=patient_sex,
        lesion_site=lesion_site,
        clinical_notes=clinical_notes,
        lab_confirmed=True,
        approved_for_train=False,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return {"case_id": case.id, "status": "pending_admin_approval"}