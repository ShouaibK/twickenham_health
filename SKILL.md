---
name: twickenham-health-invoice-app
description: "Use this skill whenever working on the Twickenham Health Limited Locum GP Invoice desktop application. Covers all coding tasks including UI screens, database operations, PDF generation, printing, packaging, and maintenance. Trigger when the user mentions: invoices, sessions, locum GP, THL-GP, Twickenham Health, dashboard, invoice form, PDF generator, SQLite DB, or any project file."
---

# Twickenham Health — Locum GP Invoice App Skill

## Version
v3.1 (Production Ready)

## ⚠️ Mandatory First Step
**At the start of every conversation involving this project — or whenever project context is unclear — Claude MUST read this SKILL.md file in full before writing, editing, or suggesting any code.**
This file is the single source of truth for all project decisions, file locations, UI specs, DB schema, conventions, and rules.
Do not rely on memory alone. Always verify against this file first.



## Project Overview
A standalone Windows 11 desktop application for generating and managing
Locum GP invoices for Twickenham Health Limited.

- Fully offline (no internet required)
- Runs as a single `.exe`
- Clean UI, fast performance, reliable output
- Designed for non-technical users



## Tech Stack
| Layer      | Tool         | Version |
|------------|-------------|--------|
| Language   | Python      | 3.11+  |
| UI         | Tkinter     | Built-in |
| Database   | SQLite      | Built-in |
| PDF        | ReportLab   | Latest |
| Images     | Pillow      | Latest |
| Packaging  | PyInstaller | Latest |

Install dependencies:
```bash
pip install reportlab pillow pyinstaller
```



## Project File Structure
```
twickenham_health/
├── build.bat                        ← One-click PyInstaller .exe builder
├── main.py                          ← Entry point — launches the app window
├── requirements.txt                 ← pip packages list
├── SKILL.md                         ← Project knowledge base (this file)
│
├── assets/
│   ├── twickenham_health_logo.png   ← Company logo (used in topbar + PDF)
│   └── icons/                       ← Toolbar button icons (16×16 PNG)
│       ├── icon_customer.png
│       ├── icon_new_invoice.png
│       ├── icon_open_invoice.png
│       ├── icon_generate_pdf.png
│       ├── icon_print-record.png    ← Note: hyphen not underscore
│       └── icon_delete_record.png
│
├── database/
│   ├── db.py                        ← All SQLite operations (CRUD)
│   ├── invoices.db                  ← Auto-created on first run
│   └── __init__.py
│
├── logic/
│   ├── invoice_logic.py             ← Totals, due date, currency calculations
│   ├── pdf_generator.py             ← Builds invoice PDF using ReportLab
│   ├── records_report.py            ← Builds records report PDF
│   └── __init__.py
│
├── output/                          ← Generated PDFs saved here (auto-created)
│   └── *.pdf
│
├── tests/
│   └── generate_pdf_test.py
│
└── ui/
    ├── customer_manager.py          ← Customer add/edit/delete screen
    ├── dashboard.py                 ← Home screen: records table + toolbar
    ├── invoice_form.py              ← New / Edit invoice entry form
    ├── invoice_view.py              ← Read-only view of a single invoice
    └── __init__.py
```
> ⚠️ Always work inside `twickenham_health/` only. The `twickenham_health - Copy/` sibling folder is a backup — never edit it.



## Company Details (Fixed — Do Not Change in Code)
```
Company Name   : Twickenham Health Limited
Address        : 1 Twickenham Grove, Stoke-on-Trent, ST4 8WS, United Kingdom
Phone          : 07859 001684
Reg No         : 16271052
Bank Name      : MONZO
Account No     : 99909112
Sort Code      : 04-00-03
```



## Customer Details (Default — Seeded on First Run)
```
Customer Name  : Allen Street Clinic
Address        : Allen Street, Stoke-On-Trent ST10 1HJ, United Kingdom
```
> Customers are now managed via the Customer Manager screen. Never hardcode customer name anywhere in code.



## Invoice Rules
- Invoice number format : THL-GP### (user types manually e.g. THL-GP041)
- Due date              : Always 20 days after invoice date (can be edited manually)
                          If the 20th day falls on Saturday → shifted to Monday (+2 days)
                          If the 20th day falls on Sunday   → shifted to Monday (+1 day)
                          Logic lives in `calculate_due_date_str()` in invoice_logic.py
                          `default_due_date_str()` applies same rule from today's date
- Session total         : If Working Hours is numeric → rate × hours
                          If Working Hours is "Duty Session" → rate as-is
- Net Amount            : Sum of all session totals
- Due Amount            : Always equals Net Amount (no tax/VAT)
- Invoice prefix        : THL-GP (never changes)



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
    customer_id INTEGER DEFAULT NULL,
    created_at  TEXT    DEFAULT CURRENT_TIMESTAMP
);
```
- `customer_id` is a FK to `customers.id` (LEFT JOIN — **never hardcode customer name anywhere**)
- `get_all_invoices()` always returns records ordered by `inv_no COLLATE NOCASE ASC` (A→Z)
- `get_all_invoices()` and `get_invoice_by_id()` both JOIN customers and return:
  `customer_name`, `customer_address`, `customer_contact`
- All UI files must use `inv["customer_name"]` — never the string "Allen Street Clinic"
- Migration: `ALTER TABLE invoices ADD COLUMN customer_id` runs safely on existing DBs
- Back-fill: existing invoices with `customer_id IS NULL` auto-assigned to first customer

### Table: customers
```sql
CREATE TABLE IF NOT EXISTS customers (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL,
    address    TEXT DEFAULT '',
    contact    TEXT DEFAULT '',
    created_at TEXT DEFAULT CURRENT_TIMESTAMP
);
```
- Seeded on first run with Allen Street Clinic as the default customer
- CRUD via: `get_all_customers()`, `get_customer_by_id()`, `add_customer()`, `update_customer()`, `delete_customer()`

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



## UI Screens & Navigation

### 1. Dashboard (dashboard.py)
- **Topbar specs (do not change without being asked):**
  - Height: `78px`
  - Logo size: `(52, 52)` px
  - "Twickenham Health Limited" font: `Segoe UI 14 bold`
  - "Locum GP Invoice Manager" font: `Segoe UI 10`
- **Toolbar** (bottom, white bg matching statusbar, thin MID_GREY separator above):
  - Search box on the LEFT
  - Buttons on the RIGHT: Customers | New Invoice | Open Invoice | Generate PDF | Print Records | Delete Records
  - Button style: navy bg, white text, `relief="groove"`, `bd=2`, `overrelief="ridge"`
  - Icon-to-label spacing: 1 space (`f" {text}"`)
  - Icons loaded from `assets/icons/` at 16×16px using `os.path.abspath(__file__)`
  - Icon filenames (exact — do not rename):
    - `icon_customer.png`, `icon_new_invoice.png`, `icon_open_invoice.png`
    - `icon_generate_pdf.png`, `icon_print-record.png`, `icon_delete_record.png`
  - Requires `import os` and `from PIL import Image, ImageTk`
- **Build order in `__init__`**: `_build_topbar()` → `_build_statusbar()` → `_build_toolbar()` → `_build_table()`
- **Records table columns:**
  - ☐ checkbox | Invoice No. | Invoice Date | Due Date | Customer | Sessions | Net Amount | Due Amount | Status
- **Column widths (do not change without being asked):**
  | Column       | Width | Anchor   | Stretch |
  |--------------|-------|----------|---------|
  | ☐ check      | 80px  | center   | No      |
  | Invoice No.  | 110px | center   | No      |
  | Invoice Date | 110px | center   | No      |
  | Due Date     | 110px | center   | No      |
  | Customer     | 200px | w (left) | **Yes** — absorbs all remaining space |
  | Sessions     | 75px  | center   | No      |
  | Net Amount   | 110px | e (right)| No      |
  | Due Amount   | 110px | e (right)| No      |
  | Status       | 95px  | center   | No      |
- **Checkbox column behaviour:**
  - Header `☐/☑` toggles ALL rows (select-all / deselect-all)
  - Individual row click toggles that row only
  - Header syncs to `☑` only when all rows are checked
  - `self._checked` (set of iids) preserved across `refresh()` calls
  - `_checked_ids()` returns `list[int]` of checked DB IDs
  - Double-click on checkbox column is ignored
- **Print button behaviour:**
  - Checked rows → prints only those invoices
  - Nothing checked → falls back to single selected row
- **Status bar:** Total invoices | Paid | Pending | Total earned (white bg)

### 2. Invoice Form (invoice_form.py)
- Fields: Invoice No. (manual), Invoice Date, Due Date, Ref (optional)
- Bill To: `ttk.Combobox` dropdown populated from `customers` table
  - Selecting customer auto-fills Address and Contact (read-only)
  - `_reload_customers(select_name=)` fetches fresh data from DB
  - `customer_id` passed to `db.save_invoice()` and `db.update_invoice()`
  - Pre-selects correct customer when editing existing invoice
- Sessions table: Sr. | Activity | Session/Job Date | Hour Rate | Working Hours | Session Total
- Add Session / Remove Session buttons
- Auto-calculates Net Amount and Due Amount live
- Save validates: invoice no. required, at least 1 session required

### 3. Invoice View (invoice_view.py)
- Read-only display of all invoice fields and sessions
- Shows real `customer_name` and `customer_address` from DB — never hardcoded
- **Topbar:** logo + title only — no buttons in topbar
- **Bottom toolbar** (light grey bg, MID_GREY separator above, buttons right-aligned):
  - Button order left→right: Edit | Generate PDF | Mark as Paid/Pending | Delete | Close
  - All buttons: navy bg, white text, `relief="groove"`, `bd=2`
  - `_update_mark_button()` keeps navy colour for both paid/pending states
- Print button removed — use dashboard Print Records instead

### 4. Customer Manager (ui/customer_manager.py)
- Accessed via Customers button in dashboard toolbar
- Split layout: customer list table (left) + add/edit form (right)
- Fields: Customer Name (required) | Address (multi-line) | Contact
- Actions: Save Customer | Clear | Delete (enabled only when editing)
- On first run, Allen Street Clinic is seeded as the default customer
- Back to Dashboard button at bottom toolbar

### 5. Bill To dropdown (invoice_form.py)
- See Invoice Form § above



## PDF Invoice Layout
Order top to bottom:
1. Top navy blue bar (full width)
2. Logo (left) + Company name & address (right, navy blue)
3. "Invoice to Customer" heading (centered, underlined)
4. Bill To block (left) + Invoice No./Date/Due Date (right, bold values)
5. Sessions table with navy header row
6. Ref. (left) + Net Amount / Due Amount (right, bold)
7. Bank Details section
8. Footer note
9. Bottom navy blue bar (full width)

PDF metadata:
- `title` = `"Twickenham Health — {inv_no}"` (shows in PDF viewer tab)
- `author` = `"Twickenham Health Limited"`

PDF colours:
- Navy bar/header : #1a2c4e
- Body text       : #000000
- Bold values     : #000000 bold



## Window Layout (main.py)
- 4% padding on all four sides
- Bottom padding = `screen_h × 4% + 40px` (Windows taskbar clearance)
- Formula:
  ```
  pad_x    = screen_w × 0.04
  pad_top  = screen_h × 0.04
  pad_bot  = screen_h × 0.04 + 40
  target_w = screen_w − pad_x × 2
  target_h = screen_h − pad_top − pad_bot
  pos_x    = pad_x
  pos_y    = pad_top
  ```



## Coding Conventions
- All UI classes inherit from `tk.Frame`
- Database calls go only through `database/db.py` — never inline SQL in UI files
- PDF generation only in `logic/pdf_generator.py`
- `generate_pdf(invoice)` reads `invoice["customer_name"]` and `invoice["customer_address"]` from DB
- Falls back to `CUSTOMER_NAME` / `CUSTOMER_ADDR` constants only if DB value is missing
- Use f-strings for formatting
- Date format in UI  : DD-Mon-YYYY (e.g. 26-Dec-2025)
- Date format in DB  : YYYY-MM-DD (ISO format)
- Currency format    : £X,XXX.XX (always GBP, always £ symbol)



## How to Run
```bash
# Run the app in development
python main.py

# Build the .exe for distribution
build.bat
```

## build.bat Contents
```bat
pyinstaller --onefile --windowed --icon=assets/logo.ico --name="TwickenhamHealth" main.py
pause
```



## Common Tasks & Where to Edit

| Task                          | File to edit                         |
|-------------------------------|--------------------------------------|
| Change company details        | This SKILL.md + pdf_generator.py     |
| Change customer details       | ui/customer_manager.py               |
| Add a new UI screen           | ui/ folder + main.py navigation      |
| Change invoice calculations   | logic/invoice_logic.py               |
| Change PDF layout             | logic/pdf_generator.py               |
| Add a database column         | database/db.py (schema + queries)    |
| Change invoice number format  | invoice_form.py + db.py              |
| Change bank details           | This SKILL.md + pdf_generator.py     |
| Change status options         | dashboard.py + db.py                 |
| Change window size/padding    | main.py (Window Layout section)      |
| Add / edit customers          | ui/customer_manager.py               |
| Change customer dropdown      | ui/invoice_form.py (_bill_to_card)   |
| Change toolbar icons          | assets/icons/ + dashboard.py         |
| Change PDF tab title          | logic/pdf_generator.py (SimpleDocTemplate title=) |



## Git Commit Convention
- **PowerShell single push all:** `git add -A; git commit -m "message"; git push`
- For separate commits per file:
  ```powershell
  git add <file>
  git commit -m "<type>: <description>"
  git push
  ```



## Things Claude Must Never Change Without Being Asked
- Company name, address, phone, reg number
- Bank details (MONZO, 99909112, 04-00-03)
- Invoice number prefix (THL-GP)
- PDF layout order and navy colour scheme
- Dashboard topbar height, logo size, and font sizes
- Dashboard column widths
- Icon filenames in assets/icons/
