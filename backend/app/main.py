from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.routers import context, diagnose
from app.settings import APP_DIR, settings

app = FastAPI(title="Agri-Vision")

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.CORS_ORIGINS,
    allow_methods=["*"],
    allow_headers=["*"],
)

settings.AUDIO_DIR.mkdir(parents=True, exist_ok=True)
app.mount("/static", StaticFiles(directory=str(settings.AUDIO_DIR.parent)), name="static")

app.include_router(context.router, prefix="/api")
app.include_router(diagnose.router, prefix="/api")

if settings.ENABLE_DOSAGE:
    from app.routers import dosage

    app.include_router(dosage.router, prefix="/api")

if settings.ENABLE_SEVERITY:
    from app.routers import severity

    app.include_router(severity.router, prefix="/api")

if settings.ENABLE_ASK:
    from app.routers import ask

    app.include_router(ask.router, prefix="/api")


@app.get("/health")
def health() -> dict:
    return {
        "status": "ok",
        "llm_backend": settings.LLM_BACKEND,
        "features": {
            "dosage": settings.ENABLE_DOSAGE,
            "severity": settings.ENABLE_SEVERITY,
            "ask": settings.ENABLE_ASK,
        },
        "db_exists": settings.DB_PATH.exists(),
    }


if settings.SERVE_FRONTEND:
    frontend_dist = APP_DIR.parent.parent / "frontend" / "dist"
    if frontend_dist.is_dir():
        app.mount("/", StaticFiles(directory=str(frontend_dist), html=True), name="frontend")
