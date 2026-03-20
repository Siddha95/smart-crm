import math
import os

import pandas as pd

from crm.models import DataSource, Record


def clean_row(row: dict) -> dict:
    """Rimuove valori NaN e li sostituisce con None per compatibilità JSON."""
    return {
        k: (None if isinstance(v, float) and math.isnan(v) else v)
        for k, v in row.items()
    }


def load_excel(filepath: str) -> pd.DataFrame:
    if not os.path.exists(filepath):
        raise FileNotFoundError(f"File non trovato: {filepath}")
    try:
        return pd.read_excel(filepath)
    except Exception as e:
        raise ValueError(f"Impossibile leggere il file Excel: {e}")


def sync_data_source(name: str, label: str, columns: list, owner) -> DataSource:
    data_source, created = DataSource.objects.get_or_create(
        name=name,
        owner=owner,
        defaults={'label': label, 'columns': columns}
    )
    if not created:
        data_source.label = label
        data_source.columns = columns
        data_source.save()
    return data_source


def import_file(filepath: str, name: str, label: str, embedding_provider=None, owner=None) -> dict:
    df = load_excel(filepath)
    columns = list(df.columns)

    data_source = sync_data_source(name, label, columns, owner)

    deleted_count, _ = Record.objects.filter(data_source=data_source).delete()

    records = []
    for _, row in df.iterrows():
        data = clean_row(row.to_dict())
        embedding = embedding_provider.embed_record(data) if embedding_provider else None
        records.append(Record(data_source=data_source, data=data, embedding=embedding))

    Record.objects.bulk_create(records)

    return {'deleted': deleted_count, 'imported': len(records), 'data_source': data_source.name}
