import os
import subprocess
from reportlab.lib.pagesizes import A4
from reportlab.lib import colors
from reportlab.lib.units import mm
from reportlab.platypus import (
    SimpleDocTemplate, Paragraph, Spacer, Table, TableStyle
)
from reportlab.lib.styles import ParagraphStyle
from reportlab.lib.enums import TA_CENTER, TA_RIGHT, TA_LEFT
from reportlab.platypus import Image as RLImage
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.ttfonts import TTFont

from logic.invoice_logic import format_date_for_display, format_currency, format_rate

# ──────────────────────────────────────────────
#  FONT REGISTRATION
# ──────────────────────────────────────────────

def _register_fonts():
    """Register Poppins and Calibri fonts."""
    base = os.path.dirname(os.path.dirname(__file__))
    fonts_dir = os.path.join(base, "assets", "fonts")

    # Poppins
    try:
        pdfmetrics.registerFont(TTFont(
            "Poppins",
            os.path.join(fonts_dir, "Poppins-Regular.ttf")
        ))
        pdfmetrics.registerFont(TTFont(
            "Poppins-Bold",
            os.path.join(fonts_dir, "Poppins-Bold.ttf")
        ))
    except Exception:
        pass  # fallback to Helvetica

    # Calibri — load from Windows fonts
    calibri_paths = [
        r"C:\Windows\Fonts\calibri.ttf",
        r"C:\Windows\Fonts\Calibri.ttf",
        "/usr/share/fonts/truetype/msttcorefonts/Calibri.ttf",
    ]
    calibri_bold_paths = [
        r"C:\Windows\Fonts\calibrib.ttf",
        r"C:\Windows\Fonts\Calibrib.ttf",
        "/usr/share/fonts/truetype/msttcorefonts/Calibri_Bold.ttf",
    ]
    for path in calibri_paths:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont("Calibri", path))
            except Exception:
                pass
            break
    for path in calibri_bold_paths:
        if os.path.exists(path):
            try:
                pdfmetrics.registerFont(TTFont("Calibri-Bold", path))
            except Exception:
                pass
            break


_register_fonts()

# Check which fonts are available
def _poppins():
    try:
        pdfmetrics.getFont("Poppins")
        return "Poppins"
    except Exception:
        return "Helvetica"

def _poppins_bold():
    try:
        pdfmetrics.getFont("Poppins-Bold")
        return "Poppins-Bold"
    except Exception:
        return "Helvetica-Bold"

def _calibri():
    try:
        pdfmetrics.getFont("Calibri")
        return "Calibri"
    except Exception:
        return "Helvetica"

def _calibri_bold():
    try:
        pdfmetrics.getFont("Calibri-Bold")
        return "Calibri-Bold"
    except Exception:
        return "Helvetica-Bold"


# ──────────────────────────────────────────────
#  COMPANY CONSTANTS
# ──────────────────────────────────────────────

COMPANY_NAME   = "Twickenham Health Limited"
COMPANY_ADDR   = "1 Twickenham Grove,\nStoke-on-Trent, ST4 8WS,\nUnited Kingdom."
COMPANY_PHONE  = "07859 001684"
COMPANY_REG    = "16271052"

BANK_NAME      = "MONZO"
BANK_ACCOUNT   = "99909112"
BANK_SORT      = "04-00-03"

FOOTER_NOTE    = ("* This is system generated invoice doesn't require "
                  "signature or stamp.")

# Colours
NAVY        = colors.HexColor("#1a2c4e")
WHITE       = colors.white
BLACK       = colors.black
LIGHT_GREY  = colors.HexColor("#f5f5f5")
TEXT_GREY   = colors.HexColor("#555555")

# Output folder
OUTPUT_DIR = os.path.join(
    os.path.dirname(os.path.dirname(__file__)), "output"
)


# ──────────────────────────────────────────────
#  HELPERS
# ──────────────────────────────────────────────

def _ensure_output_dir():
    os.makedirs(OUTPUT_DIR, exist_ok=True)


def _get_logo_path():
    base = os.path.dirname(os.path.dirname(__file__))
    for name in ["twickenham_health_logo.png", "logo.png",
                 "logo.jpg", "logo.jpeg"]:
        path = os.path.join(base, "assets", name)
        if os.path.exists(path):
            return path
    return None


def get_output_folder() -> str:
    return OUTPUT_DIR


def open_output_folder():
    os.makedirs(OUTPUT_DIR, exist_ok=True)
    try:
        os.startfile(OUTPUT_DIR)
    except Exception:
        subprocess.Popen(f'start "" "{OUTPUT_DIR}"', shell=True)


# ──────────────────────────────────────────────
#  OPEN / PRINT PDF
# ──────────────────────────────────────────────

def open_pdf(pdf_path: str) -> bool:
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


def generate_and_open(invoice: dict) -> tuple:
    try:
        pdf_path = generate_pdf(invoice)
        if open_pdf(pdf_path):
            return True, pdf_path
        return False, f"PDF saved but could not open:\n{pdf_path}"
    except Exception as e:
        return False, f"Failed to generate PDF:\n{str(e)}"


def generate_and_print(invoice: dict) -> tuple:
    return generate_and_open(invoice)


# ──────────────────────────────────────────────
#  MAIN PDF GENERATOR
# ──────────────────────────────────────────────

def generate_pdf(invoice: dict) -> str:
    _ensure_output_dir()

    inv_no   = invoice.get("inv_no", "")
    inv_date = format_date_for_display(invoice.get("inv_date", ""))
    due_date = format_date_for_display(invoice.get("due_date", ""))
    ref      = invoice.get("ref", "") or ""
    net_amt  = format_currency(invoice.get("net_amount", 0))
    due_amt  = format_currency(invoice.get("due_amount", 0))
    sessions = invoice.get("sessions", [])

    # Customer from DB — fallback to blank
    cust_name    = invoice.get("customer_name",    "")
    cust_address = invoice.get("customer_address", "")

    filename = os.path.join(OUTPUT_DIR, f"{inv_no}.pdf")

    doc = SimpleDocTemplate(
        filename,
        pagesize=A4,
        leftMargin=20*mm,
        rightMargin=20*mm,
        topMargin=0,
        bottomMargin=0,
        title=f"Twickenham Health — {inv_no}",
        author="Twickenham Health Limited",
    )

    story = []

    # 1. Top navy bar
    story.append(_navy_bar(doc))
    story.append(Spacer(1, 6*mm))

    # 2. Company header (Poppins)
    story.append(_company_header(doc))
    story.append(Spacer(1, 8*mm))

    # 3. "Invoice to Customer" heading (Poppins Bold, large, underlined)
    heading_style = ParagraphStyle(
        "Heading",
        fontName=_poppins_bold(),
        fontSize=20,
        textColor=BLACK,
        alignment=TA_CENTER,
        leading=26,
    )
    story.append(Paragraph("<u>Invoice to Customer</u>", heading_style))
    story.append(Spacer(1, 10*mm))

    # 4. Bill To block (Calibri)
    story.append(_bill_to_block(inv_no, inv_date, due_date,
                                cust_name, cust_address, doc))
    story.append(Spacer(1, 6*mm))

    # 5. Sessions table (Calibri)
    story.append(_sessions_table(sessions, doc))
    story.append(Spacer(1, 8*mm))

    # 6. Totals block (Calibri)
    story.append(_totals_block(ref, net_amt, due_amt, doc))
    story.append(Spacer(1, 10*mm))

    # 7. Bank details (Calibri)
    story.append(_bank_details(doc))
    story.append(Spacer(1, 16*mm))

    # 8. Footer note (Calibri small)
    footer_style = ParagraphStyle(
        "Footer",
        fontName=_calibri(),
        fontSize=9,
        textColor=TEXT_GREY,
        alignment=TA_LEFT,
    )
    story.append(Paragraph(FOOTER_NOTE, footer_style))
    story.append(Spacer(1, 6*mm))

    # 9. Bottom navy bar
    story.append(_navy_bar(doc))

    doc.build(story)
    return filename


# ──────────────────────────────────────────────
#  SECTION BUILDERS
# ──────────────────────────────────────────────

def _navy_bar(doc):
    """Thin full-width navy bar."""
    t = Table([[""]], colWidths=[doc.width + doc.leftMargin + doc.rightMargin])
    t.setStyle(TableStyle([
        ("BACKGROUND",    (0, 0), (-1, -1), NAVY),
        ("TOPPADDING",    (0, 0), (-1, -1), 4),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 4),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
    ]))
    return t


def _company_header(doc):
    """Logo left, company details right — Poppins fonts."""
    logo_path = _get_logo_path()

    name_style = ParagraphStyle(
        "CName",
        fontName=_poppins_bold(),
        fontSize=11,
        textColor=NAVY,
        alignment=TA_RIGHT,
        leading=15,
    )
    detail_style = ParagraphStyle(
        "CDetail",
        fontName=_poppins(),
        fontSize=8,
        textColor=NAVY,
        alignment=TA_RIGHT,
        leading=13,
    )

    right_col = [
        Paragraph(COMPANY_NAME, name_style),
        Paragraph(
            "&#9679; 1 Twickenham Grove,<br/>"
            "Stoke-on-Trent, ST4 8WS,<br/>"
            "United Kingdom.",
            detail_style
        ),
        Paragraph(f"&#9990; {COMPANY_PHONE}", detail_style),
        Paragraph(f"&#x2198; Reg. No: {COMPANY_REG}", detail_style),
    ]

    logo_cell = RLImage(logo_path, width=30*mm, height=30*mm) \
                if logo_path else Paragraph("", ParagraphStyle("empty"))

    t = Table([[logo_cell, right_col]],
              colWidths=[doc.width * 0.35, doc.width * 0.65])
    t.setStyle(TableStyle([
        ("VALIGN",        (0, 0), (-1, -1), "TOP"),
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return t


def _bill_to_block(inv_no, inv_date, due_date, cust_name, cust_address, doc):
    """Customer address (left) + invoice meta (right) — Calibri."""
    normal = ParagraphStyle(
        "BillNorm",
        fontName=_calibri(),
        fontSize=12,
        textColor=BLACK,
        leading=18,
    )
    label_style = ParagraphStyle(
        "MetaLabel",
        fontName=_calibri(),
        fontSize=12,
        textColor=BLACK,
        alignment=TA_LEFT,
        leading=20,
    )
    bold_val = ParagraphStyle(
        "MetaVal",
        fontName=_calibri_bold(),
        fontSize=12,
        textColor=BLACK,
        alignment=TA_RIGHT,
        leading=20,
    )

    # Split address into lines
    addr_lines = [l.strip() for l in
                  cust_address.replace(",\n", "\n").replace(", ", "\n")
                  .split("\n") if l.strip()]

    left_content = [Paragraph(cust_name, normal)]
    for line in addr_lines:
        left_content.append(Paragraph(line, normal))

    meta_rows = [
        [Paragraph("Invoice No.", label_style),
         Paragraph(":", label_style),
         Paragraph(f"<b>{inv_no}</b>", bold_val)],
        [Paragraph("Invoice Date", label_style),
         Paragraph(":", label_style),
         Paragraph(f"<b>{inv_date}</b>", bold_val)],
        [Paragraph("Due Date", label_style),
         Paragraph(":", label_style),
         Paragraph(f"<b>{due_date}</b>", bold_val)],
    ]

    meta_table = Table(meta_rows, colWidths=[28*mm, 6*mm, 38*mm])
    meta_table.setStyle(TableStyle([
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))

    t = Table([[left_content, meta_table]],
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
    """Sessions table — Calibri, navy header."""
    th = ParagraphStyle(
        "TH",
        fontName=_calibri_bold(),
        fontSize=12,
        textColor=WHITE,
        alignment=TA_CENTER,
        leading=15,
    )
    td = ParagraphStyle(
        "TD",
        fontName=_calibri(),
        fontSize=12,
        textColor=BLACK,
        alignment=TA_LEFT,
        leading=15,
    )
    tdc = ParagraphStyle(
        "TDC",
        fontName=_calibri(),
        fontSize=12,
        textColor=BLACK,
        alignment=TA_CENTER,
        leading=15,
    )
    tdr = ParagraphStyle(
        "TDR",
        fontName=_calibri(),
        fontSize=12,
        textColor=BLACK,
        alignment=TA_RIGHT,
        leading=15,
    )

    col_widths = [14*mm, 52*mm, 28*mm, 26*mm, 30*mm, 26*mm]

    rows = [[
        Paragraph("Sr.",                   th),
        Paragraph("Activity",              th),
        Paragraph("Session /\nJob Date",   th),
        Paragraph("Session /\nHour Rate",  th),
        Paragraph("Working\nHours",        th),
        Paragraph("Session\nTotal",        th),
    ]]

    for s in sessions:
        rows.append([
            Paragraph(str(s.get("sr_no", "")).zfill(2),               tdc),
            Paragraph(s.get("activity", "Locum GP session"),           td),
            Paragraph(format_date_for_display(s.get("job_date", "")),  tdc),
            Paragraph(format_rate(s.get("hour_rate", 0)),              tdc),
            Paragraph(str(s.get("work_hours", "")),                    tdc),
            Paragraph(format_currency(s.get("session_total", 0)),      tdr),
        ])

    t = Table(rows, colWidths=col_widths, repeatRows=1)
    t.setStyle(TableStyle([
        # Header
        ("BACKGROUND",    (0, 0), (-1, 0),  NAVY),
        ("TEXTCOLOR",     (0, 0), (-1, 0),  WHITE),
        # Alternating rows
        ("ROWBACKGROUNDS",(0, 1), (-1, -1), [WHITE, LIGHT_GREY]),
        # Borders
        ("LINEBELOW",     (0, 0), (-1, -1), 0.5, colors.HexColor("#cccccc")),
        ("LINEABOVE",     (0, 0), (-1,  0), 1,   NAVY),
        ("LINEBELOW",     (0,-1), (-1, -1), 1,   NAVY),
        # No side borders
        ("LEFTPADDING",   (0, 0), (-1, -1), 6),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 6),
        ("TOPPADDING",    (0, 0), (-1, -1), 7),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 7),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))
    return t


def _totals_block(ref, net_amt, due_amt, doc):
    """Ref left, Net/Due amounts right — Calibri."""
    norm = ParagraphStyle(
        "TotNorm",
        fontName=_calibri(),
        fontSize=12,
        textColor=BLACK,
    )
    label_r = ParagraphStyle(
        "TotLabel",
        fontName=_calibri(),
        fontSize=12,
        textColor=BLACK,
        alignment=TA_RIGHT,
        leading=22,
    )
    bold_r = ParagraphStyle(
        "TotBold",
        fontName=_calibri_bold(),
        fontSize=12,
        textColor=BLACK,
        alignment=TA_RIGHT,
        leading=22,
    )

    totals = Table(
        [
            [Paragraph("Net Amount:", label_r),
             Paragraph(f"<b>{net_amt}</b>", bold_r)],
            [Spacer(1, 4*mm), ""],
            [Paragraph("Due Amount :", label_r),
             Paragraph(f"<b>{due_amt}</b>", bold_r)],
        ],
        colWidths=[35*mm, 40*mm],
    )
    totals.setStyle(TableStyle([
        ("LEFTPADDING",   (0, 0), (-1, -1), 2),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))

    t = Table([[Paragraph(f"Ref. :  {ref}", norm), totals]],
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
    """Bank details — Calibri."""
    bold = ParagraphStyle(
        "BankBold",
        fontName=_calibri_bold(),
        fontSize=12,
        textColor=BLACK,
    )
    norm = ParagraphStyle(
        "BankNorm",
        fontName=_calibri(),
        fontSize=12,
        textColor=BLACK,
        leading=18,
    )

    header = Paragraph(
        "<b>Bank Details:</b> Please make payments to the following Bank Account:",
        bold
    )

    rows = Table(
        [
            [Paragraph("Bank Name",          norm),
             Paragraph(":",                  norm),
             Paragraph(BANK_NAME,            norm)],
            [Paragraph("Account No.",        norm),
             Paragraph(":",                  norm),
             Paragraph(BANK_ACCOUNT,         norm)],
            [Paragraph("Sort / Branch Code", norm),
             Paragraph(":",                  norm),
             Paragraph(BANK_SORT,            norm)],
        ],
        colWidths=[40*mm, 8*mm, 60*mm],
    )
    rows.setStyle(TableStyle([
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 2),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 2),
        ("VALIGN",        (0, 0), (-1, -1), "MIDDLE"),
    ]))

    outer = Table(
        [[header], [Spacer(1, 4*mm)], [rows]],
        colWidths=[doc.width],
    )
    outer.setStyle(TableStyle([
        ("LEFTPADDING",   (0, 0), (-1, -1), 0),
        ("RIGHTPADDING",  (0, 0), (-1, -1), 0),
        ("TOPPADDING",    (0, 0), (-1, -1), 0),
        ("BOTTOMPADDING", (0, 0), (-1, -1), 0),
    ]))
    return outer
