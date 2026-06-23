"""PDF generation service for electricity bills."""

import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional

try:
    from reportlab.lib import colors
    from reportlab.lib.pagesizes import A4
    from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
    from reportlab.lib.units import inch, cm
    from reportlab.platypus import (
        SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle, 
        Image as RLImage, HRFlowable
    )
    from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
    from reportlab.pdfbase import pdfmetrics
    from reportlab.pdfbase.ttfonts import TTFont
    REPORTLAB_AVAILABLE = True
    
    # Register a Unicode font that supports the rupee symbol
    # Try to use DejaVuSans which is commonly available and supports ₹
    UNICODE_FONT_REGISTERED = False
    try:
        # Common paths for DejaVuSans font
        font_paths = [
            '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
            '/usr/share/fonts/dejavu/DejaVuSans.ttf',
            '/Library/Fonts/DejaVuSans.ttf',
            '/System/Library/Fonts/Supplemental/Arial Unicode.ttf',
            os.path.expanduser('~/Library/Fonts/DejaVuSans.ttf'),
        ]
        
        for font_path in font_paths:
            if os.path.exists(font_path):
                pdfmetrics.registerFont(TTFont('DejaVuSans', font_path))
                UNICODE_FONT_REGISTERED = True
                break
    except Exception:
        pass
        
except ImportError:
    REPORTLAB_AVAILABLE = False
    UNICODE_FONT_REGISTERED = False

from config import UPLOADS_DIRECTORY

# Rupee symbol - use Rs. as requested by user
RUPEE = "Rs."

# Bill storage directory
BILLS_DIRECTORY = UPLOADS_DIRECTORY / "bills"
BILLS_DIRECTORY.mkdir(exist_ok=True)



def create_styles():
    """Create custom styles for the PDF."""
    styles = getSampleStyleSheet()
    
    # Use Unicode font if available for rupee symbol support
    font_name = 'DejaVuSans' if UNICODE_FONT_REGISTERED else 'Helvetica'
    
    styles.add(ParagraphStyle(
        name='BillTitle',
        parent=styles['Heading1'],
        fontName=font_name,
        fontSize=24,
        alignment=TA_CENTER,
        spaceAfter=20,
        textColor=colors.HexColor('#1a365d')
    ))
    
    styles.add(ParagraphStyle(
        name='SectionHeader',
        parent=styles['Heading2'],
        fontName=font_name,
        fontSize=14,
        spaceAfter=10,
        spaceBefore=15,
        textColor=colors.HexColor('#2d3748')
    ))
    
    styles.add(ParagraphStyle(
        name='RightAlign',
        parent=styles['Normal'],
        fontName=font_name,
        alignment=TA_RIGHT
    ))
    
    styles.add(ParagraphStyle(
        name='CenterAlign',
        parent=styles['Normal'],
        fontName=font_name,
        alignment=TA_CENTER
    ))
    
    # Add a style specifically for currency
    styles.add(ParagraphStyle(
        name='Currency',
        parent=styles['Normal'],
        fontName=font_name,
        alignment=TA_RIGHT
    ))
    
    return styles


def generate_bill_pdf(
    user_name: str,
    billing_period: str,
    appliances: List[Dict],
    total_units: float,
    total_bill: float,
    tariff_rate: float,
    city: str = "Unknown",
    company: str = "Electricity Provider",
    meter_reading: Optional[Dict] = None
) -> Dict:
    """Generate a PDF electricity bill."""
    
    if not REPORTLAB_AVAILABLE:
        return {
            "status": "error",
            "message": "ReportLab not available. Please install reportlab."
        }
    
    try:
        # Generate unique bill ID and filename
        bill_id = f"BILL-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        filename = f"{bill_id}.pdf"
        filepath = BILLS_DIRECTORY / filename
        
        # Create PDF document
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=A4,
            rightMargin=1*cm,
            leftMargin=1*cm,
            topMargin=1*cm,
            bottomMargin=1*cm
        )
        
        styles = create_styles()
        elements = []
        
        # Header
        elements.append(Paragraph("⚡ ELECTRICITY BILL", styles['BillTitle']))
        elements.append(Spacer(1, 10))
        
        # Company and Bill Info
        header_data = [
            [Paragraph(f"<b>{company}</b>", styles['Normal']), 
             Paragraph(f"<b>Bill No:</b> {bill_id}", styles['RightAlign'])],
            [Paragraph(f"City: {city}", styles['Normal']),
             Paragraph(f"<b>Date:</b> {datetime.now().strftime('%d/%m/%Y')}", styles['RightAlign'])],
            [Paragraph(f"Billing Period: {billing_period}", styles['Normal']),
             Paragraph(f"<b>Tariff Rate:</b> {RUPEE}{tariff_rate}/kWh", styles['RightAlign'])]
        ]
        
        header_table = Table(header_data, colWidths=[10*cm, 8*cm])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 10))
        
        # Divider
        elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#3182ce')))
        elements.append(Spacer(1, 10))
        
        # Customer Info
        elements.append(Paragraph("<b>Customer Details</b>", styles['SectionHeader']))
        elements.append(Paragraph(f"Name: {user_name}", styles['Normal']))
        elements.append(Spacer(1, 15))
        
        # Meter Reading (if available)
        if meter_reading:
            elements.append(Paragraph("<b>Meter Reading</b>", styles['SectionHeader']))
            meter_data = [
                ["Previous Reading", "Current Reading", "Units Consumed"],
                [str(meter_reading.get('previous', 'N/A')), 
                 str(meter_reading.get('current', 'N/A')),
                 str(meter_reading.get('units', total_units))]
            ]
            meter_table = Table(meter_data, colWidths=[6*cm, 6*cm, 6*cm])
            meter_table.setStyle(TableStyle([
                ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#edf2f7')),
                ('TEXTCOLOR', (0, 0), (-1, 0), colors.HexColor('#2d3748')),
                ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
                ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
                ('FONTSIZE', (0, 0), (-1, -1), 10),
                ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
                ('BACKGROUND', (0, 1), (-1, -1), colors.white),
                ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e0'))
            ]))
            elements.append(meter_table)
            elements.append(Spacer(1, 15))
        
        # Appliance-wise Breakdown
        elements.append(Paragraph("<b>Consumption Breakdown</b>", styles['SectionHeader']))
        
        # Table header
        appliance_data = [
            ["Appliance", "Power (W)", "Qty", "Daily Hours", "Monthly kWh", f"Cost ({RUPEE})"]
        ]
        
        # Calculate and add appliance rows
        total_cost = 0
        total_kwh = 0
        
        for app in appliances:
            power = app.get('power_rating', 0)
            qty = app.get('quantity', 1)
            hours = app.get('average_daily_hours', 0)
            
            # Calculate monthly consumption
            monthly_kwh = (power * qty * hours * 30) / 1000
            cost = monthly_kwh * tariff_rate
            
            total_kwh += monthly_kwh
            total_cost += cost
            
            appliance_data.append([
                app.get('name', 'Unknown'),
                str(power),
                str(qty),
                str(hours),
                f"{monthly_kwh:.2f}",
                f"{RUPEE}{cost:.2f}"
            ])
        
        # Add totals row
        appliance_data.append([
            "<b>TOTAL</b>", "", "", "", f"<b>{total_kwh:.2f}</b>", f"<b>{RUPEE}{total_cost:.2f}</b>"
        ])
        
        # Create table with Paragraph objects for bold text
        appliance_data_formatted = []
        for row in appliance_data:
            formatted_row = []
            for cell in row:
                if "<b>" in str(cell):
                    formatted_row.append(Paragraph(cell, styles['Normal']))
                else:
                    formatted_row.append(cell)
            appliance_data_formatted.append(formatted_row)
        
        appliance_table = Table(appliance_data_formatted, 
                                colWidths=[5*cm, 2.5*cm, 1.5*cm, 3*cm, 3*cm, 3*cm])
        appliance_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#3182ce')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 9),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('BACKGROUND', (0, 1), (-1, -2), colors.white),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#edf2f7')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#cbd5e0')),
            ('ROWBACKGROUNDS', (0, 1), (-1, -2), [colors.white, colors.HexColor('#f7fafc')])
        ]))
        elements.append(appliance_table)
        elements.append(Spacer(1, 20))
        
        # Bill Summary
        elements.append(Paragraph("<b>Bill Summary</b>", styles['SectionHeader']))
        
        # Calculate additional charges
        fixed_charge = 50.0  # Fixed monthly charge
        energy_charge = total_cost
        taxes = total_cost * 0.05  # 5% tax
        final_total = energy_charge + fixed_charge + taxes
        
        summary_data = [
            ["Energy Charges", f"{RUPEE}{energy_charge:.2f}"],
            ["Fixed Charges", f"{RUPEE}{fixed_charge:.2f}"],
            ["Taxes & Duties (5%)", f"{RUPEE}{taxes:.2f}"],
            ["", ""],
            ["TOTAL AMOUNT DUE", f"{RUPEE}{final_total:.2f}"]
        ]
        
        summary_table = Table(summary_data, colWidths=[12*cm, 6*cm])
        summary_table.setStyle(TableStyle([
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 8),
            ('LINEBELOW', (0, 2), (-1, 2), 1, colors.HexColor('#cbd5e0')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 14),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#2f855a')),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f0fff4')),
        ]))
        elements.append(summary_table)
        elements.append(Spacer(1, 20))
        
        # Footer
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e2e8f0')))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(
            "<i>This is a computer-generated bill. For queries, contact your electricity provider.</i>",
            styles['CenterAlign']
        ))
        elements.append(Paragraph(
            f"<i>Generated on {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</i>",
            styles['CenterAlign']
        ))
        
        # Build PDF
        doc.build(elements)
        
        return {
            "status": "success",
            "bill_id": bill_id,
            "filename": filename,
            "filepath": str(filepath),
            "download_url": f"/uploads/bills/{filename}",
            "summary": {
                "total_units": round(total_kwh, 2),
                "energy_charges": round(energy_charge, 2),
                "fixed_charges": fixed_charge,
                "taxes": round(taxes, 2),
                "total_amount": round(final_total, 2)
            }
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to generate PDF: {str(e)}"
        }


def get_bill_by_id(bill_id: str) -> Optional[str]:
    """Get bill filepath by ID."""
    filename = f"{bill_id}.pdf"
    filepath = BILLS_DIRECTORY / filename
    
    if filepath.exists():
        return str(filepath)
    return None


def list_generated_bills() -> List[Dict]:
    """List all generated bills."""
    bills = []
    for file in BILLS_DIRECTORY.glob("*.pdf"):
        bills.append({
            "bill_id": file.stem,
            "filename": file.name,
            "created": datetime.fromtimestamp(file.stat().st_mtime).isoformat(),
            "size_kb": round(file.stat().st_size / 1024, 2)
        })
    
    # Sort by creation time (newest first)
    bills.sort(key=lambda x: x["created"], reverse=True)
    return bills


def generate_ocr_bill_pdf(
    customer_name: str,
    customer_id: str,
    billing_period: str,
    previous_reading: float,
    current_reading: float,
    units: float,
    tariff_rate: float,
    city: str = "Unknown",
    company: str = "Electricity Provider"
) -> Dict:
    """Generate a PDF bill based on OCR meter reading data."""
    
    if not REPORTLAB_AVAILABLE:
        return {
            "status": "error",
            "message": "ReportLab not available. Please install reportlab."
        }
    
    try:
        # Generate unique bill ID
        bill_id = f"OCR-{datetime.now().strftime('%Y%m%d')}-{uuid.uuid4().hex[:6].upper()}"
        filename = f"{bill_id}.pdf"
        filepath = BILLS_DIRECTORY / filename
        
        # Create PDF document
        doc = SimpleDocTemplate(
            str(filepath),
            pagesize=A4,
            rightMargin=1*cm,
            leftMargin=1*cm,
            topMargin=1*cm,
            bottomMargin=1*cm
        )
        
        styles = create_styles()
        elements = []
        
        # Header
        elements.append(Paragraph("⚡ ELECTRICITY BILL", styles['BillTitle']))
        elements.append(Paragraph("<i>Based on Meter Reading</i>", styles['CenterAlign']))
        elements.append(Spacer(1, 15))
        
        # Company and Bill Info
        header_data = [
            [Paragraph(f"<b>{company}</b>", styles['Normal']), 
             Paragraph(f"<b>Bill No:</b> {bill_id}", styles['RightAlign'])],
            [Paragraph(f"City: {city}", styles['Normal']),
             Paragraph(f"<b>Date:</b> {datetime.now().strftime('%d/%m/%Y')}", styles['RightAlign'])],
            [Paragraph(f"Billing Period: {billing_period}", styles['Normal']),
             Paragraph(f"<b>Tariff Rate:</b> {RUPEE}{tariff_rate}/kWh", styles['RightAlign'])]
        ]
        
        header_table = Table(header_data, colWidths=[10*cm, 8*cm])
        header_table.setStyle(TableStyle([
            ('VALIGN', (0, 0), (-1, -1), 'TOP'),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
        ]))
        elements.append(header_table)
        elements.append(Spacer(1, 10))
        
        # Divider
        elements.append(HRFlowable(width="100%", thickness=2, color=colors.HexColor('#8b5cf6')))
        elements.append(Spacer(1, 15))
        
        # Customer Info
        elements.append(Paragraph("<b>Customer Details</b>", styles['SectionHeader']))
        customer_data = [
            ["Customer Name:", customer_name],
            ["Customer ID:", customer_id if customer_id else "N/A"]
        ]
        customer_table = Table(customer_data, colWidths=[4*cm, 14*cm])
        customer_table.setStyle(TableStyle([
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 5),
            ('FONTNAME', (0, 0), (0, -1), 'Helvetica-Bold'),
        ]))
        elements.append(customer_table)
        elements.append(Spacer(1, 20))
        
        # Meter Reading Section - Main Focus for OCR bill
        elements.append(Paragraph("<b>Meter Reading Details</b>", styles['SectionHeader']))
        
        meter_data = [
            ["Previous Reading", "Current Reading", "Units Consumed"],
            [f"{previous_reading:.0f}", f"{current_reading:.0f}", f"{units:.2f} kWh"]
        ]
        
        meter_table = Table(meter_data, colWidths=[6*cm, 6*cm, 6*cm])
        meter_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#8b5cf6')),
            ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
            ('ALIGN', (0, 0), (-1, -1), 'CENTER'),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('FONTNAME', (0, 1), (-1, 1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, 0), (-1, -1), 12),
            ('FONTSIZE', (0, 1), (-1, 1), 14),
            ('BOTTOMPADDING', (0, 0), (-1, 0), 12),
            ('TOPPADDING', (0, 1), (-1, 1), 15),
            ('BOTTOMPADDING', (0, 1), (-1, 1), 15),
            ('BACKGROUND', (0, 1), (-1, -1), colors.HexColor('#f3e8ff')),
            ('GRID', (0, 0), (-1, -1), 1, colors.HexColor('#a78bfa'))
        ]))
        elements.append(meter_table)
        elements.append(Spacer(1, 25))
        
        # Bill Calculation
        elements.append(Paragraph("<b>Bill Calculation</b>", styles['SectionHeader']))
        
        # Calculate charges
        energy_charge = units * tariff_rate
        fixed_charge = 50.0
        taxes = energy_charge * 0.05
        total_amount = energy_charge + fixed_charge + taxes
        
        calc_data = [
            ["Description", "Amount"],
            [f"Energy Charges ({units:.2f} kWh × {RUPEE}{tariff_rate})", f"{RUPEE}{energy_charge:.2f}"],
            ["Fixed Charges", f"{RUPEE}{fixed_charge:.2f}"],
            ["Taxes & Duties (5%)", f"{RUPEE}{taxes:.2f}"],
            ["", ""],
            ["TOTAL AMOUNT DUE", f"{RUPEE}{total_amount:.2f}"]
        ]
        
        calc_table = Table(calc_data, colWidths=[12*cm, 6*cm])
        calc_table.setStyle(TableStyle([
            ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#edf2f7')),
            ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
            ('ALIGN', (1, 0), (1, -1), 'RIGHT'),
            ('FONTSIZE', (0, 0), (-1, -1), 11),
            ('BOTTOMPADDING', (0, 0), (-1, -1), 10),
            ('TOPPADDING', (0, 0), (-1, -1), 10),
            ('LINEBELOW', (0, 3), (-1, 3), 1, colors.HexColor('#cbd5e0')),
            ('FONTNAME', (0, -1), (-1, -1), 'Helvetica-Bold'),
            ('FONTSIZE', (0, -1), (-1, -1), 14),
            ('TEXTCOLOR', (0, -1), (-1, -1), colors.HexColor('#7c3aed')),
            ('BACKGROUND', (0, -1), (-1, -1), colors.HexColor('#f3e8ff')),
            ('GRID', (0, 0), (-1, -1), 0.5, colors.HexColor('#e2e8f0'))
        ]))
        elements.append(calc_table)
        elements.append(Spacer(1, 25))
        
        # Footer
        elements.append(HRFlowable(width="100%", thickness=1, color=colors.HexColor('#e2e8f0')))
        elements.append(Spacer(1, 10))
        elements.append(Paragraph(
            "<i>This bill was generated from OCR meter reading extraction.</i>",
            styles['CenterAlign']
        ))
        elements.append(Paragraph(
            f"<i>Generated on {datetime.now().strftime('%d/%m/%Y %H:%M:%S')}</i>",
            styles['CenterAlign']
        ))
        
        # Build PDF
        doc.build(elements)
        
        return {
            "status": "success",
            "bill_id": bill_id,
            "filename": filename,
            "filepath": str(filepath),
            "download_url": f"/uploads/bills/{filename}",
            "summary": {
                "previous_reading": previous_reading,
                "current_reading": current_reading,
                "total_units": round(units, 2),
                "energy_charges": round(energy_charge, 2),
                "fixed_charges": fixed_charge,
                "taxes": round(taxes, 2),
                "total_amount": round(total_amount, 2)
            }
        }
    
    except Exception as e:
        return {
            "status": "error",
            "message": f"Failed to generate OCR bill PDF: {str(e)}"
        }


def get_pdf_status() -> Dict:
    """Get PDF service status."""
    return {
        "reportlab_available": REPORTLAB_AVAILABLE,
        "status": "ready" if REPORTLAB_AVAILABLE else "dependencies_missing",
        "message": "PDF service is ready" if REPORTLAB_AVAILABLE else "Please install reportlab"
    }
