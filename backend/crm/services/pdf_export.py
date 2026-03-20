"""
Responsabilità unica: esportare uno o più DataSource come file PDF.
Separato da excel_export.py per rispettare SRP.
"""
from io import BytesIO

from fpdf import FPDF
from fpdf.enums import Align, TableBordersLayout
from fpdf.fonts import FontFace

from crm.models import DataSource, Record

# ─── Costanti ────────────────────────────────────────────────────────────────
_FONT = 'Helvetica'
_MARGIN = 10
_MAX_COLS = 10

_HEADER_STYLE = FontFace(
    emphasis='BOLD',
    color=(255, 255, 255),
    fill_color=(34, 197, 94),
)
_ROW_ALT_COLOR = (245, 245, 245)


def _safe(text: str) -> str:
    """Sostituisce caratteri fuori Latin-1 per compatibilità con i font core di fpdf2."""
    return text.encode('latin-1', errors='replace').decode('latin-1')


def _write_sheet(pdf: FPDF, title: str, columns: list[str], rows: list[dict]) -> None:
    """Aggiunge una pagina al PDF con titolo e tabella con wrap automatico delle celle."""
    pdf.add_page()

    # Titolo
    pdf.set_font(_FONT, 'B', 14)
    pdf.set_text_color(40, 40, 40)
    pdf.cell(0, 10, _safe(title), new_x='LMARGIN', new_y='NEXT')
    pdf.ln(3)

    if not columns:
        pdf.set_font(_FONT, '', 10)
        pdf.cell(0, 8, 'Nessuna colonna definita.', new_x='LMARGIN', new_y='NEXT')
        return

    display_cols = columns[:_MAX_COLS]
    remaining = len(columns) - len(display_cols)

    # Tabella con wrap automatico e altezza riga variabile
    pdf.set_font(_FONT, '', 8)
    with pdf.table(
        headings_style=_HEADER_STYLE,
        borders_layout=TableBordersLayout.MINIMAL,
        cell_fill_color=_ROW_ALT_COLOR,
        cell_fill_mode='ROWS',
        line_height=6,
        text_align=Align.C,
        width=pdf.epw,
    ) as table:
        # Intestazione
        header = table.row()
        for col in display_cols:
            header.cell(_safe(col))

        # Dati
        for record_data in rows:
            row = table.row()
            for col in display_cols:
                val = str(record_data.get(col, '') or '')
                row.cell(_safe(val))

    if remaining > 0:
        pdf.ln(3)
        pdf.set_font(_FONT, 'I', 7)
        pdf.set_text_color(150, 150, 150)
        pdf.cell(
            0, 5,
            f'* {remaining} colonne aggiuntive non incluse nel PDF.',
            new_x='LMARGIN', new_y='NEXT',
        )


def _make_pdf() -> FPDF:
    pdf = FPDF(orientation='L', unit='mm', format='A4')
    pdf.set_margins(_MARGIN, _MARGIN, _MARGIN)
    pdf.set_auto_page_break(auto=True, margin=_MARGIN)
    return pdf


def export_datasource_pdf(data_source: DataSource) -> bytes:
    """Esporta un singolo DataSource come PDF e restituisce i byte raw."""
    records = Record.objects.filter(data_source=data_source).order_by('-is_favorite', 'id')
    pdf = _make_pdf()
    _write_sheet(pdf, data_source.label or data_source.name, data_source.columns, [r.data for r in records])
    buf = BytesIO()
    pdf.output(buf)
    return buf.getvalue()


def export_group_pdf(data_sources: list) -> bytes:
    """Esporta più DataSource come sezioni separate in un unico PDF."""
    pdf = _make_pdf()
    for ds in data_sources:
        records = Record.objects.filter(data_source=ds).order_by('-is_favorite', 'id')
        _write_sheet(pdf, ds.label or ds.name, ds.columns, [r.data for r in records])
    buf = BytesIO()
    pdf.output(buf)
    return buf.getvalue()
