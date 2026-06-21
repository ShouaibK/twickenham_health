import ctypes
import os
import subprocess
import time

# ──────────────────────────────────────────────
#  GENERATE + OPEN  (convenience wrapper)
# ──────────────────────────────────────────────

def generate_and_open(invoice: dict) -> tuple[bool, str]:
    """
    Generate the PDF for an invoice then open it in the default viewer.

    invoice = full invoice dict from db.get_invoice_by_id()

    Returns (True, pdf_path) on success or (False, error_message).
    """
    try:
        from logic.pdf_generator import generate_pdf
        pdf_path = generate_pdf(invoice)
        opened   = open_pdf(pdf_path)
        if opened:
            return True, pdf_path
        return False, f"PDF saved but could not open:\n{pdf_path}"
    except Exception as e:
        return False, f"Failed to generate PDF:\n{str(e)}"


def generate_and_print(invoice: dict) -> tuple[bool, str]:
    """
    Generate the PDF for an invoice then send it to the printer.

    Returns (True, pdf_path) on success or (False, error_message).
    """
    try:
        from logic.pdf_generator import generate_pdf
        pdf_path = generate_pdf(invoice)
        ok, msg  = print_pdf(pdf_path)
        if ok:
            return True, pdf_path
        return False, msg
    except Exception as e:
        return False, f"Failed to generate or print PDF:\n{str(e)}"


# ──────────────────────────────────────────────
#  OUTPUT FOLDER HELPER
# ──────────────────────────────────────────────

def get_output_folder() -> str:
    """Return the path to the output/ folder where PDFs are saved."""
    base = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(base, "output")


import os
import subprocess


# Minimal printer helper: only generate PDFs and open them in the default viewer.


def open_pdf(pdf_path: str) -> bool:
    """Open a PDF file in the default system viewer. Returns True on success."""
    if not os.path.exists(pdf_path):
        return False
    try:
        # On Windows, os.startfile will open the file in the default app.
        os.startfile(pdf_path)
        return True
    except Exception:
        # Try a generic fallback using start (should be equivalent on Windows)
        try:
            subprocess.Popen(f'start "" "{pdf_path}"', shell=True)
            return True
        except Exception:
            return False


def generate_and_open(invoice: dict) -> tuple[bool, str]:
    """Generate the PDF for an invoice then open it in the default viewer.

    Returns (True, pdf_path) on success or (False, error_message).
    """
    try:
        from logic.pdf_generator import generate_pdf
        pdf_path = generate_pdf(invoice)
        opened = open_pdf(pdf_path)
        if opened:
            return True, pdf_path
        return False, f"PDF saved but could not open:\n{pdf_path}"
    except Exception as e:
        return False, f"Failed to generate PDF:\n{str(e)}"


def generate_and_print(invoice: dict) -> tuple[bool, str]:
    """Compatibility wrapper: generate the PDF and open it in the default viewer.

    This project no longer attempts to invoke the system print dialog directly.
    Calling this will open the generated PDF so the user can print from their
    preferred viewer.
    """
    return generate_and_open(invoice)


def get_output_folder() -> str:
    """Return the path to the output/ folder where PDFs are saved."""
    base = os.path.dirname(os.path.dirname(__file__))
    return os.path.join(base, "output")


def open_output_folder():
    """Open the output/ folder in Windows Explorer."""
    folder = get_output_folder()
    os.makedirs(folder, exist_ok=True)
    try:
        os.startfile(folder)
    except Exception:
        subprocess.Popen(f'start "" "{folder}"', shell=True)
