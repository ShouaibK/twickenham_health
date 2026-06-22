import os
import subprocess
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.platypus import Image as RLImage

from logic.invoice_logic import format_date_for_display, format_currency, format_rate

# ──────────────────────────────────────────────
#  COMPANY CONSTANTS (never change without updating SKILL.md)
# ──────────────────────────────────────────────
COMPANY_NAME   = "Twickenham Health Limited"
COMPANY_ADDR1  = "1 Twickenham Grove,"
COMPANY_ADDR2  = "Stoke-on-Trent, ST4 8WS,"
COMPANY_ADDR3  = "United Kingdom."
COMPANY_PHONE  = "07859 001684"
COMPANY_REG    = "16271052"

CUSTOMER_NAME  = "Allen Street Clinic"
CUSTOMER_ADDR1 = "Allen Street, Stoke-On-Trent ST10 1HJ,"
CUSTOMER_ADDR2 = "United Kingdom."

BANK_NAME      = "MONZO"
BANK_ACCOUNT   = "99909112"
BANK_SORT      = "04-00-03"

FOOTER_NOTE    = ("* This is system generated invoice doesn't require "
                  "signature and stamp.")

# Colours
NAVY       = colors.HexColor("#1a2c4e")
WHITE      = colors.white
BLACK      = colors.black
LIGHT_GREY = colors.HexColor("#f5f5f5")

# Output folder — PDFs saved inside project/output/
OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "output"
)


# ──────────────────────────────────────────────
#  HELPERS
# ──────────────────────────────────────────────

def _ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def _get_logo_path():
    """Return logo path if it exists, else None."""
    base      = os.path.dirname(os.path.dirname(__file__))
    asset_dir = os.path.join(base, "assets")
    for name in ["twickenham_health_logo.png", "logo.png",
                 "logo.jpg", "logo.jpeg"]:
        path = os.path.join(asset_dir, name)
        if os.path.exists(path):
            return path
    return None


def get_output_folder() -> str:
    """Return the path to the output/ folder where PDFs are saved."""
    return OUTPUT_DIR


def open_output_folder():
    """Open the output/ folder in Windows Explorer."""
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    try:
        os.startfile(OUTPUT_DIR)
    except Exception:
        subprocess.Popen(f'start "" "{OUTPUT_DIR}"', shell=True)


# ──────────────────────────────────────────────
#  OPEN / PRINT PDF
# ──────────────────────────────────────────────

def open_pdf(pdf_path: str) -> bool:
    """Open a PDF in the default system viewer. Returns True on success."""
    if not os.path.exists(pdf_path):
        return False
    try:
        os.startfile(pdf_path)
        return True
    except Exception:
        try:
            subprocess.Popen(f'start "" "{pdf_path}"', shell=True)
            return True
        except Exception:
            return False


def generate_and_open(invoice: dict) -> tuple[bool, str]:
    """
    Generate a PDF invoice then open it in the default viewer.
    Returns (True, pdf_path) on success or (False, error_message).
    """
    try:
        pdf_path = generate_pdf(invoice)
        if open_pdf(pdf_path):
            return True, pdf_path
        return False, f"PDF saved but could not open:\n{pdf_path}"
    except Exception as e:
        return False, f"Failed to generate PDF:\n{str(e)}"


def generate_and_print(invoice: dict) -> tuple[bool, str]:
    """
    Generate a PDF invoice then open it for printing.
    Opens in the default viewer so the user can print from there.
    Returns (True, pdf_path) on success or (False, error_message).
    """
    return generate_and_open(invoice)


# ──────────────────────────────────────────────
#  PDF INVOICE GENERATOR
# ──────────────────────────────────────────────

def generate_pdf(invoice: dict) -> str:
    """
    Build a PDF invoice matching the Twickenham Health sample layout.

    invoice dict keys (from db.get_invoice_by_id):
        inv_no, inv_date, due_date, ref, net_amount, due_amount, sessions

    Each session dict:
        sr_no, activity, job_date, hour_rate, work_hours, session_total

    Returns the full path to the saved PDF file.
    """
    _ensure_output_dir()

    inv_no   = invoice.get("inv_no", "")
    inv_date = format_date_for_display(invoice.get("inv_date", ""))
    due_date = format_date_for_display(invoice.get("due_date", ""))
    ref      = invoice.get("ref", "") or ""
    net_amt  = format_currency(invoice.get("net_amount", 0))
    due_amt  = format_currency(invoice.get("due_amount", 0))
    sessions = invoice.get("sessions", [])

    filename = os.path.join(OUTPUT_DIR, f"{inv_no}.pdf")

    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=20*mm,
        rightMargin=20*mm,
        topMargin=0,
        bottomMargin=0,
    )

    story = []
    story.append(_navy_bar(doc))
    story.append(Spacer(1, 6*mm))
    story.append(_company_header(doc))
    story.append(Spacer(1, 6*mm))

    heading_style = ParagraphStyle(
        "Heading",
        fontName="Helvetica-Bold",
        fontSize=16,
        textColor=BLACK,
        alignment=TA_CENTER,
    )
    story.append(Paragraph("<u>Invoice to Customer</u>", heading_style))
    story.append(Spacer(1, 8*mm))

    story.append(_bill_to_block(inv_no, inv_date, due_date, doc))
    story.append(Spacer(1, 6*mm))
    story.append(_sessions_table(sessions, doc))
    story.append(Spacer(1, 6*mm))
    story.append(_totals_block(ref, net_amt, due_amt, doc))
    story.append(Spacer(1, 8*mm))
    story.append(_bank_details(doc))
    story.append(Spacer(1, 10*mm))

    footer_style = ParagraphStyle(
        "Footer",
        fontName="Helvetica",
        fontSize=7,
        textColor=colors.HexColor("#555555"),
        alignment=TA_LEFT,
    )
    story.append(Paragraph(FOOTER_NOTE, footer_style))
    story.append(Spacer(1, 6*mm))
    story.append(_navy_bar(doc))

    doc.build(story)
    return filename


# ──────────────────────────────────────────────
#  PDF SECTION BUILDERS
# ──────────────────────────────────────────────

def _navy_bar(doc):
    """Full-width navy rectangle bar."""
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
    """Logo on left, company name & address on right."""
    logo_path = _get_logo_path()

    navy_bold = ParagraphStyle(
        "NavyBold", fontName="Helvetica-Bold",
        fontSize=11, textColor=NAVY, alignment=TA_RIGHT,
    )
    navy_normal = ParagraphStyle(
        "NavyNormal", fontName="Helvetica",
        fontSize=9, textColor=NAVY, alignment=TA_RIGHT, leading=13,
    )

    company_block = [
        Paragraph(COMPANY_NAME, navy_bold),
        Paragraph(
            f"{COMPANY_ADDR1}<br/>{COMPANY_ADDR2}<br/>{COMPANY_ADDR3}",
            navy_normal
        ),
        Paragraph(f"&#9990; {COMPANY_PHONE}", navy_normal),
        Paragraph(f"Reg. No: {COMPANY_REG}", navy_normal),
    ]

    left_cell = RLImage(logo_path, width=22*mm, height=22*mm) \
                if logo_path else Paragraph("", ParagraphStyle("empty"))

    t = Table([[left_cell, company_block]],
              colWidths=[doc.width * 0.35, doc.width * 0.65])
    t.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return t


def _bill_to_block(inv_no, inv_date, due_date, doc):
    """Customer address (left) and invoice meta (right)."""
    normal = ParagraphStyle(
        "Normal2", fontName="Helvetica",
        fontSize=9, textColor=BLACK, leading=14,
    )
    bold_val = ParagraphStyle(
        "BoldVal", fontName="Helvetica-Bold",
        fontSize=9, textColor=BLACK, alignment=TA_RIGHT,
    )
    label_r = ParagraphStyle(
        "LabelR", fontName="Helvetica",
        fontSize=9, textColor=BLACK, alignment=TA_RIGHT,
    )

    left = [
        Paragraph(f"<b>{CUSTOMER_NAME}</b>", normal),
        Paragraph(CUSTOMER_ADDR1, normal),
        Paragraph(CUSTOMER_ADDR2, normal),
    ]

    meta_rows = [
        [Paragraph("Invoice No.  :", label_r),
         Paragraph(f"<b>{inv_no}</b>",   bold_val)],
        [Paragraph("Invoice Date :", label_r),
         Paragraph(f"<b>{inv_date}</b>", bold_val)],
        [Paragraph("Due Date     :", label_r),
         Paragraph(f"<b>{due_date}</b>", bold_val)],
    ]

    meta_table = Table(meta_rows, colWidths=[35*mm, 40*mm])
    meta_table.setStyle(TableStyle([
        ("LEFTPADDING",   (0, 0), (-1, -1), 2),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 2),
        ("TOPPADDING",    (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("ALIGN",         (0, 0), (-1, -1), "RIGHT"),
    ]))

    t = Table([[left, meta_table]],
              colWidths=[doc.width * 0.5, doc.width * 0.5])
    t.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return t


def _sessions_table(sessions, doc):
    """Sessions data table with navy header row."""
    th = ParagraphStyle(
        "TH", fontName="Helvetica-Bold", fontSize=9,
        textColor=WHITE, alignment=TA_CENTER, leading=12,
    )
    td = ParagraphStyle(
        "TD", fontName="Helvetica", fontSize=9,
        textColor=BLACK, alignment=TA_LEFT, leading=12,
    )
    tdc = ParagraphStyle(
        "TDC", fontName="Helvetica", fontSize=9,
        textColor=BLACK, alignment=TA_CENTER, leading=12,
    )
    tdr = ParagraphStyle(
        "TDR", fontName="Helvetica", fontSize=9,
        textColor=BLACK, alignment=TA_RIGHT, leading=12,
    )

    col_widths = [12*mm, 50*mm, 28*mm, 25*mm, 28*mm, 25*mm]

    rows = [[
        Paragraph("Sr.",              th),
        Paragraph("Activity",         th),
        Paragraph("Session /\nJob Date",  th),
        Paragraph("Session /\nHour Rate", th),
        Paragraph("Working\nHours",   th),
        Paragraph("Session\nTotal",   th),
    ]]

    for s in sessions:
        rows.append([
            Paragraph(str(s.get("sr_no", "")).zfill(2),              tdc),
            Paragraph(s.get("activity", "Locum GP session"),          td),
            Paragraph(format_date_for_display(s.get("job_date", "")), tdc),
            Paragraph(format_rate(s.get("hour_rate", 0)),             tdc),
            Paragraph(str(s.get("work_hours", "Duty Session")),       tdc),
            Paragraph(format_currency(s.get("session_total", 0)),     tdr),
        ])

    t = Table(rows, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, 0),  NAVY),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  WHITE),
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, LIGHT_GREY]),
        ("LINEBELOW",     (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("LINEABOVE",     (0, 0), (-1, 0),  1,   NAVY),
        ("LINEBELOW",     (0,-1), (-1, -1), 1,   NAVY),
        ("TOPPADDING",    (0, 0), (-1, -1), 5),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 5),
        ("LEFTPADDING",   (0, 0), (-1, -1), 4),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 4),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def _totals_block(ref, net_amt, due_amt, doc):
    """Ref on left, Net Amount / Due Amount on right."""
    normal = ParagraphStyle(
        "Norm3", fontName="Helvetica",
        fontSize=9, textColor=BLACK,
    )
    bold_right = ParagraphStyle(
        "BoldR", fontName="Helvetica-Bold",
        fontSize=10, textColor=BLACK, alignment=TA_RIGHT,
    )
    label_right = ParagraphStyle(
        "LabelRight", fontName="Helvetica",
        fontSize=9, textColor=BLACK, alignment=TA_RIGHT,
    )

    totals = Table(
        [
            [Paragraph("Net Amount :", label_right),
             Paragraph(f"<b>{net_amt}</b>", bold_right)],
            [Paragraph("Due Amount :", label_right),
             Paragraph(f"<b>{due_amt}</b>", bold_right)],
        ],
        colWidths=[35*mm, 40*mm],
    )
    totals.setStyle(TableStyle([
        ("LEFTPADDING",   (0, 0), (-1, -1), 2),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 2),
        ("TOPPADDING",    (0, 0), (-1, -1), 3),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 3),
    ]))

    t = Table([[Paragraph(f"Ref. :  {ref}", normal), totals]],
              colWidths=[doc.width * 0.5, doc.width * 0.5])
    t.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return t


def _bank_details(doc):
    """Bank details section."""
    bold = ParagraphStyle(
        "BankBold", fontName="Helvetica-Bold",
        fontSize=9, textColor=BLACK,
    )
    normal = ParagraphStyle(
        "BankNorm", fontName="Helvetica",
        fontSize=9, textColor=BLACK, leading=14,
    )

    inner = Table(
        [
            [Paragraph("Bank Name",          normal),
             Paragraph(":"),
             Paragraph(BANK_NAME,            normal)],
            [Paragraph("Account No.",        normal),
             Paragraph(":"),
             Paragraph(BANK_ACCOUNT,         normal)],
            [Paragraph("Sort / Branch Code", normal),
             Paragraph(":"),
             Paragraph(BANK_SORT,            normal)],
        ],
        colWidths=[40*mm, 6*mm, 60*mm],
        style=TableStyle([
            ("LEFTPADDING",   (0, 0), (-1, -1), 0),
            ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
            ("TOPPADDING",    (0, 0), (-1, -1), 1),
            ("BOTTOMPADDING", (0, 0), (-1, -1), 1),
        ]),
    )

    outer = Table(
        [
            [Paragraph(
                "<b>Bank Details:</b> Please make payments to the following Bank Account:",
                bold
            )],
            [Spacer(1, 3*mm)],
            [inner],
        ],
        colWidths=[doc.width],
    )
    outer.setStyle(TableStyle([
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
    ]))
    return outer
