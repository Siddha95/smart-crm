from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_ai_provider, get_embedding_provider_dep
from models import Record
from services.ai.base import AIProvider
from services.ai import prompts
from services.embeddings.base import EmbeddingProvider

router = APIRouter(prefix="/ai", tags=["ai"])

# Numero di record passati all'AI per ogni richiesta — bilanciamento costo/precisione
TOP_K = 10


class ChatRequest(BaseModel):
    question: str


def _find_similar_records(
    query: str,
    datasource_id: int,
    db: Session,
    embedding_provider: EmbeddingProvider,
    top_k: int = TOP_K,
) -> list[Record]:
    """Trova i record più simili alla query usando distanza coseno sugli embeddings."""
    query_embedding = embedding_provider.embed(query)
    return (
        db.query(Record)
        .filter(Record.data_source_id == datasource_id, Record.is_active.is_(True))
        .order_by(Record.embedding.cosine_distance(query_embedding))
        .limit(top_k)
        .all()
    )


@router.post("/records/{record_id}/analyze")
def analyze_record(
    record_id: int,
    db: Session = Depends(get_db),
    provider: AIProvider = Depends(get_ai_provider),
):
    record = db.query(Record).filter(Record.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record non trovato.")

    analysis = prompts.analyze_record(provider, record.data)
    return {"record_id": record_id, "analysis": analysis}


@router.post("/records/{record_id}/suggest")
def suggest_actions(
    record_id: int,
    db: Session = Depends(get_db),
    provider: AIProvider = Depends(get_ai_provider),
):
    record = db.query(Record).filter(Record.id == record_id).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record non trovato.")

    suggestions = prompts.suggest_actions(provider, record.data)
    return {"record_id": record_id, "suggestions": suggestions}


@router.post("/datasources/{datasource_id}/chat")
def chat(
    datasource_id: int,
    body: ChatRequest,
    db: Session = Depends(get_db),
    provider: AIProvider = Depends(get_ai_provider),
    embedding_provider: EmbeddingProvider = Depends(get_embedding_provider_dep),
):
    """Risponde a una domanda usando solo i record più rilevanti (RAG)."""
    records = _find_similar_records(body.question, datasource_id, db, embedding_provider)
    if not records:
        raise HTTPException(status_code=404, detail="Nessun record trovato per questa domanda.")

    context = f"Domanda: {body.question}"
    answer = prompts.generate_report(provider, [r.data for r in records], context)
    return {"question": body.question, "records_used": len(records), "answer": answer}
