from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from sqlalchemy import text

from ai_config import settings
from database import engine
from routers import ai, reports


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Verifica la connessione al DB all'avvio — fallisce subito se Postgres non è raggiungibile
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    yield


app = FastAPI(title="Smart CRM - AI Service", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.allowed_origins,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(reports.router)
app.include_router(ai.router)


@app.get("/health")
def health():
    return {"status": "ok"}
