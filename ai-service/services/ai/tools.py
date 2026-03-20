"""
Definizioni dei tool che l'AI può chiamare e logica di esecuzione.
I tool modificano direttamente il DB via SQLAlchemy.
"""
import json
from sqlalchemy.orm import Session

from models import DataSource, Record

# ── Definizioni tool per Claude ──────────────────────────────────────────────

TOOLS_CLAUDE = [
    {
        "name": "update_record",
        "description": (
            "Aggiorna il valore di un campo in un record CRM. "
            "Usalo quando l'utente vuole modificare i dati di un record specifico."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "record_id": {"type": "integer", "description": "ID del record da modificare"},
                "field": {"type": "string", "description": "Nome del campo da aggiornare"},
                "value": {"type": "string", "description": "Nuovo valore del campo"},
            },
            "required": ["record_id", "field", "value"],
        },
    },
    {
        "name": "delete_record",
        "description": (
            "Elimina definitivamente un record CRM. "
            "Usalo solo quando l'utente chiede esplicitamente di eliminare una riga/record."
        ),
        "input_schema": {
            "type": "object",
            "properties": {
                "record_id": {"type": "integer", "description": "ID del record da eliminare"},
            },
            "required": ["record_id"],
        },
    },
]


def execute_tool(name: str, inputs: dict, db: Session, owner_id: int) -> str:
    """Esegue un tool e restituisce una stringa con il risultato."""
    if name == "update_record":
        record = (
            db.query(Record)
            .join(DataSource, Record.data_source_id == DataSource.id)
            .filter(Record.id == inputs["record_id"], DataSource.owner_id == owner_id)
            .first()
        )
        if not record:
            return f"Errore: record {inputs['record_id']} non trovato o non autorizzato."
        data = dict(record.data)
        data[inputs["field"]] = inputs["value"]
        record.data = data
        db.commit()
        return f"✓ Campo '{inputs['field']}' aggiornato a '{inputs['value']}' nel record {inputs['record_id']}."

    elif name == "delete_record":
        record = (
            db.query(Record)
            .join(DataSource, Record.data_source_id == DataSource.id)
            .filter(Record.id == inputs["record_id"], DataSource.owner_id == owner_id)
            .first()
        )
        if not record:
            return f"Errore: record {inputs['record_id']} non trovato o non autorizzato."
        db.delete(record)
        db.commit()
        return f"✓ Record {inputs['record_id']} eliminato con successo."

    return f"Tool '{name}' non riconosciuto."
