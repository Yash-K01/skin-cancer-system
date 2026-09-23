from sqlalchemy import (Column, Integer, String, Float, DateTime, Boolean,
                        ForeignKey, Text, JSON)
from sqlalchemy.orm import relationship
from sqlalchemy.sql import func
from app.database import Base


class User(Base):
    __tablename__ = "users"
    id              = Column(Integer, primary_key=True)
    email           = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name       = Column(String)
    role            = Column(String, default="doctor")
    created_at      = Column(DateTime, server_default=func.now())

    predictions = relationship("Prediction", back_populates="user")


class Prediction(Base):
    __tablename__ = "predictions"
    id              = Column(Integer, primary_key=True)
    user_id         = Column(Integer, ForeignKey("users.id"), index=True)
    image_path      = Column(String, nullable=False)
    model_used      = Column(String)
    predicted_class = Column(String)
    confidence      = Column(Float)
    probabilities   = Column(JSON)
    status          = Column(String, index=True)
    reason          = Column(String)
    entropy         = Column(Float)
    margin          = Column(Float)
    created_at      = Column(DateTime, server_default=func.now())

    user     = relationship("User", back_populates="predictions")
    feedback = relationship("Feedback", uselist=False, back_populates="prediction")


class Feedback(Base):
    __tablename__ = "feedback"
    id              = Column(Integer, primary_key=True)
    prediction_id   = Column(Integer, ForeignKey("predictions.id"), unique=True)
    doctor_label    = Column(String)
    agrees          = Column(Boolean)
    notes           = Column(Text)
    created_at      = Column(DateTime, server_default=func.now())

    prediction = relationship("Prediction", back_populates="feedback")


class NewCaseCandidate(Base):
    __tablename__ = "new_case_candidates"
    id                  = Column(Integer, primary_key=True)
    user_id             = Column(Integer, ForeignKey("users.id"))
    image_path          = Column(String, nullable=False)
    lab_confirmed_label = Column(String)
    patient_age         = Column(Integer)
    patient_sex         = Column(String)
    lesion_site         = Column(String)
    clinical_notes      = Column(Text)
    lab_confirmed       = Column(Boolean, default=False)
    approved_for_train  = Column(Boolean, default=False)
    created_at          = Column(DateTime, server_default=func.now())


class RetrainingQueue(Base):
    __tablename__ = "retraining_queue"
    id          = Column(Integer, primary_key=True)
    case_id     = Column(Integer, ForeignKey("new_case_candidates.id"))
    added_at    = Column(DateTime, server_default=func.now())
    consumed    = Column(Boolean, default=False)
    consumed_at = Column(DateTime)