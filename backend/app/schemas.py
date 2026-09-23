from pydantic import BaseModel, EmailStr
from typing import Optional, Dict
from datetime import datetime


class UserCreate(BaseModel):
    email: EmailStr
    password: str
    full_name: str
    role: str = "doctor"


class UserOut(BaseModel):
    id: int
    email: str
    full_name: Optional[str]
    role: str
    class Config:
        from_attributes = True


class Token(BaseModel):
    access_token: str
    token_type: str = "bearer"


class PredictionOut(BaseModel):
    id: int
    predicted_class: Optional[str]
    confidence: Optional[float]
    probabilities: Optional[Dict[str, float]]
    status: str
    reason: str
    entropy: Optional[float]
    margin: Optional[float]
    created_at: datetime
    class Config:
        from_attributes = True


class FeedbackIn(BaseModel):
    prediction_id: int
    doctor_label: str
    agrees: bool
    notes: Optional[str] = None


class NewCaseIn(BaseModel):
    lab_confirmed_label: str
    patient_age: Optional[int] = None
    patient_sex: Optional[str] = None
    lesion_site: Optional[str] = None
    clinical_notes: Optional[str] = None