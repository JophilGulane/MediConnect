"""
PDF prescription generator using ReportLab.
Call generate_prescription_pdf(prescription) → returns BytesIO.
"""
import io
from reportlab.lib.pagesizes import letter
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib import colors
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Paragraph, Table, TableStyle, Spacer, HRFlowable
from reportlab.lib.enums import TA_CENTER, TA_RIGHT


BRAND_BLUE = colors.HexColor('#0A6EBD')
BRAND_BLUE_LIGHT = colors.HexColor('#EFF6FF')
BRAND_TEAL = colors.HexColor('#00C9A7')
GREY = colors.HexColor('#4A6785')


def generate_prescription_pdf(prescription):
    """Generate a ReportLab PDF for a prescription. Returns a BytesIO buffer."""
    buffer = io.BytesIO()

    doc = SimpleDocTemplate(
        buffer,
        pagesize=letter,
        rightMargin=0.75 * inch,
        leftMargin=0.75 * inch,
        topMargin=0.75 * inch,
        bottomMargin=0.75 * inch,
    )

    styles = getSampleStyleSheet()
    story = []

    # ── Header ──────────────────────────────────────────
    header_style = ParagraphStyle(
        'header', parent=styles['Title'],
        fontSize=22, textColor=BRAND_BLUE, spaceAfter=4, alignment=TA_CENTER
    )
    sub_style = ParagraphStyle(
        'sub', parent=styles['Normal'],
        fontSize=10, textColor=GREY, alignment=TA_CENTER, spaceAfter=12
    )
    story.append(Paragraph('MediConnect', header_style))
    story.append(Paragraph('Digital Prescription', sub_style))
    story.append(HRFlowable(width='100%', thickness=2, color=BRAND_BLUE, spaceAfter=16))

    # ── Doctor & Patient Info ────────────────────────────
    doctor = prescription.doctor
    patient = prescription.patient

    try:
        dp = doctor.doctorprofile
        specialty_display = dp.get_specialty_display()
        license_number = dp.license_number
    except Exception:
        specialty_display = 'N/A'
        license_number = 'N/A'

    info_data = [
        [
            Paragraph(f'<b>Prescribing Doctor</b>', styles['Normal']),
            Paragraph(f'<b>Patient</b>', styles['Normal']),
        ],
        [
            Paragraph(f'Dr. {doctor.get_full_name()}<br/>{specialty_display}<br/>Lic. No: {license_number}', styles['Normal']),
            Paragraph(f'{patient.get_full_name()}<br/>Date Issued: {prescription.issued_at.strftime("%B %d, %Y")}', styles['Normal']),
        ],
    ]
    info_table = Table(info_data, colWidths=[3.25 * inch, 3.25 * inch])
    info_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BRAND_BLUE_LIGHT),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 9),
        ('TEXTCOLOR', (0, 0), (-1, 0), BRAND_BLUE),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#DBEAFE')),
        ('PADDING', (0, 0), (-1, -1), 10),
        ('VALIGN', (0, 0), (-1, -1), 'TOP'),
    ]))
    story.append(info_table)
    story.append(Spacer(1, 20))

    # ── Medicines Table ─────────────────────────────────
    heading_style = ParagraphStyle(
        'heading', parent=styles['Heading3'],
        textColor=BRAND_BLUE, fontSize=11, spaceAfter=8
    )
    story.append(Paragraph('Prescribed Medicines', heading_style))

    med_data = [['Medicine', 'Dosage', 'Frequency', 'Duration']]
    medicines = prescription.medicines or []
    for med in medicines:
        med_data.append([
            med.get('name', ''),
            med.get('dosage', ''),
            med.get('frequency', ''),
            med.get('duration', ''),
        ])
    if not medicines:
        med_data.append(['—', '—', '—', '—'])

    med_table = Table(med_data, colWidths=[2 * inch, 1.25 * inch, 1.5 * inch, 1.75 * inch])
    med_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), BRAND_BLUE),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, BRAND_BLUE_LIGHT]),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('PADDING', (0, 0), (-1, -1), 8),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    story.append(med_table)
    story.append(Spacer(1, 16))

    # ── Notes ────────────────────────────────────────────
    if prescription.notes:
        story.append(Paragraph('Doctor Notes', heading_style))
        story.append(Paragraph(prescription.notes, styles['Normal']))
        story.append(Spacer(1, 12))

    # ── Instructions ─────────────────────────────────────
    if prescription.instructions:
        story.append(Paragraph('Patient Instructions', heading_style))
        story.append(Paragraph(prescription.instructions, styles['Normal']))
        story.append(Spacer(1, 24))

    # ── Signature ────────────────────────────────────────
    story.append(HRFlowable(width='40%', thickness=1, color=BRAND_BLUE, spaceAfter=4))
    sig_style = ParagraphStyle('sig', parent=styles['Normal'], fontSize=9, textColor=GREY)
    story.append(Paragraph(f'Dr. {doctor.get_full_name()} &nbsp;&nbsp;|&nbsp;&nbsp; {specialty_display}', sig_style))
    story.append(Spacer(1, 8))
    story.append(Paragraph(
        '<i>This is a digital prescription generated by MediConnect. '
        'Always consult with your healthcare provider before making any medical decisions.</i>',
        ParagraphStyle('disclaimer', parent=styles['Normal'], fontSize=7, textColor=colors.grey)
    ))

    doc.build(story)
    buffer.seek(0)
    return buffer
