from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from datetime import datetime
import os

# ── Constants ─────────────────────────────────
NAVY       = colors.HexColor("#1a2c4e")
WHITE      = colors.white
BLACK      = colors.black
LIGHT_GREY = colors.HexColor("#f5f5f5")
MID_GREY   = colors.HexColor("#e0e0e0")
GREEN      = colors.HexColor("#0F6E56")

COMPANY_NAME  = "Twickenham Health Limited"
COMPANY_ADDR  = "1 Twickenham Grove, Stoke-on-Trent, ST4 8WS, United Kingdom"
COMPANY_PHONE = "07859 001684"
COMPANY_REG   = "16271052"

OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "output"
)


def generate_records_pdf(invoices: list, title: str = "Invoice Records") -> str:
    """
    Generate a PDF report of invoice records (the dashboard table).

    invoices = list of invoice dicts from db.get_all_invoices()
               Each dict: inv_no, inv_date, due_date, net_amount,
                          due_amount, status, session_count

    Returns the full path to the saved PDF.
    """
    os.makedirs(OUTPUT_DIR, exist_ok=True)

    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    filename  = os.path.join(OUTPUT_DIR, f"Records_Report_{timestamp}.pdf")

    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=15*mm,
        rightMargin=15*mm,
        topMargin=0,
        bottomMargin=10*mm,
    )

    story = []

    # ── 1. TOP NAVY BAR ──────────────────────
    story.append(_nav_bar(doc))

    # ── 2. COMPANY HEADER ────────────────────
    story.append(Spacer(1, 5*mm))
    story.append(_company_header(doc))
    story.append(Spacer(1, 4*mm))

    # ── 3. REPORT TITLE ──────────────────────
    heading = ParagraphStyle(
        "Heading",
        fontName="Helvetica-Bold",
        fontSize=14,
        textColor=BLACK,
        alignment=TA_CENTER,
    )
    story.append(Paragraph(f"<u>{title}</u>", heading))
    story.append(Spacer(1, 2*mm))

    # Print date
    date_style = ParagraphStyle(
        "DateStyle",
        fontName="Helvetica",
        fontSize=8,
        textColor=colors.HexColor("#555555"),
        alignment=TA_CENTER,
    )
    story.append(Paragraph(
        f"Printed on: {datetime.now().strftime('%d-%b-%Y %H:%M')}  |  "
        f"Total Records: {len(invoices)}",
        date_style
    ))
    story.append(Spacer(1, 4*mm))

    # ── 4. RECORDS TABLE ─────────────────────
    story.append(_records_table(invoices, doc))
    story.append(Spacer(1, 4*mm))

    # ── 5. SUMMARY TOTALS ────────────────────
    story.append(_summary_totals(invoices, doc))
    story.append(Spacer(1, 6*mm))

    # ── 6. FOOTER NOTE ───────────────────────
    footer_style = ParagraphStyle(
        "Footer",
        fontName="Helvetica",
        fontSize=7,
        textColor=colors.HexColor("#555555"),
        alignment=TA_LEFT,
    )
    story.append(Paragraph(
        "* This is a system generated records report.",
        footer_style
    ))
    story.append(Spacer(1, 4*mm))

    # ── 7. BOTTOM NAVY BAR ───────────────────
    story.append(_nav_bar(doc))

    doc.build(story)
    return filename


# ──────────────────────────────────────────────
#  SECTION BUILDERS
# ──────────────────────────────────────────────

def _nav_bar(doc):
    """Full-width navy bar."""
    t = Table([[""]], colWidths=[doc.width + doc.leftMargin + doc.rightMargin])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), NAVY),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
    ]))
    return t


def _company_header(doc):
    """Company name and details centred at top."""
    name_style = ParagraphStyle(
        "CompanyName",
        fontName="Helvetica-Bold",
        fontSize=13,
        textColor=NAVY,
        alignment=TA_CENTER,
    )
    detail_style = ParagraphStyle(
        "CompanyDetail",
        fontName="Helvetica",
        fontSize=8,
        textColor=NAVY,
        alignment=TA_CENTER,
        leading=12,
    )
    t = Table(
        [
            [Paragraph(COMPANY_NAME, name_style)],
            [Paragraph(
                f"{COMPANY_ADDR}  |  ☎ {COMPANY_PHONE}  |  Reg. No: {COMPANY_REG}",
                detail_style
            )],
        ],
        colWidths=[doc.width],
    )
    t.setStyle(TableStyle([
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    return t


def _records_table(invoices, doc):
    """Records table matching the dashboard layout."""
    th = ParagraphStyle(
        "TH", fontName="Helvetica-Bold",
        fontSize=8, textColor=WHITE, alignment=TA_CENTER
    )
    td_center = ParagraphStyle(
        "TDC", fontName="Helvetica",
        fontSize=8, textColor=BLACK, alignment=TA_CENTER
    )
    td_left = ParagraphStyle(
        "TDL", fontName="Helvetica",
        fontSize=8, textColor=BLACK, alignment=TA_LEFT
    )
    td_right = ParagraphStyle(
        "TDR", fontName="Helvetica-Bold",
        fontSize=8, textColor=BLACK, alignment=TA_RIGHT
    )

    col_widths = [20*mm, 24*mm, 24*mm, 40*mm, 16*mm, 24*mm, 24*mm, 18*mm]

    # Header row
    rows = [[
        Paragraph("Invoice No.",   th),
        Paragraph("Invoice Date",  th),
        Paragraph("Due Date",      th),
        Paragraph("Customer",      th),
        Paragraph("Sessions",      th),
        Paragraph("Net Amount",    th),
        Paragraph("Due Amount",    th),
        Paragraph("Status",        th),
    ]]

    # Data rows
    for inv in invoices:
        from logic.invoice_logic import format_date_for_display, format_currency
        status = inv.get("status", "pending")
        status_label = {
            "paid":    "Paid",
            "pending": "Pending",
            "overdue": "Overdue",
        }.get(status, status.title())

        # Colour code status
        status_colour = {
            "paid":    colors.HexColor("#0F6E56"),
            "pending": colors.HexColor("#854F0B"),
            "overdue": colors.HexColor("#A32D2D"),
        }.get(status, BLACK)

        td_status = ParagraphStyle(
            f"TDS_{status}", fontName="Helvetica-Bold",
            fontSize=8, textColor=status_colour, alignment=TA_CENTER
        )

        rows.append([
            Paragraph(inv.get("inv_no", ""),                           td_center),
            Paragraph(format_date_for_display(inv.get("inv_date", "")), td_center),
            Paragraph(format_date_for_display(inv.get("due_date", "")), td_center),
            Paragraph("Allen Street Clinic",                            td_left),
            Paragraph(str(inv.get("session_count", 0)),                 td_center),
            Paragraph(format_currency(inv.get("net_amount", 0)),        td_right),
            Paragraph(format_currency(inv.get("due_amount", 0)),        td_right),
            Paragraph(status_label,                                     td_status),
        ])

    t = Table(rows, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        # Header
        ("BACKGROUND",    (0, 0), (-1, 0),  NAVY),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  WHITE),
        # Alternating rows
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, LIGHT_GREY]),
        # Grid lines
        ("LINEBELOW",     (0, 0), (-1, -1), 0.3, MID_GREY),
        ("LINEABOVE",     (0, 0), (-1, 0),  1,   NAVY),
        ("LINEBELOW",     (0, -1),(-1, -1), 1,   NAVY),
        # Padding
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def _summary_totals(invoices, doc):
    """Summary totals row at the bottom of the report."""
    from logic.invoice_logic import format_currency

    total_net   = sum(inv.get("net_amount", 0) for inv in invoices)
    total_due   = sum(inv.get("due_amount", 0) for inv in invoices)
    total_paid  = sum(1 for inv in invoices if inv.get("status") == "paid")
    total_pend  = sum(1 for inv in invoices if inv.get("status") in ("pending", "overdue"))

    label_style = ParagraphStyle(
        "SumLabel", fontName="Helvetica-Bold",
        fontSize=9, textColor=NAVY, alignment=TA_LEFT
    )
    value_style = ParagraphStyle(
        "SumVal", fontName="Helvetica-Bold",
        fontSize=9, textColor=BLACK, alignment=TA_RIGHT
    )

    data = [
        [
            Paragraph(f"Total Records: {len(invoices)}", label_style),
            Paragraph(f"Paid: {total_paid}", label_style),
            Paragraph(f"Pending/Overdue: {total_pend}", label_style),
            Paragraph(f"Total Net: {format_currency(total_net)}", value_style),
            Paragraph(f"Total Due: {format_currency(total_due)}", value_style),
        ]
    ]

    col_widths = [
        doc.width * 0.22,
        doc.width * 0.15,
        doc.width * 0.22,
        doc.width * 0.20,
        doc.width * 0.21,
    ]

    t = Table(data, colWidths=col_widths)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), colors.HexColor("#e8edf4")),
        ("LINEABOVE",     (0, 0), (-1, 0),  1, NAVY),
        ("LINEBELOW",     (0, 0), (-1, -1), 1, NAVY),
        ("TOPPADDING",    (0, 0), (-1, -1), 6),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 6),
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t
