from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.api.auth_router import router as auth_router
from app.api.clients_router import router as clients_router
from app.api.closing_router import router as closing_router

app = FastAPI(title="RUMO Closing Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # narrowed via env in Task 8.x
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(clients_router)
app.include_router(closing_router)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
