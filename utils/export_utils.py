"""
utils/export_utils.py
=====================
Export Utilities for Generating Reports in CSV and PDF Formats.

College Viva Concepts:
1. Streaming Tabular Data: CSV export uses Python's native 'csv' module for fast,
   universal spreadsheet compatibility.
2. PDF Generation with ReportLab: Programmatically constructs styled PDF documents
   using Flowables (Paragraph, Table, Spacer) and Document Templates.
"""

import csv
from datetime import datetime
from pathlib import Path
from typing import Sequence, Any, Union

try:
    from reportlab.lib.pagesizes import letter
    from reportlab.lib import colors
    from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    REPORTLAB_AVAILABLE = True
except ImportError:
    REPORTLAB_AVAILABLE = False


def export_to_csv(rows: Sequence[Sequence[Any]], headers: Sequence[str], path: Union[str, Path]) -> str:
    """
    Exports a table of headers and rows into a CSV file.

    Args:
        rows: Sequence of data rows (lists or tuples).
        headers: Column header names.
        path: Target file path.

    Returns:
        str: Absolute path of the generated CSV file.
    """
    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)

    with open(target, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        writer.writerow(headers)
        for row in rows:
            # Convert values to strings or clean representations
            formatted_row = [str(val) if val is not None else "" for val in row]
            writer.writerow(formatted_row)

    return str(target.resolve())


def export_to_pdf(
    title: str, rows: Sequence[Sequence[Any]], headers: Sequence[str], path: Union[str, Path]
) -> str:
    """
    Generates a clean, professional PDF report table using ReportLab.

    Args:
        title: Report header title.
        rows: Sequence of tabular rows.
        headers: Column header titles.
        path: Target file path for the PDF.

    Returns:
        str: Absolute path of the generated PDF file.

    Raises:
        RuntimeError: If reportlab is not installed.
    """
    if not REPORTLAB_AVAILABLE:
        raise RuntimeError("reportlab is not installed. Please run: pip install reportlab")

    target = Path(path)
    target.parent.mkdir(parents=True, exist_ok=True)

    # Setup Document
    doc = SimpleDocTemplate(
        str(target),
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36,
    )
    styles = getSampleStyleSheet()

    title_style = ParagraphStyle(
        "ReportTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#1e3a8a"),
        alignment=0,  # Left
    )
    subtitle_style = ParagraphStyle(
        "ReportSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        textColor=colors.HexColor("#64748b"),
        alignment=0,
    )
    cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=10,
        textColor=colors.HexColor("#1e293b"),
    )
    header_cell_style = ParagraphStyle(
        "HeaderCell",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8,
        leading=10,
        textColor=colors.white,
    )

    story = []

    # 1. Title Banner
    story.append(Paragraph(f"Canteen Management System - {title}", title_style))
    gen_time = datetime.now().strftime("%Y-%m-%d %I:%M %p")
    story.append(Paragraph(f"Generated on: {gen_time} | Total Rows: {len(rows)}", subtitle_style))
    story.append(Spacer(1, 14))

    # 2. Table Data Preparation
    table_data = []

    # Add header row
    header_row = [Paragraph(str(h), header_cell_style) for h in headers]
    table_data.append(header_row)

    # Add data rows
    if rows:
        for r in rows:
            data_row = [Paragraph(str(val) if val is not None else "-", cell_style) for val in r]
            table_data.append(data_row)
    else:
        # If no data returned
        empty_msg = [Paragraph("<i>No matching records found for this period.</i>", cell_style)] * len(headers)
        table_data.append(empty_msg)

    # 3. Create and Style Table
    table = Table(table_data, repeatRows=1)
    table_style = TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#1e3a8a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("ALIGN", (0, 0), (-1, -1), "LEFT"),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("ROWBACKGROUNDS", (0, 1), (-1, -1), [colors.white, colors.HexColor("#f8fafc")]),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
    ])
    table.setStyle(table_style)
    story.append(table)

    # Build PDF
    doc.build(story)
    return str(target.resolve())
