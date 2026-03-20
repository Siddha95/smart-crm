import math
import os

import numpy as np
import pandas as pd
from django.db import transaction

from crm.models import DataSource, Record


def clean_row(row: dict) -> dict:
    """Converte i valori pandas/numpy in tipi Python nativi serializzabili in JSON."""
    result = {}
    for k, v in row.items():
        if v is pd.NaT or (isinstance(v, float) and math.isnan(v)):
            result[k] = None
        elif isinstance(v, pd.Timestamp):
            result[k] = v.isoformat()
        elif isinstance(v, np.integer):
            result[k] = int(v)
        elif isinstance(v, np.floating):
            result[k] = None if np.isnan(v) else float(v)
        elif isinstance(v, np.bool_):
            result[k] = bool(v)
        else:
            result[k] = v
    return result


def get_sheet_names(filepath: str) -> list[str]:
    """Restituisce i nomi dei fogli presenti nel file Excel."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File non trovato: {filepath}")
    try:
        xl = pd.ExcelFile(filepath)
        return xl.sheet_names
    except Exception as e:
        raise ValueError(f"Impossibile leggere il file Excel: {e}")


def load_sheet(filepath: str, sheet_name: str) -> pd.DataFrame:
    """Carica un singolo foglio dal file Excel."""
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File non trovato: {filepath}")
    try:
        return pd.read_excel(filepath, sheet_name=sheet_name)
    except Exception as e:
        raise ValueError(f"Impossibile leggere il foglio '{sheet_name}': {e}")


def _sync_data_source(name: str, label: str, columns: list, source_file: str, owner) -> DataSource:
    """Crea o aggiorna un DataSource. source_file raggruppa i fogli dello stesso file."""
    data_source, created = DataSource.objects.get_or_create(
        name=name,
        owner=owner,
        defaults={'label': label, 'columns': columns, 'source_file': source_file}
    )
    if not created:
        data_source.label = label
        data_source.columns = columns
        data_source.source_file = source_file
        data_source.save()
    return data_source


def _import_sheet(filepath: str, sheet_name: str, source_file: str, embedding_provider, owner) -> dict:
    """Importa un singolo foglio come DataSource."""
    df = load_sheet(filepath, sheet_name)
    columns = list(df.columns)

    # Nome interno univoco: {source_file}_{sheet_name}
    ds_name = f"{source_file}_{sheet_name}"
    data_source = _sync_data_source(ds_name, sheet_name, columns, source_file, owner)

    records = []
    for _, row in df.iterrows():
        data = clean_row(row.to_dict())
        embedding = embedding_provider.embed_record(data) if embedding_provider else None
        records.append(Record(data_source=data_source, data=data, embedding=embedding))

    with transaction.atomic():
        deleted_count, _ = Record.objects.filter(data_source=data_source).delete()
        Record.objects.bulk_create(records)

    return {
        'sheet': sheet_name,
        'data_source_id': data_source.id,
        'deleted': deleted_count,
        'imported': len(records),
    }


def preview_sheets(filepath: str, max_rows: int = 5) -> list[dict]:
    """Restituisce un'anteprima dei primi N record per ogni foglio, senza importare."""
    sheet_names = get_sheet_names(filepath)
    result = []
    for sheet_name in sheet_names:
        df = load_sheet(filepath, sheet_name)
        columns = list(df.columns)
        rows = [clean_row(row.to_dict()) for _, row in df.head(max_rows).iterrows()]
        result.append({'name': sheet_name, 'columns': columns, 'rows': rows})
    return result


def import_all_sheets(filepath: str, source_file: str, embedding_provider=None, owner=None) -> dict:
    """Importa tutti i fogli del file Excel, creando un DataSource per ogni foglio."""
    sheet_names = get_sheet_names(filepath)
    results = []
    for sheet_name in sheet_names:
        result = _import_sheet(filepath, sheet_name, source_file, embedding_provider, owner)
        results.append(result)

    return {
        'source_file': source_file,
        'sheets': results,
        'total_imported': sum(r['imported'] for r in results),
    }
