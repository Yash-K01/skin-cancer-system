from pydantic_settings import BaseSettings
from pathlib import Path
import os


class Settings(BaseSettings):
    MODEL_7CLASS: str = "models/densenet121_7class.keras"
    MODEL_BINARY: str = "models/densenet201_binary.keras"
    UPLOAD_DIR: str = os.getenv("UPLOAD_DIR", "uploads")
    IMG_SIZE: int = 224

    CLASS_NAMES_7: list = ["akiec", "bcc", "bkl", "df", "mel", "nv", "vasc"]
    MALIGNANT_CLASSES: set = {"mel", "bcc", "akiec"}

    CONFIDENCE_MIN: float = 0.60
    MARGIN_MIN: float = 0.20
    ENTROPY_MAX: float = 1.5

    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./skin_cancer.db")

    SECRET_KEY: str = os.getenv("SECRET_KEY", "change-this-in-production")
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 60 * 24

    ALLOWED_ORIGINS: list = os.getenv(
        "ALLOWED_ORIGINS",
        '["http://localhost:5173","http://localhost:3000"]'
    ) if isinstance(os.getenv("ALLOWED_ORIGINS"), str) else ["*"]

    class Config:
        env_file = ".env"


# Parse ALLOWED_ORIGINS from JSON string if provided via env
import json
_orig = os.getenv("ALLOWED_ORIGINS")
if _orig:
    try:
        _parsed = json.loads(_orig)
    except Exception:
        _parsed = ["*"]
else:
    _parsed = ["http://localhost:5173", "http://localhost:3000", "*"]


class SettingsWithCORS(Settings):
    ALLOWED_ORIGINS: list = _parsed


settings = SettingsWithCORS()
Path(settings.UPLOAD_DIR).mkdir(exist_ok=True, parents=True)