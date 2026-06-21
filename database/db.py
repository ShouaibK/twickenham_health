import sqlite3
import os
from datetime import datetime

# Database file path — sits inside the database/ folder
DB_PATH = os.path.join(os.path.dirname(__file__), "invoices.db")


def get_connection():
    """Return a SQLite connection with foreign keys enabled."""
    conn = sqlite3.connect(DB_PATH)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn


def initialise_db():
    """Create tables on first run if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.executescript("""
        CREATE TABLE IF NOT EXISTS invoices (
            id          INTEGER PRIMARY KEY AUTOINCREMENT,
            inv_no      TEXT    NOT NULL UNIQUE,
            inv_date    TEXT    NOT NULL,
            due_date    TEXT    NOT NULL,
            ref         TEXT    DEFAULT '',
            net_amount  REAL    NOT NULL DEFAULT 0.0,
            due_amount  REAL    NOT NULL DEFAULT 0.0,
            status      TEXT    NOT NULL DEFAULT 'pending',
            created_at  TEXT    DEFAULT CURRENT_TIMESTAMP
        );

        CREATE TABLE IF NOT EXISTS sessions (
            id            INTEGER PRIMARY KEY AUTOINCREMENT,
            invoice_id    INTEGER NOT NULL,
            sr_no         INTEGER NOT NULL,
            activity      TEXT    NOT NULL DEFAULT 'Locum GP session',
            job_date      TEXT    NOT NULL,
            hour_rate     REAL    NOT NULL DEFAULT 0.0,
            work_hours    TEXT    NOT NULL DEFAULT 'Duty Session',
            session_total REAL    NOT NULL DEFAULT 0.0,
            FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
        );
    """)

    conn.commit()
    conn.close()


# ──────────────────────────────────────────────
#  INVOICE CRUD
# ──────────────────────────────────────────────

def save_invoice(inv_no, inv_date, due_date, ref,
                 net_amount, due_amount, sessions):
    """
    Insert a new invoice and its sessions.
    sessions = list of dicts with keys:
        sr_no, activity, job_date, hour_rate, work_hours, session_total
    Returns the new invoice id, or None on error.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            INSERT INTO invoices
                (inv_no, inv_date, due_date, ref, net_amount, due_amount, status)
            VALUES (?, ?, ?, ?, ?, ?, 'pending')
        """, (inv_no, inv_date, due_date, ref, net_amount, due_amount))

        invoice_id = cursor.lastrowid

        for s in sessions:
            cursor.execute("""
                INSERT INTO sessions
                    (invoice_id, sr_no, activity, job_date,
                     hour_rate, work_hours, session_total)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                invoice_id,
                s["sr_no"],
                s["activity"],
                s["job_date"],
                s["hour_rate"],
                s["work_hours"],
                s["session_total"],
            ))

        conn.commit()
        return invoice_id

    except sqlite3.IntegrityError:
        # Duplicate invoice number
        conn.rollback()
        return None
    finally:
        conn.close()


def update_invoice(invoice_id, inv_no, inv_date, due_date, ref,
                   net_amount, due_amount, sessions):
    """
    Update an existing invoice and replace all its sessions.
    Returns True on success, False on duplicate inv_no.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE invoices
               SET inv_no     = ?,
                   inv_date   = ?,
                   due_date   = ?,
                   ref        = ?,
                   net_amount = ?,
                   due_amount = ?
             WHERE id = ?
        """, (inv_no, inv_date, due_date, ref,
              net_amount, due_amount, invoice_id))

        # Delete old sessions then re-insert
        cursor.execute("DELETE FROM sessions WHERE invoice_id = ?",
                       (invoice_id,))

        for s in sessions:
            cursor.execute("""
                INSERT INTO sessions
                    (invoice_id, sr_no, activity, job_date,
                     hour_rate, work_hours, session_total)
                VALUES (?, ?, ?, ?, ?, ?, ?)
            """, (
                invoice_id,
                s["sr_no"],
                s["activity"],
                s["job_date"],
                s["hour_rate"],
                s["work_hours"],
                s["session_total"],
            ))

        conn.commit()
        return True

    except sqlite3.IntegrityError:
        conn.rollback()
        return False
    finally:
        conn.close()


def delete_invoice(invoice_id):
    """Permanently delete an invoice and all its sessions."""
    conn = get_connection()
    conn.execute("DELETE FROM invoices WHERE id = ?", (invoice_id,))
    conn.commit()
    conn.close()


def mark_as_paid(invoice_id):
    """Set invoice status to paid."""
    conn = get_connection()
    conn.execute("UPDATE invoices SET status = 'paid' WHERE id = ?",
                 (invoice_id,))
    conn.commit()
    conn.close()


def mark_as_pending(invoice_id):
    """Set invoice status back to pending."""
    conn = get_connection()
    conn.execute("UPDATE invoices SET status = 'pending' WHERE id = ?",
                 (invoice_id,))
    conn.commit()
    conn.close()


# ──────────────────────────────────────────────
#  FETCH / SEARCH
# ──────────────────────────────────────────────

def get_all_invoices(search=""):
    """
    Return all invoices as a list of dicts, newest first.
    Optionally filter by invoice number, date, due date, reference, or status.
    """
    conn = get_connection()
    cursor = conn.cursor()

    if search:
        pattern = f"%{search}%"
        cursor.execute("""
            SELECT id, inv_no, inv_date, due_date, ref,
                   net_amount, due_amount, status, created_at,
                   (SELECT COUNT(*) FROM sessions WHERE invoice_id = invoices.id) AS session_count
              FROM invoices
             WHERE inv_no   LIKE ?
                OR inv_date LIKE ?
                OR due_date LIKE ?
                OR ref      LIKE ?
                OR status   LIKE ?
                OR 'Allen Street Clinic' LIKE ?
            ORDER BY created_at DESC
        """, (pattern, pattern, pattern, pattern, pattern, pattern))
    else:
        cursor.execute("""
            SELECT id, inv_no, inv_date, due_date, ref,
                   net_amount, due_amount, status, created_at,
                   (SELECT COUNT(*) FROM sessions WHERE invoice_id = invoices.id) AS session_count
              FROM invoices
             ORDER BY created_at DESC
        """)

    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_invoice_by_id(invoice_id):
    """Return a single invoice dict with its sessions list."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM invoices WHERE id = ?", (invoice_id,))
    row = cursor.fetchone()
    if not row:
        conn.close()
        return None

    invoice = dict(row)

    cursor.execute("""
        SELECT * FROM sessions
         WHERE invoice_id = ?
         ORDER BY sr_no ASC
    """, (invoice_id,))

    invoice["sessions"] = [dict(s) for s in cursor.fetchall()]
    conn.close()
    return invoice


def invoice_number_exists(inv_no, exclude_id=None):
    """Check if an invoice number is already taken (for validation)."""
    conn = get_connection()
    cursor = conn.cursor()
    if exclude_id:
        cursor.execute(
            "SELECT id FROM invoices WHERE inv_no = ? AND id != ?",
            (inv_no, exclude_id))
    else:
        cursor.execute(
            "SELECT id FROM invoices WHERE inv_no = ?", (inv_no,))
    exists = cursor.fetchone() is not None
    conn.close()
    return exists


# ──────────────────────────────────────────────
#  DASHBOARD STATS
# ──────────────────────────────────────────────

def get_stats():
    """Return summary stats for the status bar."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) FROM invoices")
    total = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM invoices WHERE status = 'paid'")
    paid = cursor.fetchone()[0]

    cursor.execute(
        "SELECT COUNT(*) FROM invoices WHERE status IN ('pending','overdue')")
    pending = cursor.fetchone()[0]

    cursor.execute("SELECT COALESCE(SUM(net_amount), 0) FROM invoices")
    total_earned = cursor.fetchone()[0]

    conn.close()
    return {
        "total":        total,
        "paid":         paid,
        "pending":      pending,
        "total_earned": total_earned,
    }
