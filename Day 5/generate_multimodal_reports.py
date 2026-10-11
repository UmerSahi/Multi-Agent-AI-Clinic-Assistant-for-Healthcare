"""
Multimodal Clinical Lab Report Generator (PDF & High-Resolution Image)
Generates authentic clinical documents for the 30 benchmark lab reports
using ReportLab (for PDF) and PyMuPDF (for PNG images).
"""

import os
import json
from pathlib import Path
from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle

try:
    import fitz  # pymupdf
except ImportError:
    fitz = None

DAY5_DIR = Path(__file__).resolve().parent
ROOT_DIR = DAY5_DIR.parent
DAY2_LAB_DIR = ROOT_DIR / "Day 2" / "lab_reports"
GROUND_TRUTH_FILE = DAY2_LAB_DIR / "ground_truth_30_reports.json"

PDF_DIR = DAY5_DIR / "lab_reports_pdf"
IMG_DIR = DAY5_DIR / "lab_reports_img"

PDF_DIR.mkdir(parents=True, exist_ok=True)
IMG_DIR.mkdir(parents=True, exist_ok=True)


def create_pdf_report(report_data: dict, output_path: Path):
    """Generates a professional hospital lab report PDF."""
    doc = SimpleDocTemplate(
        str(output_path),
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()
    title_style = ParagraphStyle(
        "ClinicTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=18,
        leading=22,
        textColor=colors.HexColor("#0f172a"),
        alignment=1
    )
    subtitle_style = ParagraphStyle(
        "ClinicSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=12,
        textColor=colors.HexColor("#64748b"),
        alignment=1
    )
    section_style = ParagraphStyle(
        "SectionHeader",
        parent=styles["Heading3"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#0284c7")
    )
    meta_style = ParagraphStyle(
        "MetaText",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1e293b")
    )

    story = []

    # Hospital Header
    story.append(Paragraph("CITY CARE CLINICS & DIAGNOSTICS", title_style))
    story.append(Paragraph("Clinical Pathology & Diagnostic Testing • Gulberg Lahore • UAN: (042) 111-222-333", subtitle_style))
    story.append(Spacer(1, 14))

    # Meta Table
    meta_data = [
        [
            Paragraph(f"<b>Patient Name:</b> {report_data['patient_name']}", meta_style),
            Paragraph(f"<b>Report Reference:</b> {report_data['report_id']}", meta_style)
        ],
        [
            Paragraph(f"<b>MRN / Patient ID:</b> {report_data['mrn']}", meta_style),
            Paragraph(f"<b>Collection Date:</b> {report_data.get('collection_date', '2026-09-06')}", meta_style)
        ],
        [
            Paragraph(f"<b>Panel Type:</b> {report_data['panel']}", meta_style),
            Paragraph("<b>Reporting Lab:</b> Main Clinical Pathology Lab", meta_style)
        ]
    ]
    meta_table = Table(meta_data, colWidths=[270, 270])
    meta_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ("BOX", (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ("VALIGN", (0, 0), (-1, -1), "MIDDLE"),
        ("TOPPADDING", (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
    ]))
    story.append(meta_table)
    story.append(Spacer(1, 18))

    # Test Results Header
    story.append(Paragraph("OBSERVED INVESTIGATION FINDINGS", section_style))
    story.append(Spacer(1, 8))

    # Test Table
    table_rows = [
        ["INVESTIGATION", "OBSERVED VALUE", "UNIT", "REFERENCE RANGE", "STATUS"]
    ]

    for t in report_data["tests"]:
        val = t["numeric_value"]
        low = t["reference_range_low"]
        high = t["reference_range_high"]
        flag = t["flag"]

        status_text = f"[{flag}]"
        table_rows.append([
            t["test_name"],
            f"{val:.2f}" if isinstance(val, float) and "." in str(val) else str(val),
            t.get("unit", ""),
            f"{low} - {high}",
            status_text
        ])

    test_table = Table(table_rows, colWidths=[180, 95, 80, 115, 70])
    test_table.setStyle(TableStyle([
        ("BACKGROUND", (0, 0), (-1, 0), colors.HexColor("#0f172a")),
        ("TEXTCOLOR", (0, 0), (-1, 0), colors.white),
        ("FONTNAME", (0, 0), (-1, 0), "Helvetica-Bold"),
        ("FONTSIZE", (0, 0), (-1, 0), 9),
        ("BOTTOMPADDING", (0, 0), (-1, 0), 7),
        ("GRID", (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ("FONTNAME", (0, 1), (-1, -1), "Helvetica"),
        ("FONTSIZE", (0, 1), (-1, -1), 9),
        ("ALIGN", (1, 0), (-1, -1), "CENTER"),
        ("TOPPADDING", (0, 1), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 1), (-1, -1), 5),
    ]))

    story.append(test_table)
    story.append(Spacer(1, 24))

    # Footer Disclaimer
    disclaimer_style = ParagraphStyle(
        "Disclaimer",
        parent=styles["Normal"],
        fontName="Helvetica-Oblique",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#64748b")
    )
    story.append(Paragraph(
        "Confidential Medical Diagnostic Document. Results must be interpreted in conjunction with complete clinical history. "
        "Verified by Consultant Pathologist Dr. Maryam Naveed (PMDC-41298-P).",
        disclaimer_style
    ))

    doc.build(story)


def convert_pdf_to_image(pdf_path: Path, output_path: Path):
    """Renders the first page of the PDF to a high-res PNG image."""
    if not fitz:
        return
    doc = fitz.open(str(pdf_path))
    if len(doc) > 0:
        page = doc[0]
        pix = page.get_pixmap(dpi=150)
        pix.save(str(output_path))


def generate_all_30():
    if not GROUND_TRUTH_FILE.exists():
        print(f"Error: {GROUND_TRUTH_FILE} not found.")
        return

    with open(GROUND_TRUTH_FILE, "r", encoding="utf-8") as f:
        reports = json.load(f)

    print(f"Generating 30 clinical PDFs and PNG images...")
    for i, rpt in enumerate(reports, start=1):
        rpt_id = rpt["report_id"]
        pdf_path = PDF_DIR / f"{rpt_id}.pdf"
        img_path = IMG_DIR / f"{rpt_id}.png"

        create_pdf_report(rpt, pdf_path)
        convert_pdf_to_image(pdf_path, img_path)

    print(f"Successfully generated 30 PDFs in {PDF_DIR.name} and 30 Images in {IMG_DIR.name}!")


if __name__ == "__main__":
    generate_all_30()
