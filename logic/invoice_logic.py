from datetime import datetime, timedelta


# ──────────────────────────────────────────────
#  DATE HELPERS
# ──────────────────────────────────────────────

def today_str():
    """Return today's date as YYYY-MM-DD (for database storage)."""
    return datetime.today().strftime("%Y-%m-%d")


def default_due_date_str():
    """
    Return today + 20 days as YYYY-MM-DD.
    If that date falls on a Saturday (weekday=5) → shift to Monday (+2).
    If it falls on a Sunday  (weekday=6) → shift to Monday (+1).
    """
    due = datetime.today() + timedelta(days=20)
    if due.weekday() == 5:    # Saturday
        due += timedelta(days=2)
    elif due.weekday() == 6:  # Sunday
        due += timedelta(days=1)
    return due.strftime("%Y-%m-%d")


def calculate_due_date_str(invoice_date_str):
    """
    Calculate due date from a given invoice date string (YYYY-MM-DD).
    20 days later, shifted to Monday if it lands on a weekend.
    Returns YYYY-MM-DD string.
    """
    try:
        inv_date = datetime.strptime(invoice_date_str, "%Y-%m-%d")
    except ValueError:
        return default_due_date_str()
    due = inv_date + timedelta(days=20)
    if due.weekday() == 5:    # Saturday → Monday
        due += timedelta(days=2)
    elif due.weekday() == 6:  # Sunday → Monday
        due += timedelta(days=1)
    return due.strftime("%Y-%m-%d")


def format_date_for_display(date_str):
    """
    Convert YYYY-MM-DD  →  26-Dec-2025  (for UI and PDF display).
    Returns original string if parsing fails.
    """
    try:
        dt = datetime.strptime(date_str, "%Y-%m-%d")
        return dt.strftime("%d-%b-%Y")
    except ValueError:
        return date_str


def format_date_for_db(date_str):
    """
    Convert DD-Mon-YYYY  →  YYYY-MM-DD  (for database storage).
    Also accepts YYYY-MM-DD unchanged.
    Returns original string if parsing fails.
    """
    for fmt in ("%d-%b-%Y", "%Y-%m-%d", "%d/%m/%Y"):
        try:
            return datetime.strptime(date_str, fmt).strftime("%Y-%m-%d")
        except ValueError:
            continue
    return date_str


# ──────────────────────────────────────────────
#  SESSION CALCULATIONS
# ──────────────────────────────────────────────

def calculate_session_total(hour_rate, work_hours):
    """
    Calculate the total for one session row.

    Rules (from SKILL.md):
      - If work_hours is numeric  →  rate × hours
      - If work_hours is text
        (e.g. 'Duty Session')    →  rate as-is (flat fee)

    Returns a float.
    """
    try:
        rate = float(hour_rate)
    except (ValueError, TypeError):
        return 0.0

    try:
        hours = float(work_hours)
        return round(rate * hours, 2)
    except (ValueError, TypeError):
        # Non-numeric work_hours → flat rate
        return round(rate, 2)


def calculate_totals(sessions):
    """
    Given a list of session dicts, return (net_amount, due_amount).
    due_amount always equals net_amount (no VAT/tax).

    Each session dict must have keys: hour_rate, work_hours.
    """
    net = sum(
        calculate_session_total(s.get("hour_rate", 0),
                                s.get("work_hours", "Duty Session"))
        for s in sessions
    )
    net = round(net, 2)
    return net, net   # due_amount == net_amount


# ──────────────────────────────────────────────
#  FORMATTING HELPERS
# ──────────────────────────────────────────────

def format_currency(amount):
    """Format a float as  £1,685.00"""
    try:
        return f"£{float(amount):,.2f}"
    except (ValueError, TypeError):
        return "£0.00"


def format_rate(amount):
    """Format a float as  £350.00  (no thousands separator for rates)."""
    try:
        return f"£{float(amount):.2f}"
    except (ValueError, TypeError):
        return "£0.00"


# ──────────────────────────────────────────────
#  INVOICE NUMBER VALIDATION
# ──────────────────────────────────────────────

def validate_invoice_number(inv_no):
    """
    Check the invoice number follows the THL-GP### pattern.
    Returns (True, "") or (False, error_message).
    """
    inv_no = inv_no.strip().upper()
    if not inv_no:
        return False, "Invoice number cannot be empty."
    if not inv_no.startswith("THL-GP"):
        return False, "Invoice number must start with THL-GP (e.g. THL-GP041)."
    suffix = inv_no[6:]
    if not suffix.isdigit():
        return False, "Invoice number must end with digits (e.g. THL-GP041)."
    return True, ""


def validate_invoice_data(inv_no, inv_date, due_date, sessions):
    """
    Full validation before saving.
    Returns (True, "") or (False, error_message).
    """
    ok, msg = validate_invoice_number(inv_no)
    if not ok:
        return False, msg

    if not inv_date:
        return False, "Invoice date is required."

    if not due_date:
        return False, "Due date is required."

    if not sessions or len(sessions) == 0:
        return False, "Please add at least one session."

    for i, s in enumerate(sessions, 1):
        if not s.get("job_date"):
            return False, f"Session {i}: job date is required."
        try:
            rate = float(s.get("hour_rate", 0))
            if rate <= 0:
                return False, f"Session {i}: hour rate must be greater than 0."
        except (ValueError, TypeError):
            return False, f"Session {i}: hour rate must be a number."

    return True, ""


# ──────────────────────────────────────────────
#  SESSION BUILDER
# ──────────────────────────────────────────────

def build_session_list(raw_sessions):
    """
    Take raw session data from the UI form and return a clean list
    ready for db.save_invoice() or db.update_invoice().

    raw_sessions = list of dicts with keys:
        activity, job_date, hour_rate, work_hours
    """
    result = []
    for i, s in enumerate(raw_sessions, 1):
        hour_rate = float(s.get("hour_rate", 0) or 0)
        work_hours = str(s.get("work_hours", "Duty Session")).strip()
        total = calculate_session_total(hour_rate, work_hours)
        result.append({
            "sr_no":         i,
            "activity":      s.get("activity", "Locum GP session").strip(),
            "job_date":      format_date_for_db(s.get("job_date", "")),
            "hour_rate":     hour_rate,
            "work_hours":    work_hours,
            "session_total": total,
        })
    return result
