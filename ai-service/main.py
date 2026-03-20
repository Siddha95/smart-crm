from contextlib import asynccontextmanager

from fastapi import FastAPI
from sqlalchemy import text

from database import engine
from routers import ai, reports


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Verifica la connessione al DB all'avvio — fallisce subito se Postgres non è raggiungibile
    with engine.connect() as conn:
        conn.execute(text("SELECT 1"))
    yield


app = FastAPI(title="Smart CRM - AI Service", lifespan=lifespan)

app.include_router(reports.router)
app.include_router(ai.router)


@app.get("/health")
def health():
    return {"status": "ok"}
