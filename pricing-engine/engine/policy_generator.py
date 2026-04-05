"""
Policy document PDF generator.

Generates a branded Leadway Householder Insurance policy document
after successful payment.
"""

import io
import datetime
import random
import string
from pathlib import Path
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.lib.units import mm
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, HRFlowable, Image
)
from reportlab.lib.enums import TA_CENTER, TA_LEFT, TA_RIGHT


ORANGE = HexColor('#FF6B22')
DARK = HexColor('#333333')
GRAY = HexColor('#888888')
LIGHT_GRAY = HexColor('#F5F5F5')
WHITE = HexColor('#FFFFFF')


def generate_policy_number():
    year = datetime.datetime.now().strftime('%Y')
    seq = ''.join(random.choices(string.digits, k=6))
    return f"HH{year}{seq}LA"


def generate_policy_pdf(data: dict) -> bytes:
    """Generate a branded policy document PDF and return bytes."""

    buffer = io.BytesIO()
    doc = SimpleDocTemplate(
        buffer, pagesize=A4,
        leftMargin=25*mm, rightMargin=25*mm,
        topMargin=20*mm, bottomMargin=20*mm,
    )

    styles = getSampleStyleSheet()

    # Custom styles
    styles.add(ParagraphStyle(
        'BrandTitle', parent=styles['Title'],
        fontName='Helvetica-Bold', fontSize=22, textColor=ORANGE,
        spaceAfter=4*mm, alignment=TA_CENTER,
    ))
    styles.add(ParagraphStyle(
        'BrandSubtitle', parent=styles['Normal'],
        fontName='Helvetica', fontSize=11, textColor=DARK,
        alignment=TA_CENTER, spaceAfter=8*mm,
    ))
    styles.add(ParagraphStyle(
        'SectionHead', parent=styles['Heading2'],
        fontName='Helvetica-Bold', fontSize=13, textColor=ORANGE,
        spaceBefore=6*mm, spaceAfter=3*mm,
    ))
    styles.add(ParagraphStyle(
        'FieldLabel', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=9, textColor=GRAY,
    ))
    styles.add(ParagraphStyle(
        'FieldValue', parent=styles['Normal'],
        fontName='Helvetica-Bold', fontSize=11, textColor=DARK,
    ))
    styles.add(ParagraphStyle(
        'PolicyBody', parent=styles['Normal'],
        fontName='Helvetica', fontSize=10, textColor=DARK,
        leading=14, spaceAfter=2*mm,
    ))
    styles.add(ParagraphStyle(
        'SmallText', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8, textColor=GRAY,
        leading=11,
    ))
    styles.add(ParagraphStyle(
        'FooterText', parent=styles['Normal'],
        fontName='Helvetica', fontSize=8, textColor=GRAY,
        alignment=TA_CENTER,
    ))

    elements = []

    # --- HEADER WITH LOGO ---
    logo_path = Path(__file__).parent.parent / "frontend" / "leadway-logo.jpeg"
    if logo_path.exists():
        logo = Image(str(logo_path), width=28*mm, height=28*mm)
        header_data = [[
            logo,
            Paragraph(
                '<font size="20" color="#FF6B22"><b>LEADWAY ASSURANCE</b></font><br/>'
                '<font size="10" color="#333333">HOUSEOWNERS &amp; HOUSEHOLDERS INSURANCE POLICY</font>',
                ParagraphStyle('HeaderRight', parent=styles['Normal'], alignment=TA_RIGHT, leading=16)
            )
        ]]
        header_table = Table(header_data, colWidths=[35*mm, 125*mm])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
            ('ALIGN', (0, 0), (0, 0), 'LEFT'),
            ('ALIGN', (1, 0), (1, 0), 'RIGHT'),
        ]))
        elements.append(header_table)
    else:
        elements.append(Paragraph("LEADWAY ASSURANCE", styles['BrandTitle']))
        elements.append(Paragraph("HOUSEOWNERS & HOUSEHOLDERS INSURANCE POLICY", styles['BrandSubtitle']))

    # Orange line
    elements.append(HRFlowable(
        width="100%", thickness=2, color=ORANGE,
        spaceBefore=4*mm, spaceAfter=6*mm,
    ))

    # --- POLICY DETAILS TABLE ---
    policy_number = data.get('policy_number', generate_policy_number())
    issue_date = datetime.datetime.now().strftime('%d %B %Y')
    duration = data.get('duration_months', 12)
    start_date = datetime.datetime.now()
    end_date = start_date + datetime.timedelta(days=duration * 30)

    elements.append(Paragraph("POLICY DETAILS", styles['SectionHead']))

    details_data = [
        ['POLICY HOLDER', data.get('customer_name', '').upper()],
        ['POLICY NUMBER', policy_number],
        ['DATE OF ISSUE', issue_date],
        ['COVER FROM', start_date.strftime('%d %B %Y')],
        ['COVER TO', end_date.strftime('%d %B %Y')],
        ['PRODUCT', 'HOUSEHOLDER'],
        ['CLIENT TYPE', data.get('client_type', 'INDIVIDUAL').upper()],
        ['COVER TYPE', data.get('cover_type', 'STANDARD').upper()],
        ['BRANCH', data.get('location', 'LAGOS').upper()],
        ['CURRENCY', 'NGN'],
        ['POLICY FREQUENCY', 'ANNUALLY' if duration == 12 else f'{duration} MONTHS'],
    ]

    detail_table = Table(details_data, colWidths=[55*mm, 105*mm])
    detail_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (0, -1), GRAY),
        ('TEXTCOLOR', (1, 0), (1, -1), DARK),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, HexColor('#EEEEEE')),
        ('LINEBELOW', (0, -1), (-1, -1), 1, ORANGE),
        ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
    ]))
    elements.append(detail_table)
    elements.append(Spacer(1, 6*mm))

    # --- INSURED PROPERTY ---
    elements.append(Paragraph("INSURED PROPERTY", styles['SectionHead']))

    address = data.get('address', 'As declared in proposal')
    elements.append(Paragraph(f"<b>Address:</b> {address}", styles['PolicyBody']))

    building_si = data.get('building_sum_insured', 0)
    content_si = data.get('content_sum_insured', 0)
    total_si = building_si + content_si

    si_data = [
        ['ITEM', 'SUM INSURED (NGN)'],
        ['Building', f'{building_si:,.2f}'],
        ['Household Contents', f'{content_si:,.2f}'],
        ['TOTAL SUM INSURED', f'{total_si:,.2f}'],
    ]

    si_table = Table(si_data, colWidths=[80*mm, 80*mm])
    si_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -2), 'Helvetica'),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('BACKGROUND', (0, 0), (-1, 0), ORANGE),
        ('TEXTCOLOR', (0, -1), (-1, -1), ORANGE),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 5),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ('LINEBELOW', (0, 1), (-1, -2), 0.5, HexColor('#EEEEEE')),
        ('LINEABOVE', (0, -1), (-1, -1), 1, ORANGE),
        ('GRID', (0, 0), (-1, 0), 0.5, ORANGE),
    ]))
    elements.append(si_table)
    elements.append(Spacer(1, 4*mm))

    # --- BUILDING PHOTOS ---
    building_photos = data.get('building_photos', [])
    if building_photos:
        elements.append(Paragraph("BUILDING PHOTOGRAPHS", styles['SectionHead']))
        photo_row = []
        for i, photo_data in enumerate(building_photos[:4]):
            try:
                # photo_data is a base64 data URL: "data:image/jpeg;base64,..."
                if ',' in photo_data:
                    header, b64 = photo_data.split(',', 1)
                else:
                    b64 = photo_data
                import base64
                img_bytes = base64.b64decode(b64)
                img_buffer = io.BytesIO(img_bytes)
                photo_img = Image(img_buffer, width=36*mm, height=28*mm)
                photo_row.append(photo_img)
            except Exception:
                pass

        if photo_row:
            # Arrange photos in a row (max 4)
            photo_table = Table([photo_row], colWidths=[40*mm] * len(photo_row))
            photo_table.setStyle(TableStyle([
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('VALIGN', (0, 0), (-1, -1), 'MIDDLE'),
                ('TOPPADDING', (0, 0), (-1, -1), 2),
                ('BOTTOMPADDING', (0, 0), (-1, -1), 2),
            ]))
            elements.append(photo_table)
        elements.append(Spacer(1, 4*mm))

    # --- COVERAGES ---
    elements.append(Paragraph("COVERAGES INCLUDED", styles['SectionHead']))

    coverages = data.get('coverages', [])
    for cov in coverages:
        elements.append(Paragraph(f"• {cov}", styles['PolicyBody']))

    elements.append(Spacer(1, 4*mm))

    # --- PREMIUM BREAKDOWN ---
    elements.append(Paragraph("PREMIUM BREAKDOWN", styles['SectionHead']))

    premium_data = [['ITEM', 'AMOUNT (NGN)']]

    section_items = [
        ('Building Premium', data.get('building_premium', 0)),
        ('Content Premium', data.get('content_premium', 0)),
        ('Accidental Damage Premium', data.get('accidental_damage_premium', 0)),
        ('All Risks Premium', data.get('all_risks_premium', 0)),
        ('Personal Accident Premium', data.get('personal_accident_premium', 0)),
        ('Alt. Accommodation Premium', data.get('alt_accommodation_premium', 0)),
    ]

    for label, amount in section_items:
        if amount > 0:
            premium_data.append([label, f'{amount:,.2f}'])

    premium_data.append(['Base Premium', f'{data.get("base_premium", 0):,.2f}'])

    adjustments = [
        ('Location Adjustment', data.get('location_adjustment', 0)),
        ('Cover Type Adjustment', data.get('cover_type_adjustment', 0)),
        ('Claims Loading', data.get('claims_loading', 0)),
        ('Security Discount', -data.get('security_discount', 0)),
        ('Fire Equipment Discount', -data.get('fire_equipment_discount', 0)),
        ('Duration Adjustment', data.get('duration_adjustment', 0)),
    ]

    for label, amount in adjustments:
        if amount != 0:
            sign = '+' if amount > 0 else ''
            premium_data.append([label, f'{sign}{amount:,.2f}'])

    gross = data.get('gross_premium', 0)

    premium_data.append(['TOTAL PREMIUM', f'{gross:,.2f}'])

    prem_table = Table(premium_data, colWidths=[100*mm, 60*mm])
    prem_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (-1, 0), WHITE),
        ('BACKGROUND', (0, 0), (-1, 0), ORANGE),
        ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LINEBELOW', (0, 1), (-1, -2), 0.5, HexColor('#EEEEEE')),
        ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
        ('TEXTCOLOR', (0, -1), (-1, -1), ORANGE),
        ('BACKGROUND', (0, -1), (-1, -1), LIGHT_GRAY),
        ('LINEABOVE', (0, -1), (-1, -1), 1, ORANGE),
    ]))
    elements.append(prem_table)
    elements.append(Spacer(1, 6*mm))

    # --- PAYMENT CONFIRMATION ---
    elements.append(Paragraph("PAYMENT CONFIRMATION", styles['SectionHead']))

    payment_ref = data.get('payment_reference', 'N/A')
    payment_date = datetime.datetime.now().strftime('%d %B %Y at %H:%M')

    pay_data = [
        ['Amount Paid', f"NGN {gross:,.2f}"],
        ['Payment Reference', payment_ref],
        ['Payment Date', payment_date],
        ['Payment Status', 'CONFIRMED'],
    ]

    pay_table = Table(pay_data, colWidths=[55*mm, 105*mm])
    pay_table.setStyle(TableStyle([
        ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ('FONTNAME', (1, 0), (1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('TEXTCOLOR', (0, 0), (0, -1), GRAY),
        ('TEXTCOLOR', (1, 0), (1, -1), DARK),
        ('TEXTCOLOR', (1, -1), (1, -1), HexColor('#2E7D32')),
        ('FONTNAME', (1, -1), (1, -1), 'Helvetica-Bold'),
        ('TOPPADDING', (0, 0), (-1, -1), 4),
        ('BOTTOMPADDING', (0, 0), (-1, -1), 4),
        ('LINEBELOW', (0, 0), (-1, -2), 0.5, HexColor('#EEEEEE')),
    ]))
    elements.append(pay_table)
    elements.append(Spacer(1, 8*mm))

    # --- INSURED PERILS ---
    elements.append(Paragraph("INSURED PERILS", styles['SectionHead']))
    perils = "Fire • Lightning • Explosion • Theft • Riot & Strike • Malicious Damage • Aircraft Impact • Burst Pipes • Impact Damage • Earthquake/Volcano • Hurricane/Cyclone • Flood • Storm"
    elements.append(Paragraph(perils, styles['PolicyBody']))
    elements.append(Spacer(1, 4*mm))

    # --- TERMS ---
    elements.append(Paragraph("IMPORTANT NOTICE", styles['SectionHead']))
    elements.append(Paragraph(
        "This policy is subject to the terms, conditions, and exclusions of the Leadway Assurance "
        "Houseowners & Householders Insurance Policy. The insured should read the full policy document "
        "carefully and ensure that all information provided is accurate and complete.",
        styles['PolicyBody']
    ))
    elements.append(Paragraph(
        "Theft cover applies only if accompanied by actual forcible and violent breaking in or out. "
        "No single item of jewelry insured under this policy shall be of greater value than 2.5% of "
        "the contents sum insured per location unless specifically insured.",
        styles['PolicyBody']
    ))
    elements.append(Spacer(1, 8*mm))

    # --- FOOTER ---
    elements.append(HRFlowable(width="100%", thickness=1, color=ORANGE, spaceBefore=4*mm, spaceAfter=4*mm))
    elements.append(Paragraph(
        "Leadway Assurance Company Limited (RC 7588)<br/>"
        "Leadway House, 121/123 Funso Williams Avenue, Iponri, Surulere, Lagos<br/>"
        "Tel: 02-012800700 | Email: insure@leadway.com | www.leadway.com",
        styles['FooterText']
    ))

    doc.build(elements)
    return buffer.getvalue()
