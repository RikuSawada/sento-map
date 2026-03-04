from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.routers.auth import router as auth_router
from app.routers.review import router as review_router
from app.routers.sento import router as sento_router

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.cors_origin],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router, prefix="/auth", tags=["auth"])
app.include_router(sento_router, prefix="/sentos", tags=["sentos"])
app.include_router(review_router, prefix="/sentos", tags=["reviews"])


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
