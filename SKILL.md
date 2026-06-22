---
name: twickenham-health-invoice-app
description: >
  Use this skill whenever working on the Twickenham Health Limited Locum GP
  Invoice desktop application. Covers all coding tasks including UI screens,
  database operations, PDF generation, records report, printing, packaging
  to .exe, and maintenance tasks.

  Trigger when the user mentions: invoices, sessions, locum GP, THL-GP,
  Twickenham Health, dashboard, invoice form, invoice view, pdf generator,
  records report, SQLite db, or any of the project files (main.py, db.py,
  pdf_generator.py, dashboard.py, invoice_form.py, invoice_view.py,
  records_report.py, invoice_logic.py, build.bat etc).
---

# Twickenham Health — Locum GP Invoice App Skill

## Version
v2.0 — Production Ready (June 2026)

## GitHub Repository
https://github.com/ShouaibK/twickenham_health

---

## Project Overview
A standalone Windows 11 desktop application for generating and managing
Locum GP invoices for Twickenham Health Limited.

- Fully offline — no internet required
- Runs as a single `.exe` via PyInstaller
- Clean Tkinter UI in navy and white matching company branding
- Designed for non-technical users
- SQLite database — single file, portable backup

---

## Environment
| Item | Detail |
|---|---|
| OS | Windows 11 25H2 |
| Python | 3.13.14 |
| pip | 26.1.2 |
| VS Code | 1.125.1 |
| Project path | `C:\Practice\twickenham_health\` |
| GitHub | https://github.com/ShouaibK/twickenham_health |

---

## Tech Stack
| Layer | Tool | Version |
|---|---|---|
| Language | Python | 3.13.14 |
| UI | Tkinter | Built-in |
| Database | SQLite | Built-in |
| PDF | ReportLab | Latest |
| Images | Pillow | Built-in via ui/__init__.py |
| Packaging | PyInstaller | Latest |

Install dependencies:
```bash
pip install reportlab pillow pyinstaller
```

---

## Actual Project File Structure (Current)
```
twickenham_health/
├── assets/
│   └── twickenham_health_logo.png  ← Company logo (used in UI + PDF)
├── database/
│   ├── __init__.py
│   ├── db.py                       ← ALL SQLite operations (CRUD)
│   └── invoices.db                 ← Auto-created on first run
├── logic/
│   ├── __init__.py
│   ├── invoice_logic.py            ← Calculations, validation, formatting
│   ├── pdf_generator.py            ← PDF invoice builder + open/print helpers
│   └── records_report.py           ← PDF records report (dashboard print)
├── output/                         ← Generated PDFs saved here (gitignored)
├── tests/
│   └── generate_pdf_test.py        ← PDF generation test
├── ui/
│   ├── __init__.py                 ← load_logo_image() helper
│   ├── dashboard.py                ← Home screen: records table + toolbar
│   ├── invoice_form.py             ← New / Edit invoice entry form
│   └── invoice_view.py             ← Read-only view of a single invoice
├── .gitignore                      ← Ignores __pycache__, output/
├── build.bat                       ← One-click PyInstaller .exe builder
├── main.py                         ← Entry point — launches the app window
├── requirements.txt                ← pip packages list
└── SKILL.md                        ← This file
```

---

## IMPORTANT — Files That No Longer Exist
These files were removed — do NOT recreate or reference them:
- ~~`logic/printer.py`~~ — merged into `logic/pdf_generator.py`
- ~~`ui/pdf_preview.py`~~ — never built, not needed

---

## Company Details (Fixed — Never Change Without Being Told)
```
Company Name : Twickenham Health Limited
Address      : 1 Twickenham Grove, Stoke-on-Trent, ST4 8WS, United Kingdom
Phone        : 07859 001684
Reg No       : 16271052
Bank Name    : MONZO
Account No   : 99909112
Sort Code    : 04-00-03
```

---

## Customer Details (Fixed — Always the Same)
```
Customer Name : Allen Street Clinic
Address       : Allen Street, Stoke-On-Trent ST10 1HJ, United Kingdom
```

---

## Invoice Rules
| Rule | Detail |
|---|---|
| Invoice number format | THL-GP### — user types manually (e.g. THL-GP041) |
| Invoice prefix | THL-GP — never changes |
| Due date | Always invoice date + 14 days (editable) |
| Session total (numeric hours) | rate × hours |
| Session total (text hours) | rate as-is (flat fee e.g. "Duty Session") |
| Net Amount | Sum of all session totals |
| Due Amount | Always equals Net Amount — no VAT/tax |
| Status values | pending / paid / overdue |

---

## Database Schema (SQLite)

### Table: invoices
```sql
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
```

### Table: sessions
```sql
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
```

---

## UI Screens & Navigation

### main.py — App Entry Point
- Window: auto-sizes to 85% of screen, centres on launch
- Loads logo as window icon from `assets/twickenham_health_logo.png`
- Navigation methods: `show_dashboard()`, `open_invoice_form()`, `open_invoice_view()`
- Screen switching via `_show_screen()` — destroys current, shows new

### 1. Dashboard (ui/dashboard.py)
- Navy topbar with logo + company name
- Toolbar buttons: New Invoice | Open | Generate PDF | Print | Delete
- **Print button** → generates records PDF report (NOT a single invoice)
- Records table columns: Invoice No. | Invoice Date | Due Date | Customer | Sessions | Net Amount | Due Amount | Status
- Double-click row → opens invoice view
- Search bar: filters by invoice no., date, ref, status
- Sortable columns (click header)
- Status bar: Total | Paid | Pending | Total Earned
- Row colours: alternating white/grey, green=paid, red=overdue

### 2. Invoice Form (ui/invoice_form.py)
- Used for both New Invoice and Edit Invoice
- Fields: Invoice No. (manual, THL-GP prefix), Invoice Date, Due Date, Ref (optional)
- Bill To: pre-filled read-only (Allen Street Clinic)
- Sessions table: Sr. | Activity | Job Date | Hour Rate | Working Hours | Session Total
- Add/Remove session rows dynamically
- Session totals calculate live on keypress
- Due date auto-sets to invoice date + 14 days on focus-out
- Net Amount & Due Amount update live
- Bank details shown read-only at bottom
- Validates before saving: invoice no. format, dates, at least 1 session
- Checks duplicate invoice numbers

### 3. Invoice View (ui/invoice_view.py)
- Read-only display of full invoice
- Topbar buttons: Close | Edit | Generate PDF | Print | Mark as Paid/Pending | Delete
- Toggle paid/pending — updates status live without leaving screen
- Delete shows confirmation dialog with invoice summary
- Sections: Invoice Summary | Sessions | Totals | Bank Details

---

## Logic Files

### logic/invoice_logic.py
Key functions:
- `calculate_session_total(rate, hours)` — numeric: rate×hours, text: flat rate
- `calculate_totals(sessions)` → (net_amount, due_amount)
- `format_currency(amount)` → "£1,685.00"
- `format_rate(amount)` → "£350.00"
- `format_date_for_display(date_str)` → "26-Dec-2025"
- `format_date_for_db(date_str)` → "2025-12-26"
- `validate_invoice_data(inv_no, inv_date, due_date, sessions)` → (bool, msg)
- `build_session_list(raw_sessions)` → clean list for db

### logic/pdf_generator.py
Key functions (invoice PDF + open/print helpers — all in one file):
- `generate_pdf(invoice)` → builds invoice PDF, returns path
- `generate_and_open(invoice)` → generate + open in default viewer
- `generate_and_print(invoice)` → same as generate_and_open
- `open_pdf(pdf_path)` → opens PDF in default system viewer
- `get_output_folder()` → returns output/ folder path
- `open_output_folder()` → opens output/ in Windows Explorer
- PDFs saved to `output/THL-GP###.pdf`

### logic/records_report.py
Key functions (records table PDF report):
- `generate_records_pdf(invoices, title)` → builds records report PDF, returns path
- Used by dashboard Print button to print ALL visible records
- Includes: company header, records table, summary totals, timestamp
- PDFs saved to `output/Records_Report_TIMESTAMP.pdf`

---

## PDF Invoice Layout (Must Match Sample Exactly)
Top to bottom order:
1. Full-width navy bar (#1a2c4e)
2. Logo (left, 22mm) + Company name & address (right, navy)
3. "Invoice to Customer" — centred, underlined, bold
4. Bill To block (left) + Invoice No./Date/Due Date (right, bold values)
5. Sessions table — navy header row:
   Sr. | Activity | Session/Job Date | Session/Hour Rate | Working Hours | Session Total
6. Ref. (left) + Net Amount / Due Amount (right, bold)
7. Bank Details — Bank Name, Account No., Sort/Branch Code
8. Footer: "* This is system generated invoice doesn't require signature and stamp."
9. Full-width navy bar (#1a2c4e)

Colours:
- Navy bars & table header : #1a2c4e
- Table header text : #ffffff
- Body text : #000000
- Alternating rows : #ffffff / #f5f5f5

---

## Coding Conventions
- All UI classes inherit from `tk.Frame`
- All database operations go through `database/db.py` only — no inline SQL in UI
- All PDF generation in `logic/pdf_generator.py` only
- All imports from `logic.pdf_generator` — NOT from `logic.printer` (deleted)
- Use f-strings for all string formatting
- Date in UI/PDF : DD-Mon-YYYY (e.g. 26-Dec-2025)
- Date in DB : YYYY-MM-DD (ISO format)
- Currency : £X,XXX.XX (always GBP, always £ symbol)
- Colours defined as constants at top of each UI file

---

## Common Tasks & Where to Edit

| Task | File(s) to Edit |
|---|---|
| Change company details | `SKILL.md` + `logic/pdf_generator.py` |
| Change bank details | `SKILL.md` + `logic/pdf_generator.py` |
| Change customer details | `logic/pdf_generator.py` + `ui/invoice_form.py` |
| Add new UI screen | `ui/` folder + `main.py` navigation |
| Change invoice calculations | `logic/invoice_logic.py` |
| Change PDF invoice layout | `logic/pdf_generator.py` |
| Change records report layout | `logic/records_report.py` |
| Add/change database column | `database/db.py` (schema + all queries) |
| Change invoice number format | `ui/invoice_form.py` + `logic/invoice_logic.py` |
| Change status options | `ui/dashboard.py` + `database/db.py` |
| Change window size/title | `main.py` |
| Change logo | Replace `assets/twickenham_health_logo.png` |

---

## How to Run & Build

```bash
# Run in development
python main.py

# Build standalone .exe
build.bat
```

Output .exe saved to: `dist/TwickenhamHealth.exe`

---

## GitHub Workflow
```bash
# Save changes
git add .
git commit -m "describe change"
git push

# Get latest on another PC
git pull

# First time on new PC
git clone https://github.com/ShouaibK/twickenham_health.git
cd twickenham_health
pip install -r requirements.txt
python main.py
```

---

## Things Claude Must NEVER Change Without Being Explicitly Asked
- Company name, address, phone, reg number
- Bank details (MONZO, 99909112, 04-00-03)
- Customer name and address (Allen Street Clinic)
- Invoice number prefix (THL-GP)
- PDF layout order and navy colour scheme (#1a2c4e)
- Database schema (without migrating existing data)
- Import `logic.printer` — this file was DELETED, use `logic.pdf_generator`
