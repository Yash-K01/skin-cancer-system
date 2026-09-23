import os
from pathlib import Path
from pydantic_settings import BaseSettings


def _parse_origins(val: str) -> list:
    if not val:
        return ["*"]
    val = val.strip()
    if val.startswith("["):
        import json
        try:
            return json.loads(val)
        except Exception:
            pass
    return [x.strip() for x in val.split(",") if x.strip()]


class Settings(BaseSettings):
    MODEL_7CLASS: str = "models/densenet121_7class.keras"
    MODEL_BINARY: str = "models/densenet201_binary.keras"
    UPLOAD_DIR: str = "uploads"
    IMG_SIZE: int = 224

    CLASS_NAMES_7: list = ["akiec", "bcc", "bkl", "df", "mel", "nv", "vasc"]
    MALIGNANT_CLASSES: set = {"mel", "bcc", "akiec"}

    CONFIDENCE_MIN: float = 0.60
    MARGIN_MIN: float = 0.20
    ENTROPY_MAX: float = 1.5

    DATABASE_URL: str = "sqlite:///./skin_cancer.db"

    SECRET_KEY: str = "change-this-in-production"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 1440

    CORS_ORIGINS: str = "*"

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
settings.ALLOWED_ORIGINS = _parse_origins(settings.CORS_ORIGINS)
Path(settings.UPLOAD_DIR).mkdir(exist_ok=True, parents=True)