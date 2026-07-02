from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth_router import router as auth_router
from app.api.clients_router import router as clients_router
from app.api.closing_router import router as closing_router
from app.api.ingest_router import router as ingest_router
from app.config import Settings

_settings = Settings.from_env()
app = FastAPI(title="RUMO Closing Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=_settings.cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(clients_router)
app.include_router(closing_router)
app.include_router(ingest_router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
