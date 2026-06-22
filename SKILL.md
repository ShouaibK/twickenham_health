---
name: twickenham-health-invoice-app
description: "Use this skill whenever working on the Twickenham Health Limited Locum GP Invoice desktop application. Covers all coding tasks including UI screens, database operations, PDF generation, printing, packaging, and maintenance. Trigger when the user mentions: invoices, sessions, locum GP, THL-GP, Twickenham Health, dashboard, invoice form, PDF generator, SQLite DB, or any project file."
---

# Twickenham Health — Locum GP Invoice App Skill

## Version
v1.8 (Production Ready)



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
├── main.py                   ← Entry point — launches the app window
├── ui/
│   ├── __init__.py
│   ├── dashboard.py          ← Home screen: records table + toolbar
│   ├── invoice_form.py       ← New / Edit invoice entry form
│   ├── invoice_view.py       ← Read-only view of a single invoice
│   └── pdf_preview.py        ← PDF preview before printing
├── logic/
│   ├── __init__.py
│   ├── invoice_logic.py      ← Totals, due amount calculations
│   ├── pdf_generator.py      ← Builds PDF using ReportLab
│   └── printer.py            ← Sends PDF to Windows printer
├── database/
│   ├── __init__.py
│   ├── db.py                 ← All SQLite operations (CRUD)
│   └── invoices.db           ← Auto-created on first run
├── assets/
│   ├── logo.png              ← Twickenham Health circular logo
│   └── fonts/                ← Custom fonts for PDF output
├── requirements.txt          ← pip packages list
└── build.bat                 ← One-click PyInstaller .exe builder
```



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



## Customer Details (Fixed — Always the Same)
```
Customer Name  : Allen Street Clinic
Address        : Allen Street, Stoke-On-Trent ST10 1HJ, United Kingdom
```



## Invoice Rules
- Invoice number format : THL-GP### (user types manually e.g. THL-GP041)
- Due date              : Always 14 days after invoice date (can be edited)
- Session total         : If Working Hours is numeric → rate × hours
                          If Working Hours is "Duty Session" → rate as-is
- Net Amount            : Sum of all session totals
- Due Amount            : Always equals Net Amount (no tax/VAT)
- Invoice prefix        : THL-GP (never changes)



## Database Schema (SQLite)

### Table: invoices
```sql
CREATE TABLE invoices (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    inv_no      TEXT NOT NULL UNIQUE,
    inv_date    TEXT NOT NULL,
    due_date    TEXT NOT NULL,
    ref         TEXT,
    net_amount  REAL NOT NULL,
    due_amount  REAL NOT NULL,
    status      TEXT DEFAULT 'pending',  -- pending | paid | overdue
    created_at  TEXT DEFAULT CURRENT_TIMESTAMP
);
```

### Table: sessions
```sql
CREATE TABLE sessions (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    invoice_id  INTEGER NOT NULL,
    sr_no       INTEGER NOT NULL,
    activity    TEXT DEFAULT 'Locum GP session',
    job_date    TEXT NOT NULL,
    hour_rate   REAL NOT NULL,
    work_hours  TEXT NOT NULL,   -- e.g. "Duty Session" or "3"
    session_total REAL NOT NULL,
    FOREIGN KEY (invoice_id) REFERENCES invoices(id) ON DELETE CASCADE
);
```



## UI Screens & Navigation

### 1. Dashboard (dashboard.py)
- Toolbar buttons: New Invoice | Open | Generate PDF | Print | Delete
- Records table columns: ☐ | Invoice No. | Invoice Date | Due Date | Customer | Sessions | Net Amount | Due Amount | Status
- First column is a **checkbox column** (`"check"`) for multi-selection:
  - Header shows `☐` / `☑` — clicking it toggles ALL rows on/off (select-all / deselect-all)
  - Header auto-updates to `☑` when every row is individually checked, back to `☐` when any is unchecked
  - Clicking a row's checkbox cell toggles `☐` / `☑` for that row only
  - Checked IDs are stored in `self._checked` (a `set` of string iids); `self._all_checked` (bool) tracks header state
  - `_checked_ids()` returns a `list[int]` of all checked database IDs
  - Double-clicking the checkbox column is ignored (does not open invoice)
  - Single-row selection via `_selected_id()` is fully independent and untouched
  - `self._checked` is preserved across `refresh()` calls — checked state survives data reloads
  - Column width: `30px`, non-stretching, no sort on click
- **Print button behaviour:**
  - If any checkboxes are ticked → prints only those checked invoices
  - If no checkboxes are ticked → falls back to the single selected row
  - Confirmation dialog shows the mode clearly (`X checked invoice(s)` or `1 selected invoice (THL-GP###)`)
- Row hover actions: Eye (view) | PDF | Print | Edit
- Status bar: Total invoices | Paid | Pending | Total earned
- Search bar: filter by invoice no., date, or customer
- **Topbar specs (do not change without being asked):**
  - Height: `78px`
  - Logo size: `(52, 52)` px
  - "Twickenham Health Limited" font: `Segoe UI 14 bold`
  - "Locum GP Invoice Manager" font: `Segoe UI 10`

### 2. Invoice Form (invoice_form.py)
- Fields: Invoice No. (manual), Invoice Date, Due Date, Ref (optional)
- Bill To: pre-filled, read-only (Allen Street Clinic)
- Sessions table: Sr. | Activity | Session/Job Date | Hour Rate | Working Hours | Session Total
- Add Session / Remove Session buttons
- Auto-calculates Net Amount and Due Amount live
- Save button validates: invoice no. required, at least 1 session required

### 3. Invoice View (invoice_view.py)
- Read-only display of all invoice fields and sessions
- Action buttons: Generate PDF | Print | Edit | Mark as Paid | Delete
- Delete triggers confirmation dialog first

### 4. Delete Confirmation Dialog
- Shows invoice summary (no., customer, date, amount)
- Warning: action cannot be undone
- Buttons: Cancel | Yes, Delete Invoice

### 5. PDF Preview (pdf_preview.py)
- Opens generated PDF in Windows default viewer
- Or prints directly via printer.py



## PDF Invoice Layout (Must Match Sample)
Replicate exactly — in this order top to bottom:
1. Top navy blue bar (full width)
2. Logo (left) + Company name & address (right, navy blue)
3. "Invoice to Customer" heading (centered, underlined)
4. Bill To block (left) + Invoice No./Date/Due Date (right, bold values)
5. Sessions table with navy header row:
   Sr. | Activity | Session/Job Date | Session/Hour Rate | Working Hours | Session Total
6. Ref. (left) + Net Amount / Due Amount (right, bold)
7. Bank Details section (Bank Name, Account No., Sort/Branch Code)
8. Footer note: "* This is system generated invoice doesn't require signature and stamp."
9. Bottom navy blue bar (full width)

PDF colours:
- Navy header/footer bar : #1a2c4e
- Table header background : #1a2c4e
- Table header text       : #ffffff
- Body text               : #000000
- Bold values             : #000000 bold



## Window Layout (main.py)
- Window size is calculated dynamically from screen resolution at startup
- **4% padding on all four sides** — no hard-coded pixel dimensions
- Bottom padding = `screen_h × 4% + 40px` to exclude the Windows taskbar (40px)
- Formula:
  ```
  pad_x    = screen_w × 0.04
  pad_top  = screen_h × 0.04
  pad_bot  = screen_h × 0.04 + 40   ← taskbar clearance
  target_w = screen_w − pad_x × 2
  target_h = screen_h − pad_top − pad_bot
  pos_x    = pad_x
  pos_y    = pad_top
  ```
- `minsize` is set equal to `target_w × target_h` (window is not resizable smaller)
- Do **not** revert to percentage-based sizing (e.g. `0.85 × screen`) — the 4% padding rule is intentional



## Coding Conventions
- All UI classes inherit from `tk.Frame`
- Database calls go only through `database/db.py` — never inline SQL in UI files
- PDF generation only in `logic/pdf_generator.py`
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

| Task                        | File to edit                    |
|-----------------------------|---------------------------------|
| Change company details      | This SKILL.md + pdf_generator.py|
| Change customer details      | invoice_form.py + pdf_generator.py |
| Add a new UI screen         | ui/ folder + main.py navigation |
| Change invoice calculations | logic/invoice_logic.py          |
| Change PDF layout           | logic/pdf_generator.py          |
| Add a database column       | database/db.py (schema + queries)|
| Change invoice number format| invoice_form.py + db.py         |
| Change bank details         | This SKILL.md + pdf_generator.py|
| Change status options       | dashboard.py + db.py            |
| Change window size/padding  | main.py (Window Layout section) |



## Git Commit Convention
- Always use **separate commits per file**, never bundle multiple files in one commit
- Always use **separate `git push`** after each commit
- Format:
  ```bash
  git add <file>
  git commit -m "<type>: <description>"
  git push

  git add <file>
  git commit -m "<type>: <description>"
  git push
  ```
- Company name, address, phone, reg number
- Bank details (MONZO, 99909112, 04-00-03)
- Customer name and address (Allen Street Clinic)
- Invoice number prefix (THL-GP)
- PDF layout order and navy colour scheme
- Dashboard topbar height, logo size, and font sizes (see UI Screens § 1)
