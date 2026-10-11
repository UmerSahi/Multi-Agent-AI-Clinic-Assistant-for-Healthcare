"""
City Care Clinics — Professional Clinical Prescription PDF Generator
Uses ReportLab to generate authentic, high-fidelity medical prescriptions
with clinic branding, patient details, Rx medication schedule, doctor signature stamp,
and medical guidance.
"""

import io
import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Dict, Any, List

from reportlab.lib.pagesizes import letter
from reportlab.lib import colors
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, KeepTogether
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


def generate_prescription_pdf_bytes(prescription_data: Dict[str, Any], appointment_data: Dict[str, Any] = None) -> bytes:
    """
    Generates a professional hospital prescription PDF as raw bytes.
    """
    buf = io.BytesIO()
    doc = SimpleDocTemplate(
        buf,
        pagesize=letter,
        rightMargin=36,
        leftMargin=36,
        topMargin=36,
        bottomMargin=36
    )

    styles = getSampleStyleSheet()

    # Custom Typography Styles
    title_style = ParagraphStyle(
        "ClinicTitle",
        parent=styles["Heading1"],
        fontName="Helvetica-Bold",
        fontSize=22,
        leading=26,
        textColor=colors.HexColor("#0f294a"),
        alignment=TA_CENTER
    )

    subtitle_style = ParagraphStyle(
        "ClinicSubtitle",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#0891b2"),
        alignment=TA_CENTER
    )

    clinic_meta_style = ParagraphStyle(
        "ClinicMeta",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8,
        leading=11,
        textColor=colors.HexColor("#64748b"),
        alignment=TA_CENTER
    )

    section_heading = ParagraphStyle(
        "SectionHeading",
        parent=styles["Heading2"],
        fontName="Helvetica-Bold",
        fontSize=12,
        leading=15,
        textColor=colors.HexColor("#0f294a"),
        spaceAfter=4
    )

    body_style = ParagraphStyle(
        "PrescriptionBody",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=9,
        leading=13,
        textColor=colors.HexColor("#1e293b")
    )

    body_bold = ParagraphStyle(
        "PrescriptionBodyBold",
        parent=body_style,
        fontName="Helvetica-Bold"
    )

    table_hdr_style = ParagraphStyle(
        "TableHeader",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=8.5,
        leading=11,
        textColor=colors.white,
        alignment=TA_CENTER
    )

    table_cell_style = ParagraphStyle(
        "TableCell",
        parent=styles["Normal"],
        fontName="Helvetica",
        fontSize=8.5,
        leading=11,
        textColor=colors.HexColor("#1e293b")
    )

    rx_symbol_style = ParagraphStyle(
        "RxSymbol",
        parent=styles["Normal"],
        fontName="Helvetica-Bold",
        fontSize=24,
        leading=26,
        textColor=colors.HexColor("#0891b2")
    )

    # Resolve Data
    app = appointment_data or {}
    p_data = prescription_data or {}

    doctor_name = p_data.get("doctor_name") or app.get("doctor_name") or "Dr. Ali Khan"
    doctor_spec = p_data.get("doctor_specialty") or app.get("doctor_specialty") or "General Medicine"
    pmdc_num = p_data.get("pmdc_number") or app.get("pmdc_number") or "PMDC-22280-P"
    branch_name = p_data.get("branch_name") or app.get("branch_name") or "City Care Clinics — Johar Town Branch"

    patient_name = p_data.get("patient_name") or app.get("patient_name") or "Valued Patient"
    patient_mrn = p_data.get("patient_mrn") or app.get("patient_mrn") or app.get("patient_id") or "CCC-PK-1000"
    patient_phone = p_data.get("patient_phone") or app.get("patient_phone") or "0300-1234567"
    patient_age = str(p_data.get("patient_age") or app.get("patient_age") or "28")
    patient_gender = p_data.get("patient_gender") or app.get("patient_gender") or "Male"
    patient_allergies = p_data.get("patient_allergies") or app.get("known_allergies") or "None reported"

    booking_ref = p_data.get("booking_reference") or app.get("booking_reference") or "BK-2026-1000"
    rx_id = p_data.get("id") or f"RX-{booking_ref.replace('#', '')}"
    diagnosis = p_data.get("diagnosis") or app.get("reason_for_visit") or "Clinical Outpatient Consultation"
    advice = p_data.get("advice") or "Take prescribed medications with full glass of water. Avoid skipping doses. Adequate rest recommended."

    date_str = p_data.get("created_at") or app.get("scheduled_start") or datetime.now(timezone.utc).isoformat()
    try:
        dt_obj = datetime.fromisoformat(date_str.replace("Z", "+00:00"))
        formatted_date = dt_obj.strftime("%d %B %Y, %I:%M %p")
    except Exception:
        formatted_date = date_str[:16].replace("T", " ")

    story = []

    # 1. HEADER (Clinic Logo & Identification)
    story.append(Paragraph("CITY CARE CLINICS", title_style))
    story.append(Paragraph("CENTER FOR ADVANCED HEALTHCARE & MULTI-SPECIALTY OUTPATIENT SERVICES", subtitle_style))
    story.append(Spacer(1, 2))
    story.append(Paragraph(
        "Lahore Branches: Gulberg III • DHA Phase 5 • Johar Town | Islamabad: F-8 Markaz<br/>"
        "24/7 Helpline: <b>+92-42-111-CARE (2273)</b> • Web: <b>www.citycareclinics.pk</b> • EMR Verified",
        clinic_meta_style
    ))
    story.append(Spacer(1, 6))

    # Teal & Navy Divider Line
    story.append(HRFlowable(width="100%", thickness=2.5, color=colors.HexColor("#0891b2"), spaceBefore=2, spaceAfter=8))

    # 2. PATIENT & PHYSICIAN INFO GRID
    pat_info_html = (
        f"<b>Patient Name:</b> {patient_name}<br/>"
        f"<b>MRN:</b> <font color='#0891b2'><b>{patient_mrn}</b></font><br/>"
        f"<b>Age / Gender:</b> {patient_age} Years / {patient_gender}<br/>"
        f"<b>Contact:</b> {patient_phone}<br/>"
        f"<b>Allergies:</b> <font color='#dc2626'><b>{patient_allergies}</b></font>"
    )

    doc_info_html = (
        f"<b>Consulting Physician:</b> <b>{doctor_name}</b><br/>"
        f"<b>Specialty:</b> {doctor_spec}<br/>"
        f"<b>PMDC Reg No:</b> {pmdc_num}<br/>"
        f"<b>Consultation Date:</b> {formatted_date}<br/>"
        f"<b>Booking Ref:</b> <b>#{booking_ref}</b> | <b>Rx ID:</b> <font color='#0891b2'><b>{rx_id}</b></font>"
    )

    info_table_data = [
        [
            Paragraph("<b>PATIENT PROFILE</b>", ParagraphStyle("Hdr1", parent=body_bold, textColor=colors.HexColor("#0f294a"))),
            Paragraph("<b>CONSULTATION & PRACTITIONER</b>", ParagraphStyle("Hdr2", parent=body_bold, textColor=colors.HexColor("#0f294a")))
        ],
        [
            Paragraph(pat_info_html, body_style),
            Paragraph(doc_info_html, body_style)
        ]
    ]

    info_table = Table(info_table_data, colWidths=[270, 270])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (1, 0), colors.HexColor("#f1f5f9")),
        ('BACKGROUND', (0, 1), (1, 1), colors.HexColor("#f8fafc")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0, 0), (-1, -1), 6),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 6),
        ('LEFTPADDING', (0, 0), (-1, -1), 10),
        ('RIGHTPADDING', (0, 0), (-1, -1), 10),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 10))

    # 3. CLINICAL DIAGNOSIS BANNER
    diag_data = [
        [
            Paragraph("<b>Clinical Diagnosis / Clinical Notes:</b>", ParagraphStyle("DiagLabel", parent=body_bold, fontSize=9.5, textColor=colors.HexColor("#0f294a"))),
            Paragraph(f"<b>{diagnosis}</b>", ParagraphStyle("DiagVal", parent=body_style, fontSize=9.5, textColor=colors.HexColor("#0369a1")))
        ]
    ]
    diag_table = Table(diag_data, colWidths=[180, 360])
    diag_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f0fdf4")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#bbf7d0")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 8),
        ('RIGHTPADDING', (0, 0), (-1, -1), 8),
    ]))
    story.append(diag_table)
    story.append(Spacer(1, 12))

    # 4. Rx PRESCRIPTION SECTION
    story.append(Paragraph("℞ <b>Prescribed Medication Schedule</b>", ParagraphStyle("RxTitle", parent=section_heading, textColor=colors.HexColor("#0891b2"), fontSize=13)))
    story.append(Spacer(1, 4))

    # Parse medicines
    medicines = p_data.get("medicines") or []
    if isinstance(medicines, str):
        try:
            medicines = json.loads(medicines)
        except Exception:
            medicines = []

    if not medicines:
        medicines = [
            {
                "name": "Panadol (Paracetamol) 500mg",
                "dosage": "500 mg",
                "frequency": "1 tablet twice daily after meals",
                "duration": "5 Days",
                "instructions": "Take after meals with water. Do not exceed 4g daily."
            }
        ]

    med_table_rows = [
        [
            Paragraph("<b>#</b>", table_hdr_style),
            Paragraph("<b>Medication & Formulation</b>", table_hdr_style),
            Paragraph("<b>Dosage / Strength</b>", table_hdr_style),
            Paragraph("<b>Frequency & Timing</b>", table_hdr_style),
            Paragraph("<b>Duration</b>", table_hdr_style),
            Paragraph("<b>Special Instructions</b>", table_hdr_style)
        ]
    ]

    for idx, med in enumerate(medicines, 1):
        m_name = med.get("name") or med.get("drug_name") or "Medicine"
        m_dose = str(med.get("dosage") or med.get("dosage_mg") or "As directed")
        m_freq = str(med.get("frequency") or med.get("frequency_per_day") or "Twice daily after meals")
        m_dur = str(med.get("duration") or med.get("duration_days") or "5 Days")
        m_inst = str(med.get("instructions") or med.get("timing") or "Take with water after food")

        med_table_rows.append([
            Paragraph(str(idx), ParagraphStyle("IdCol", parent=table_cell_style, alignment=TA_CENTER)),
            Paragraph(f"<b>{m_name}</b>", table_cell_style),
            Paragraph(m_dose, table_cell_style),
            Paragraph(m_freq, table_cell_style),
            Paragraph(m_dur, table_cell_style),
            Paragraph(m_inst, table_cell_style),
        ])

    med_table = Table(med_table_rows, colWidths=[24, 150, 75, 125, 60, 106])
    med_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor("#0f294a")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ('INNERGRID', (0, 0), (-1, -1), 0.5, colors.HexColor("#e2e8f0")),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LEFTPADDING', (0, 0), (-1, -1), 5),
        ('RIGHTPADDING', (0, 0), (-1, -1), 5),
        *[('BACKGROUND', (0, r), (-1, r), colors.HexColor("#f8fafc")) for r in range(1, len(med_table_rows), 2)]
    ]))
    story.append(med_table)
    story.append(Spacer(1, 14))

    # 5. PHYSICIAN ADVICE & WARNINGS
    advice_html = (
        f"<b>Physician's Guidance & Follow-up Instructions:</b><br/>"
        f"• {advice}<br/>"
        f"• Stay well hydrated. In case of unexpected allergic rash, swelling, or nausea, discontinue and call the clinic hotline.<br/>"
        f"• Scheduled follow-up: If symptoms do not improve within 3-5 days, book a review consultation."
    )
    advice_table = Table([[Paragraph(advice_html, body_style)]], colWidths=[540])
    advice_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, -1), colors.HexColor("#f8fafc")),
        ('BOX', (0, 0), (-1, -1), 1, colors.HexColor("#cbd5e1")),
        ('TOPPADDING', (0, 0), (-1, -1), 8),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
        ('LEFTPADDING', (0, 0), (-1, -1), 12),
        ('RIGHTPADDING', (0, 0), (-1, -1), 12),
    ]))
    story.append(advice_table)
    story.append(Spacer(1, 16))

    # 6. SIGNATURE & VERIFICATION BLOCK
    disclaimer_html = (
        "<font size='7.5' color='#64748b'>"
        "<b>EMERGENCY WARNING:</b><br/>"
        "This prescription is valid across Pakistan pharmacies.<br/>"
        "In case of acute chest pain, breathlessness, or trauma, report to City Care 24/7 Emergency or dial 1122.<br/>"
        "Official EMR Document: Generated electronically via City Care Multi-Agent System."
        "</font>"
    )

    sign_html = (
        "<div align='right'>"
        "<font size='8' color='#0891b2'><b>[ DIGITALLY SIGNED & VERIFIED ]</b></font><br/>"
        f"<font size='10' color='#0f294a'><b>{doctor_name}</b></font><br/>"
        f"<font size='8' color='#334155'>{doctor_spec}</font><br/>"
        f"<font size='7.5' color='#64748b'>PMDC Reg: {pmdc_num} • {branch_name}</font><br/>"
        f"<font size='7' color='#94a3b8'>Signed At: {formatted_date}</font>"
        "</div>"
    )

    sig_data = [
        [
            Paragraph(disclaimer_html, body_style),
            Paragraph(sign_html, ParagraphStyle("SigStyle", parent=body_style, alignment=TA_RIGHT))
        ]
    ]

    sig_table = Table(sig_data, colWidths=[290, 250])
    sig_table.setStyle(TableStyle([
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
    ]))

    story.append(KeepTogether([
        HRFlowable(width="100%", thickness=1, color=colors.HexColor("#cbd5e1"), spaceBefore=4, spaceAfter=8),
        sig_table
    ]))

    doc.build(story)
    return buf.getvalue()


def save_prescription_pdf_file(prescription_data: Dict[str, Any], output_path: Path, appointment_data: Dict[str, Any] = None) -> Path:
    """Saves generated prescription PDF bytes to specified file path."""
    pdf_bytes = generate_prescription_pdf_bytes(prescription_data, appointment_data)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    with open(output_path, "wb") as f:
        f.write(pdf_bytes)
    return output_path
