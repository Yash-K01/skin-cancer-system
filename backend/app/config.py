import os
from pathlib import Path
from pydantic_settings import BaseSettings


def _parse_origins(val: str) -> list:
    if not val:
        return ["*"]
    val = val.strip()
    if val.startswith("["):
        # JSON list
        import json
        try:
            return json.loads(val)
        except Exception:
            pass
    # Comma-separated
    return [x.strip() for x in val.split(",") if x.strip()]


class Settings(BaseSettings):
    MODEL_7CLASS: str = os.getenv("MODEL_7CLASS", "models/densenet121_7class.keras")
    MODEL_BINARY: str = os.getenv("MODEL_BINARY", "models/densenet201_binary.keras")
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
    ACCESS_TOKEN_EXPIRE_MINUTES: int = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "1440"))

    ALLOWED_ORIGINS: list = _parse_origins(os.getenv("ALLOWED_ORIGINS", "*"))

    class Config:
        env_file = ".env"
        extra = "ignore"


settings = Settings()
Path(settings.UPLOAD_DIR).mkdir(exist_ok=True, parents=True)