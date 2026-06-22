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
            customer_id INTEGER DEFAULT NULL,
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

        CREATE TABLE IF NOT EXISTS customers (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            name       TEXT NOT NULL,
            address    TEXT DEFAULT '',
            contact    TEXT DEFAULT '',
            created_at TEXT DEFAULT CURRENT_TIMESTAMP
        );
    """)

    # Migration: add customer_id column if it doesn't exist (for existing DBs)
    try:
        cursor.execute("ALTER TABLE invoices ADD COLUMN customer_id INTEGER DEFAULT NULL")
        conn.commit()
    except Exception:
        pass  # column already exists

    # Seed default customer if table is empty
    cursor.execute("SELECT COUNT(*) FROM customers")
    if cursor.fetchone()[0] == 0:
        cursor.execute(
            "INSERT INTO customers (name, address, contact) VALUES (?, ?, ?)",
            (
                "Allen Street Clinic",
                "Allen Street, Stoke-On-Trent ST10 1HJ, United Kingdom",
                "",
            ),
        )
        conn.commit()

    # Back-fill existing invoices that have no customer_id → assign default customer
    cursor.execute("SELECT id FROM customers ORDER BY id LIMIT 1")
    default_row = cursor.fetchone()
    if default_row:
        cursor.execute(
            "UPDATE invoices SET customer_id = ? WHERE customer_id IS NULL",
            (default_row[0],)
        )
        conn.commit()

    conn.commit()
    conn.close()


# ──────────────────────────────────────────────
#  INVOICE CRUD
# ──────────────────────────────────────────────

def save_invoice(inv_no, inv_date, due_date, ref,
                 net_amount, due_amount, sessions, customer_id=None):
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
                (inv_no, inv_date, due_date, ref, net_amount, due_amount,
                 status, customer_id)
            VALUES (?, ?, ?, ?, ?, ?, 'pending', ?)
        """, (inv_no, inv_date, due_date, ref, net_amount, due_amount,
              customer_id))

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
                   net_amount, due_amount, sessions, customer_id=None):
    """
    Update an existing invoice and replace all its sessions.
    Returns True on success, False on duplicate inv_no.
    """
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            UPDATE invoices
               SET inv_no      = ?,
                   inv_date    = ?,
                   due_date    = ?,
                   ref         = ?,
                   net_amount  = ?,
                   due_amount  = ?,
                   customer_id = ?
             WHERE id = ?
        """, (inv_no, inv_date, due_date, ref,
              net_amount, due_amount, customer_id, invoice_id))

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
            SELECT i.id, i.inv_no, i.inv_date, i.due_date, i.ref,
                   i.net_amount, i.due_amount, i.status, i.created_at,
                   i.customer_id,
                   COALESCE(c.name, 'Unknown') AS customer_name,
                   COALESCE(c.address, '')     AS customer_address,
                   COALESCE(c.contact, '')     AS customer_contact,
                   (SELECT COUNT(*) FROM sessions
                     WHERE invoice_id = i.id)  AS session_count
              FROM invoices i
              LEFT JOIN customers c ON c.id = i.customer_id
             WHERE i.inv_no   LIKE ?
                OR i.inv_date LIKE ?
                OR i.due_date LIKE ?
                OR i.ref      LIKE ?
                OR i.status   LIKE ?
                OR c.name     LIKE ?
            ORDER BY i.created_at DESC
        """, (pattern, pattern, pattern, pattern, pattern, pattern))
    else:
        cursor.execute("""
            SELECT i.id, i.inv_no, i.inv_date, i.due_date, i.ref,
                   i.net_amount, i.due_amount, i.status, i.created_at,
                   i.customer_id,
                   COALESCE(c.name, 'Unknown') AS customer_name,
                   COALESCE(c.address, '')     AS customer_address,
                   COALESCE(c.contact, '')     AS customer_contact,
                   (SELECT COUNT(*) FROM sessions
                     WHERE invoice_id = i.id)  AS session_count
              FROM invoices i
              LEFT JOIN customers c ON c.id = i.customer_id
             ORDER BY i.created_at DESC
        """)

    rows = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return rows


def get_invoice_by_id(invoice_id):
    """Return a single invoice dict with its sessions list."""
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT i.*,
               COALESCE(c.name,    'Unknown') AS customer_name,
               COALESCE(c.address, '')        AS customer_address,
               COALESCE(c.contact, '')        AS customer_contact
          FROM invoices i
          LEFT JOIN customers c ON c.id = i.customer_id
         WHERE i.id = ?
    """, (invoice_id,))
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


# ──────────────────────────────────────────────
#  CUSTOMER CRUD
# ──────────────────────────────────────────────

def get_all_customers(search: str = "") -> list:
    """Return all customers ordered by name, optionally filtered."""
    conn   = get_connection()
    cursor = conn.cursor()
    if search:
        like = f"%{search}%"
        cursor.execute(
            "SELECT id, name, address, contact FROM customers "
            "WHERE name LIKE ? OR contact LIKE ? "
            "ORDER BY name COLLATE NOCASE",
            (like, like),
        )
    else:
        cursor.execute(
            "SELECT id, name, address, contact FROM customers "
            "ORDER BY name COLLATE NOCASE"
        )
    rows = cursor.fetchall()
    conn.close()
    return [{"id": r["id"], "name": r["name"],
             "address": r["address"], "contact": r["contact"]} for r in rows]


def get_customer_by_id(customer_id: int):
    """Return a single customer dict or None."""
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "SELECT id, name, address, contact FROM customers WHERE id = ?",
        (customer_id,),
    )
    row = cursor.fetchone()
    conn.close()
    if row is None:
        return None
    return {"id": row["id"], "name": row["name"],
            "address": row["address"], "contact": row["contact"]}


def add_customer(name: str, address: str, contact: str) -> int:
    """Insert a new customer and return its new id."""
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "INSERT INTO customers (name, address, contact) VALUES (?, ?, ?)",
        (name.strip(), address.strip(), contact.strip()),
    )
    new_id = cursor.lastrowid
    conn.commit()
    conn.close()
    return new_id


def update_customer(customer_id: int, name: str,
                    address: str, contact: str) -> None:
    """Update an existing customer record."""
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE customers SET name=?, address=?, contact=? WHERE id=?",
        (name.strip(), address.strip(), contact.strip(), customer_id),
    )
    conn.commit()
    conn.close()


def delete_customer(customer_id: int) -> None:
    """Delete a customer by id."""
    conn   = get_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM customers WHERE id = ?", (customer_id,))
    conn.commit()
    conn.close()

