from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.database import Base, engine
from app.ml.loader import load_models
from app.routers import auth, predict, feedback, new_case, admin
from app.config import settings


@asynccontextmanager
async def lifespan(app: FastAPI):
    print("[startup] Creating DB tables...")
    Base.metadata.create_all(bind=engine)
    print("[startup] Loading models...")
    load_models()
    yield
    print("[shutdown] Bye.")


app = FastAPI(
    title="Skin Cancer Detection API",
    version="1.0",
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router)
app.include_router(predict.router)
app.include_router(feedback.router)
app.include_router(new_case.router)
app.include_router(admin.router)


@app.get("/")
def health():
    return {"status": "ok", "service": "skin-cancer-api"}