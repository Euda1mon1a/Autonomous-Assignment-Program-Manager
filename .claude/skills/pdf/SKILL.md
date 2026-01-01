---
name: pdf
description: PDF generation and manipulation for compliance reports, schedule printouts, and document extraction. Use when creating printable documents or extracting data from PDFs.
model_tier: sonnet
parallel_hints:
  can_parallel_with: [xlsx, code-review, test-writer]
  must_serialize_with: [database-migration]
  preferred_batch_size: 3
context_hints:
  max_file_context: 30
  compression_level: 1
  requires_git_context: false
  requires_db_context: true
escalation_triggers:
  - pattern: "password.*protected"
    reason: "Encrypted PDFs require human verification of access rights"
  - keyword: ["PHI", "HIPAA", "confidential"]
    reason: "Protected health information requires human review"
  - pattern: "extract.*signature"
    reason: "Signature extraction has legal implications"
---

# PDF Processing Skill

Comprehensive PDF operations for generating compliance reports, printable schedules, and extracting data from uploaded documents.

## When This Skill Activates

- Generating printable schedule PDFs
- Creating ACGME compliance reports
- Extracting data from uploaded PDF documents
- Merging or splitting PDF files
- Adding watermarks or headers to documents

## Required Libraries

```python
# PDF generation
from reportlab.lib.pagesizes import letter, A4
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.units import inch
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer

# PDF reading and manipulation
import pypdf
from pypdf import PdfReader, PdfWriter, PdfMerger

# Text and table extraction
import pdfplumber

# OCR for scanned documents (optional)
# import pytesseract
# from pdf2image import convert_from_path
```

## PDF Generation Patterns

### Schedule Report

```python
from reportlab.platypus import SimpleDocTemplate, Table, TableStyle, Paragraph, Spacer
from reportlab.lib.pagesizes import letter, landscape
from reportlab.lib import colors
from reportlab.lib.styles import getSampleStyleSheet
from io import BytesIO
from datetime import date

def generate_schedule_pdf(
    schedule_data: dict,
    start_date: date,
    end_date: date
) -> BytesIO:
    """Generate printable schedule PDF."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(
        buffer,
        pagesize=landscape(letter),
        rightMargin=0.5*inch,
        leftMargin=0.5*inch,
        topMargin=0.5*inch,
        bottomMargin=0.5*inch
    )

    styles = getSampleStyleSheet()
    elements = []

    # Title
    title = Paragraph(
        f"<b>Schedule: {start_date.strftime('%B %d')} - {end_date.strftime('%B %d, %Y')}</b>",
        styles['Title']
    )
    elements.append(title)
    elements.append(Spacer(1, 0.25*inch))

    # Build table data
    headers = ['Name', 'Role'] + [d.strftime('%a %m/%d') for d in schedule_data['dates']]
    table_data = [headers]

    for person in schedule_data['assignments']:
        row = [person['name'], person['role']]
        row.extend(person['daily_assignments'])
        table_data.append(row)

    # Create table with styling
    table = Table(table_data, repeatRows=1)
    table.setStyle(TableStyle([
        # Header styling
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#366092')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, 0), 10),
        ('ALIGN', (0, 0), (-1, 0), 'CENTER'),

        # Body styling
        ('FONTNAME', (0, 1), (-1, -1), 'Helvetica'),
        ('FONTSIZE', (0, 1), (-1, -1), 8),
        ('ALIGN', (0, 1), (-1, -1), 'CENTER'),

        # Grid
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),

        # Alternating row colors
        ('ROWBACKGROUNDS', (0, 1), (-1, -1), [colors.white, colors.HexColor('#F0F0F0')]),
    ]))

    elements.append(table)

    # Footer with generation timestamp
    elements.append(Spacer(1, 0.5*inch))
    footer = Paragraph(
        f"<i>Generated: {date.today().strftime('%Y-%m-%d %H:%M')}</i>",
        styles['Normal']
    )
    elements.append(footer)

    doc.build(elements)
    buffer.seek(0)
    return buffer
```

### ACGME Compliance Report

```python
def generate_compliance_report_pdf(
    compliance_data: dict,
    period_start: date,
    period_end: date
) -> BytesIO:
    """Generate ACGME compliance report PDF."""
    buffer = BytesIO()
    doc = SimpleDocTemplate(buffer, pagesize=letter)

    styles = getSampleStyleSheet()
    elements = []

    # Header
    elements.append(Paragraph(
        "<b>ACGME Compliance Report</b>",
        styles['Title']
    ))
    elements.append(Paragraph(
        f"Period: {period_start.strftime('%B %d, %Y')} - {period_end.strftime('%B %d, %Y')}",
        styles['Normal']
    ))
    elements.append(Spacer(1, 0.25*inch))

    # Summary section
    elements.append(Paragraph("<b>Compliance Summary</b>", styles['Heading2']))

    summary_data = [
        ['Metric', 'Compliant', 'Total', 'Rate'],
        ['80-Hour Rule', str(compliance_data['hours_compliant']),
         str(compliance_data['total_residents']),
         f"{compliance_data['hours_rate']:.1%}"],
        ['1-in-7 Rule', str(compliance_data['day_off_compliant']),
         str(compliance_data['total_residents']),
         f"{compliance_data['day_off_rate']:.1%}"],
        ['Supervision Ratios', str(compliance_data['supervision_compliant']),
         str(compliance_data['total_checks']),
         f"{compliance_data['supervision_rate']:.1%}"],
    ]

    summary_table = Table(summary_data, colWidths=[2*inch, 1*inch, 1*inch, 1*inch])
    summary_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#366092')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
    ]))

    elements.append(summary_table)
    elements.append(Spacer(1, 0.5*inch))

    # Violations section (if any)
    if compliance_data.get('violations'):
        elements.append(Paragraph("<b>Violations</b>", styles['Heading2']))

        for violation in compliance_data['violations']:
            elements.append(Paragraph(
                f"• <b>{violation['resident']}</b>: {violation['type']} - {violation['details']}",
                styles['Normal']
            ))
        elements.append(Spacer(1, 0.25*inch))

    # Individual resident details
    elements.append(Paragraph("<b>Individual Compliance</b>", styles['Heading2']))

    detail_data = [['Resident', 'PGY', 'Avg Hours', '80hr', 'Days Off', '1-in-7']]
    for resident in compliance_data['residents']:
        detail_data.append([
            resident['name'],
            f"PGY-{resident['pgy_level']}",
            f"{resident['avg_hours']:.1f}",
            '✓' if resident['hours_compliant'] else '✗',
            str(resident['days_off']),
            '✓' if resident['day_off_compliant'] else '✗',
        ])

    detail_table = Table(detail_data, colWidths=[1.5*inch, 0.5*inch, 0.8*inch, 0.5*inch, 0.7*inch, 0.5*inch])
    detail_table.setStyle(TableStyle([
        ('BACKGROUND', (0, 0), (-1, 0), colors.HexColor('#366092')),
        ('TEXTCOLOR', (0, 0), (-1, 0), colors.white),
        ('FONTNAME', (0, 0), (-1, 0), 'Helvetica-Bold'),
        ('FONTSIZE', (0, 0), (-1, -1), 9),
        ('GRID', (0, 0), (-1, -1), 0.5, colors.grey),
        ('ALIGN', (1, 0), (-1, -1), 'CENTER'),
    ]))

    elements.append(detail_table)

    doc.build(elements)
    buffer.seek(0)
    return buffer
```

## PDF Reading and Extraction

### Extract Text from PDF

```python
import pdfplumber

def extract_text_from_pdf(file_path: str) -> str:
    """Extract all text from a PDF file."""
    text_content = []

    with pdfplumber.open(file_path) as pdf:
        for page in pdf.pages:
            text = page.extract_text()
            if text:
                text_content.append(text)

    return "\n\n".join(text_content)
```

### Extract Tables from PDF

```python
import pandas as pd
import pdfplumber

def extract_tables_from_pdf(file_path: str) -> list[pd.DataFrame]:
    """Extract all tables from a PDF as DataFrames."""
    tables = []

    with pdfplumber.open(file_path) as pdf:
        for page_num, page in enumerate(pdf.pages):
            page_tables = page.extract_tables()

            for table_idx, table in enumerate(page_tables):
                if table and len(table) > 1:
                    # Use first row as headers
                    df = pd.DataFrame(table[1:], columns=table[0])
                    df.attrs['source'] = f"Page {page_num + 1}, Table {table_idx + 1}"
                    tables.append(df)

    return tables
```

### Import Schedule from PDF

```python
async def import_schedule_from_pdf(
    file_path: str,
    db: AsyncSession,
    schedule_id: str
) -> tuple[list, list]:
    """
    Attempt to import schedule data from PDF.

    Note: PDF parsing is less reliable than Excel.
    Best for structured, table-based PDFs.
    """
    errors = []
    created = []

    tables = extract_tables_from_pdf(file_path)

    if not tables:
        errors.append({'error': 'No tables found in PDF'})
        return created, errors

    # Try to identify schedule table
    for df in tables:
        # Look for date-like columns
        date_cols = [col for col in df.columns if _looks_like_date(col)]

        if not date_cols:
            continue

        # Process as schedule
        # ... similar logic to Excel import
        pass

    return created, errors


def _looks_like_date(value: str) -> bool:
    """Check if value looks like a date header."""
    import re
    date_patterns = [
        r'\d{1,2}/\d{1,2}',  # MM/DD
        r'Mon|Tue|Wed|Thu|Fri|Sat|Sun',  # Day names
        r'Jan|Feb|Mar|Apr|May|Jun|Jul|Aug|Sep|Oct|Nov|Dec',  # Month names
    ]
    return any(re.search(p, str(value), re.I) for p in date_patterns)
```

## PDF Manipulation

### Merge PDFs

```python
from pypdf import PdfMerger

def merge_pdfs(input_files: list[str], output_path: str) -> None:
    """Merge multiple PDFs into one."""
    merger = PdfMerger()

    for pdf_file in input_files:
        merger.append(pdf_file)

    merger.write(output_path)
    merger.close()
```

### Split PDF

```python
from pypdf import PdfReader, PdfWriter

def split_pdf(input_file: str, output_dir: str) -> list[str]:
    """Split PDF into individual pages."""
    reader = PdfReader(input_file)
    output_files = []

    for i, page in enumerate(reader.pages):
        writer = PdfWriter()
        writer.add_page(page)

        output_path = f"{output_dir}/page_{i+1}.pdf"
        with open(output_path, 'wb') as out_file:
            writer.write(out_file)
        output_files.append(output_path)

    return output_files
```

### Add Watermark

```python
from pypdf import PdfReader, PdfWriter
from reportlab.pdfgen import canvas
from reportlab.lib.pagesizes import letter
from io import BytesIO

def add_watermark(input_file: str, watermark_text: str, output_file: str) -> None:
    """Add text watermark to all pages."""
    # Create watermark
    watermark_buffer = BytesIO()
    c = canvas.Canvas(watermark_buffer, pagesize=letter)
    c.setFont("Helvetica", 50)
    c.setFillColorRGB(0.5, 0.5, 0.5, 0.3)  # Gray, semi-transparent
    c.saveState()
    c.translate(300, 400)
    c.rotate(45)
    c.drawCentredString(0, 0, watermark_text)
    c.restoreState()
    c.save()
    watermark_buffer.seek(0)

    watermark_pdf = PdfReader(watermark_buffer)
    watermark_page = watermark_pdf.pages[0]

    # Apply to each page
    reader = PdfReader(input_file)
    writer = PdfWriter()

    for page in reader.pages:
        page.merge_page(watermark_page)
        writer.add_page(page)

    with open(output_file, 'wb') as out_file:
        writer.write(out_file)
```

## FastAPI Integration

### Export Endpoint

```python
from fastapi import APIRouter
from fastapi.responses import StreamingResponse

router = APIRouter()

@router.get("/schedules/{schedule_id}/export/pdf")
async def export_schedule_pdf(
    schedule_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Export schedule as printable PDF."""
    schedule = await get_schedule_with_assignments(db, schedule_id)

    pdf_buffer = generate_schedule_pdf(
        schedule_data=schedule,
        start_date=schedule.start_date,
        end_date=schedule.end_date
    )

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=schedule_{schedule_id}.pdf"
        }
    )


@router.get("/compliance/report/pdf")
async def export_compliance_report(
    start_date: date,
    end_date: date,
    db: AsyncSession = Depends(get_db)
):
    """Generate ACGME compliance report PDF."""
    compliance_data = await calculate_compliance(db, start_date, end_date)

    pdf_buffer = generate_compliance_report_pdf(
        compliance_data=compliance_data,
        period_start=start_date,
        period_end=end_date
    )

    return StreamingResponse(
        pdf_buffer,
        media_type="application/pdf",
        headers={
            "Content-Disposition": f"attachment; filename=compliance_report_{start_date}_{end_date}.pdf"
        }
    )
```

## Security Considerations

### Uploaded PDF Validation

```python
import magic

def validate_pdf_upload(file_content: bytes) -> bool:
    """Validate uploaded file is actually a PDF."""
    # Check magic bytes
    mime = magic.from_buffer(file_content, mime=True)
    if mime != 'application/pdf':
        return False

    # Check file header
    if not file_content.startswith(b'%PDF'):
        return False

    return True
```

### Sanitize Extracted Text

```python
import re

def sanitize_extracted_text(text: str) -> str:
    """Remove potentially dangerous content from extracted text."""
    # Remove control characters
    text = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', text)

    # Remove script-like patterns (basic XSS prevention)
    text = re.sub(r'<script[^>]*>.*?</script>', '', text, flags=re.I | re.S)

    return text.strip()
```

## Verification Checklist

Before finalizing any PDF operation:

- [ ] PDF renders correctly in multiple viewers
- [ ] Tables fit within page margins
- [ ] Fonts are embedded (for portability)
- [ ] File size is reasonable
- [ ] No sensitive data in metadata
- [ ] Page orientation matches content

## References

- [ReportLab Documentation](https://docs.reportlab.com/)
- [pypdf Documentation](https://pypdf.readthedocs.io/)
- [pdfplumber Documentation](https://github.com/jsvine/pdfplumber)
- Project exports: `backend/app/services/exports/`
