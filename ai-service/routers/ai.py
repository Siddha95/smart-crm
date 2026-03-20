from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import cast, Text
from sqlalchemy.orm import Session

from database import get_db
from dependencies import get_embedding_provider_dep, get_user_ai_provider, get_user_embedding_provider, get_user_id
from models import DataSource, Record
from services.ai.base import AIProvider
from services.ai import prompts
from services.ai.tools import TOOLS_CLAUDE, execute_tool
from services.embeddings.base import EmbeddingProvider

router = APIRouter(prefix="/ai", tags=["ai"])

TOP_K = 8
MAX_FIELD_LEN = 120  # caratteri max per valore di campo
MAX_RECORDS_IN_CONTEXT = 12


class ChatRequest(BaseModel):
    question: str


def _base_query(db: Session, datasource_id: int | None, owner_id: int | None):
    q = db.query(Record).filter(Record.is_active.is_(True))
    if datasource_id:
        q = q.filter(Record.data_source_id == datasource_id)
    elif owner_id:
        q = q.join(DataSource, Record.data_source_id == DataSource.id).filter(DataSource.owner_id == owner_id)
    return q


def _find_by_text(
    query: str, db: Session,
    datasource_id: int | None = None,
    owner_id: int | None = None,
    top_k: int = TOP_K,
) -> list[Record]:
    """Ricerca full-text case-insensitive nel JSONB."""
    from sqlalchemy import or_
    words = [w.strip(".,;:!?\"'()") for w in query.split() if len(w.strip(".,;:!?\"'()")) > 2]
    if not words:
        return []
    conditions = [cast(Record.data, Text).ilike(f"%{w}%") for w in words]
    return _base_query(db, datasource_id, owner_id).filter(or_(*conditions)).limit(top_k).all()


def _find_hybrid(
    query: str,
    db: Session,
    embedding_provider: EmbeddingProvider,
    datasource_id: int | None = None,
    owner_id: int | None = None,
    top_k: int = TOP_K,
) -> list[Record]:
    """Combina ricerca vettoriale + full-text, deduplicata. Funziona con o senza datasource specifico."""
    seen_ids: set[int] = set()
    results: list[Record] = []

    try:
        query_embedding = embedding_provider.embed(query)
        vector_records = (
            _base_query(db, datasource_id, owner_id)
            .order_by(Record.embedding.cosine_distance(query_embedding))
            .limit(top_k)
            .all()
        )
        for r in vector_records:
            if r.id not in seen_ids:
                seen_ids.add(r.id)
                results.append(r)
    except Exception:
        pass

    for r in _find_by_text(query, db, datasource_id, owner_id, top_k):
        if r.id not in seen_ids:
            seen_ids.add(r.id)
            results.append(r)

    return results[:MAX_RECORDS_IN_CONTEXT]


@router.post("/records/{record_id}/analyze")
def analyze_record(
    record_id: int,
    db: Session = Depends(get_db),
    provider: AIProvider = Depends(get_user_ai_provider),
    owner_id: int = Depends(get_user_id),
):
    record = db.query(Record).filter(Record.id == record_id, Record.data_source.has(owner_id=owner_id)).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record non trovato.")

    analysis = prompts.analyze_record(provider, record.data)
    return {"record_id": record_id, "analysis": analysis}


@router.post("/records/{record_id}/suggest")
def suggest_actions(
    record_id: int,
    db: Session = Depends(get_db),
    provider: AIProvider = Depends(get_user_ai_provider),
    owner_id: int = Depends(get_user_id),
):
    record = db.query(Record).filter(Record.id == record_id, Record.data_source.has(owner_id=owner_id)).first()
    if not record:
        raise HTTPException(status_code=404, detail="Record non trovato.")

    suggestions = prompts.suggest_actions(provider, record.data)
    return {"record_id": record_id, "suggestions": suggestions}


def _serialize_record(r: Record) -> str:
    fields = {
        k: (str(v)[:MAX_FIELD_LEN] + "…" if len(str(v)) > MAX_FIELD_LEN else str(v))
        for k, v in r.data.items()
        if v not in (None, "", [])
    }
    return f"[{r.id}] " + ", ".join(f"{k}: {v}" for k, v in fields.items())


def _run_chat(
    question: str,
    records: list[Record],
    provider: AIProvider,
    db: Session,
    owner_id: int,
) -> dict:
    context_rows = "\n".join(_serialize_record(r) for r in records)
    system_prompt = (
        "Assistente CRM. Record disponibili (formato: [ID] campo: valore):\n"
        f"{context_rows}\n\n"
        "Puoi rispondere, modificare campi ed eliminare record con i tool. "
        "Chiedi conferma prima di eliminare. Rispondi in italiano."
    )

    def tool_exec(name: str, inputs: dict) -> str:
        return execute_tool(name, inputs, db, owner_id)

    answer = provider.complete_with_tools(
        messages=[{"role": "user", "content": question}],
        tools=TOOLS_CLAUDE,
        tool_executor=tool_exec,
        system=system_prompt,
    )
    return {"question": question, "records_used": len(records), "answer": answer}


@router.post("/chat")
def chat_global(
    body: ChatRequest,
    db: Session = Depends(get_db),
    provider: AIProvider = Depends(get_user_ai_provider),
    embedding_provider: EmbeddingProvider = Depends(get_user_embedding_provider),
    owner_id: int = Depends(get_user_id),
):
    """Chat cross-datasource: cerca su tutti i dati dell'utente."""
    records = _find_hybrid(body.question, db, embedding_provider, owner_id=owner_id)
    return _run_chat(body.question, records, provider, db, owner_id)


@router.post("/datasources/{datasource_id}/chat")
def chat(
    datasource_id: int,
    body: ChatRequest,
    db: Session = Depends(get_db),
    provider: AIProvider = Depends(get_user_ai_provider),
    embedding_provider: EmbeddingProvider = Depends(get_user_embedding_provider),
    owner_id: int = Depends(get_user_id),
):
    """Chat contestuale a un datasource specifico."""
    records = _find_hybrid(body.question, db, embedding_provider, datasource_id=datasource_id, owner_id=owner_id)
    return _run_chat(body.question, records, provider, db, owner_id)
