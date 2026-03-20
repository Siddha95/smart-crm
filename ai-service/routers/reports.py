from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_user_ai_provider, get_user_id
from models import DataSource, Record
from services.ai.base import AIProvider
from services.ai import prompts

router = APIRouter(prefix="/reports", tags=["reports"])


@router.get("/datasources")
def list_datasources(
    db: Session = Depends(get_db),
    owner_id: int = Depends(get_user_id),
):
    sources = db.query(DataSource).filter(DataSource.owner_id == owner_id).all()
    return [
        {"id": s.id, "name": s.name, "label": s.label, "columns": s.columns}
        for s in sources
    ]


@router.get("/datasources/{datasource_id}/records")
def list_records(
    datasource_id: int,
    active_only: bool = True,
    db: Session = Depends(get_db),
    owner_id: int = Depends(get_user_id),
):
    source = db.query(DataSource).filter(
        DataSource.id == datasource_id, DataSource.owner_id == owner_id
    ).first()
    if not source:
        raise HTTPException(status_code=404, detail="DataSource non trovato.")

    query = db.query(Record).filter(Record.data_source_id == datasource_id)
    if active_only:
        query = query.filter(Record.is_active.is_(True))
    return [{"id": r.id, "data": r.data} for r in query.all()]


@router.post("/datasources/{datasource_id}/report")
def generate_report(
    datasource_id: int,
    context: str = "",
    db: Session = Depends(get_db),
    provider: AIProvider = Depends(get_user_ai_provider),
    owner_id: int = Depends(get_user_id),
):
    source = db.query(DataSource).filter(
        DataSource.id == datasource_id, DataSource.owner_id == owner_id
    ).first()
    if not source:
        raise HTTPException(status_code=404, detail="DataSource non trovato.")

    records = (
        db.query(Record)
        .filter(Record.data_source_id == datasource_id, Record.is_active.is_(True))
        .all()
    )
    if not records:
        raise HTTPException(status_code=404, detail="Nessun record trovato.")

    report = prompts.generate_report(provider, [r.data for r in records], context)
    return {"datasource": source.name, "report": report}
