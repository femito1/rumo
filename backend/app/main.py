from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

app = FastAPI(title="RUMO Closing Platform API")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # narrowed via env in Task 8.x
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}
