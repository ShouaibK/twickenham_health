import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from database import db
from logic.invoice_logic import (
    calculate_session_total,
    calculate_totals,
    format_currency,
    format_date_for_db,
    format_date_for_display,
    today_str,
    default_due_date_str,
    validate_invoice_data,
    build_session_list,
)
from ui import load_logo_image

# ──────────────────────────────────────────────
#  COLOURS & FONTS
# ──────────────────────────────────────────────
NAVY        = "#1a2c4e"
WHITE       = "#ffffff"
LIGHT_GREY  = "#f5f5f5"
MID_GREY    = "#e0e0e0"
GREEN       = "#0F6E56"
RED         = "#A32D2D"
TEXT_DARK   = "#1a1a1a"
TEXT_MID    = "#555555"

FONT_TITLE  = ("Segoe UI", 10, "bold")
FONT_NORMAL = ("Segoe UI", 9)
FONT_SMALL  = ("Segoe UI", 8)
FONT_MONO   = ("Consolas", 9)


class InvoiceForm(tk.Frame):
    """
    New Invoice / Edit Invoice form screen.
    Pass invoice_id=None for a new invoice,
    or invoice_id=<int> to edit an existing one.
    """

    def __init__(self, parent, on_save, on_cancel,
                 invoice_id=None, *args, **kwargs):
        super().__init__(parent, bg=LIGHT_GREY, *args, **kwargs)
        self._logo_image = load_logo_image(size=(40, 40))

        self.on_save    = on_save
        self.on_cancel  = on_cancel
        self.invoice_id = invoice_id
        self._session_rows = []   # list of dicts holding row widgets

        self._build_topbar()

        # Scrollable body
        self._canvas = tk.Canvas(self, bg=LIGHT_GREY,
                                 highlightthickness=0)
        scrollbar = ttk.Scrollbar(self, orient="vertical",
                                  command=self._canvas.yview)
        self._canvas.configure(yscrollcommand=scrollbar.set)
        scrollbar.pack(side="right", fill="y")
        self._canvas.pack(side="left", fill="both", expand=True)

        self._body = tk.Frame(self._canvas, bg=LIGHT_GREY)
        self._body_id = self._canvas.create_window(
            (0, 0), window=self._body, anchor="nw")

        self._body.bind("<Configure>", self._on_body_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)
        self._canvas.bind_all("<MouseWheel>", self._on_mousewheel)

        self._build_body()

        # Load data if editing
        if self.invoice_id:
            self._load_invoice(self.invoice_id)
        else:
            self._add_session_row()
            self._add_session_row()

    # ──────────────────────────────────────────
    #  TOP BAR
    # ──────────────────────────────────────────

    def _build_topbar(self):
        bar = tk.Frame(self, bg=NAVY, height=64)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        left = tk.Frame(bar, bg=NAVY)
        left.pack(side="left", padx=14, pady=8)
        if self._logo_image:
            tk.Label(left, image=self._logo_image, bg=NAVY).pack(side="left", padx=(0, 8))
        else:
            tk.Label(left, text="📄", bg=NAVY, fg=WHITE,
                     font=("Segoe UI", 14)).pack(side="left", padx=(0, 8))
        title_f = tk.Frame(left, bg=NAVY)
        title_f.pack(side="left")
        mode = "Edit Invoice" if self.invoice_id else "New Invoice"
        tk.Label(title_f, text=mode,
                 bg=NAVY, fg=WHITE,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w")
        tk.Label(title_f, text="Twickenham Health Limited",
                 bg=NAVY, fg="#aab8cc",
                 font=FONT_SMALL).pack(anchor="w")

        right = tk.Frame(bar, bg=NAVY)
        right.pack(side="right", padx=14)
        self._btn(right, "✖  Cancel", self.on_cancel,
                  bg=NAVY, fg=WHITE, bd=1,
                  hl="#aab8cc").pack(side="left", padx=4)
        self._btn(right, "💾  Save Invoice", self._save,
                  bg=GREEN, fg=WHITE).pack(side="left", padx=4)

    # ──────────────────────────────────────────
    #  BODY
    # ──────────────────────────────────────────

    def _build_body(self):
        pad = {"padx": 16, "pady": 8}

        # ── Invoice Details ──────────────────
        self._invoice_details_card()

        # ── Bill To ─────────────────────────
        self._bill_to_card()

        # ── Sessions ────────────────────────
        self._sessions_card()

        # ── Summary ─────────────────────────
        self._summary_card()

        # ── Bank Details ────────────────────
        self._bank_card()

    # ──────────────────────────────────────────
    #  CARDS
    # ──────────────────────────────────────────

    def _invoice_details_card(self):
        card = self._card(self._body, "Invoice Details")

        row = tk.Frame(card, bg=WHITE)
        row.pack(fill="x", pady=4)

        # Invoice No.
        f1 = tk.Frame(row, bg=WHITE)
        f1.pack(side="left", expand=True, fill="x", padx=(0, 8))
        tk.Label(f1, text="Invoice No.", bg=WHITE,
                 fg=TEXT_MID, font=FONT_SMALL).pack(anchor="w")
        self._inv_no = tk.Entry(f1, font=FONT_MONO,
                                relief="solid", bd=1)
        self._inv_no.pack(fill="x", ipady=4)
        self._inv_no.insert(0, "THL-GP")

        # Invoice Date
        f2 = tk.Frame(row, bg=WHITE)
        f2.pack(side="left", expand=True, fill="x", padx=(0, 8))
        tk.Label(f2, text="Invoice Date (YYYY-MM-DD)", bg=WHITE,
                 fg=TEXT_MID, font=FONT_SMALL).pack(anchor="w")
        self._inv_date = tk.Entry(f2, font=FONT_NORMAL,
                                  relief="solid", bd=1)
        self._inv_date.pack(fill="x", ipady=4)
        self._inv_date.insert(0, today_str())
        self._inv_date.bind("<FocusOut>", self._on_inv_date_change)

        # Due Date
        f3 = tk.Frame(row, bg=WHITE)
        f3.pack(side="left", expand=True, fill="x")
        tk.Label(f3, text="Due Date (YYYY-MM-DD)", bg=WHITE,
                 fg=TEXT_MID, font=FONT_SMALL).pack(anchor="w")
        self._due_date = tk.Entry(f3, font=FONT_NORMAL,
                                  relief="solid", bd=1)
        self._due_date.pack(fill="x", ipady=4)
        self._due_date.insert(0, default_due_date_str())

        # Ref
        ref_row = tk.Frame(card, bg=WHITE)
        ref_row.pack(fill="x", pady=(8, 0))
        tk.Label(ref_row, text="Ref. (optional)", bg=WHITE,
                 fg=TEXT_MID, font=FONT_SMALL).pack(anchor="w")
        self._ref = tk.Entry(ref_row, font=FONT_NORMAL,
                             relief="solid", bd=1, width=40)
        self._ref.pack(anchor="w", ipady=4)

    def _bill_to_card(self):
        card = self._card(self._body, "Bill To")
        row  = tk.Frame(card, bg=WHITE)
        row.pack(fill="x", pady=4)

        # Customer dropdown
        f1 = tk.Frame(row, bg=WHITE)
        f1.pack(side="left", expand=True, fill="x", padx=(0, 8))
        tk.Label(f1, text="Customer Name", bg=WHITE,
                 fg=TEXT_MID, font=FONT_SMALL).pack(anchor="w")

        self._customer_var = tk.StringVar()
        self._customer_map = {}   # display name → {id, address, contact}
        self._customer_cb  = ttk.Combobox(
            f1, textvariable=self._customer_var,
            font=FONT_NORMAL, state="readonly")
        self._customer_cb.pack(fill="x", ipady=4)
        self._customer_cb.bind("<<ComboboxSelected>>",
                               self._on_customer_selected)

        # Address (auto-filled, read-only)
        f2 = tk.Frame(row, bg=WHITE)
        f2.pack(side="left", expand=True, fill="x")
        tk.Label(f2, text="Address", bg=WHITE,
                 fg=TEXT_MID, font=FONT_SMALL).pack(anchor="w")
        self._customer_address = tk.Entry(
            f2, font=FONT_NORMAL, relief="solid", bd=1,
            bg=LIGHT_GREY, fg=TEXT_MID)
        self._customer_address.pack(fill="x", ipady=4)
        self._customer_address.config(state="readonly")

        # Contact (auto-filled, read-only)
        contact_row = tk.Frame(card, bg=WHITE)
        contact_row.pack(fill="x", pady=(6, 0))
        tk.Label(contact_row, text="Contact", bg=WHITE,
                 fg=TEXT_MID, font=FONT_SMALL).pack(anchor="w")
        self._customer_contact = tk.Entry(
            contact_row, font=FONT_NORMAL, relief="solid", bd=1,
            bg=LIGHT_GREY, fg=TEXT_MID, width=40)
        self._customer_contact.pack(anchor="w", ipady=4)
        self._customer_contact.config(state="readonly")

        # Load customers into dropdown
        self._reload_customers()

    def _reload_customers(self, select_name=None):
        """Fetch customers from DB and populate the dropdown."""
        customers = db.get_all_customers()
        self._customer_map = {
            c["name"]: c for c in customers
        }
        names = list(self._customer_map.keys())
        self._customer_cb["values"] = names

        # Default selection
        if select_name and select_name in self._customer_map:
            self._customer_var.set(select_name)
        elif names:
            self._customer_var.set(names[0])
        self._on_customer_selected()

    def _on_customer_selected(self, _event=None):
        """Auto-fill address and contact when a customer is chosen."""
        name = self._customer_var.get()
        cust = self._customer_map.get(name)
        if not cust:
            return
        self._customer_address.config(state="normal")
        self._customer_address.delete(0, "end")
        self._customer_address.insert(0, cust.get("address", ""))
        self._customer_address.config(state="readonly")

        self._customer_contact.config(state="normal")
        self._customer_contact.delete(0, "end")
        self._customer_contact.insert(0, cust.get("contact", ""))
        self._customer_contact.config(state="readonly")

    def _sessions_card(self):
        self._sessions_outer = self._card(self._body, "Sessions")

        # Table header
        hdr = tk.Frame(self._sessions_outer, bg=NAVY)
        hdr.pack(fill="x", pady=(0, 4))
        for text, w in [("Sr.", 4), ("Activity", 22),
                        ("Job Date", 12), ("Hour Rate £", 10),
                        ("Working Hours", 13), ("Session Total", 11), ("", 3)]:
            tk.Label(hdr, text=text, bg=NAVY, fg=WHITE,
                     font=FONT_SMALL, width=w,
                     anchor="center").pack(side="left", padx=2, pady=4)

        # Rows container
        self._sessions_frame = tk.Frame(self._sessions_outer, bg=WHITE)
        self._sessions_frame.pack(fill="x")

        # Add session button
        self._btn(self._sessions_outer, "＋  Add Session",
                  self._add_session_row,
                  bg=WHITE, fg=TEXT_MID,
                  bd=1, hl=MID_GREY).pack(anchor="w", pady=(8, 0))

    def _summary_card(self):
        card = self._card(self._body, "Summary")
        row  = tk.Frame(card, bg=WHITE)
        row.pack(fill="x")

        # Net Amount
        f1 = tk.Frame(row, bg=LIGHT_GREY, padx=16, pady=10)
        f1.pack(side="left", expand=True, fill="x", padx=(0, 8))
        tk.Label(f1, text="Net Amount", bg=LIGHT_GREY,
                 fg=TEXT_MID, font=FONT_SMALL).pack(anchor="w")
        self._net_label = tk.Label(f1, text="£0.00",
                                   bg=LIGHT_GREY, fg=TEXT_DARK,
                                   font=("Segoe UI", 16, "bold"))
        self._net_label.pack(anchor="w")

        # Due Amount
        f2 = tk.Frame(row, bg=NAVY, padx=16, pady=10)
        f2.pack(side="left", expand=True, fill="x")
        tk.Label(f2, text="Due Amount", bg=NAVY,
                 fg="#aab8cc", font=FONT_SMALL).pack(anchor="w")
        self._due_label = tk.Label(f2, text="£0.00",
                                   bg=NAVY, fg=WHITE,
                                   font=("Segoe UI", 16, "bold"))
        self._due_label.pack(anchor="w")

    def _bank_card(self):
        card = self._card(self._body, "Bank Details")
        details = [
            ("Bank Name",        "MONZO"),
            ("Account No.",      "99909112"),
            ("Sort / Branch Code", "04-00-03"),
        ]
        for label, value in details:
            row = tk.Frame(card, bg=WHITE)
            row.pack(fill="x", pady=2)
            tk.Label(row, text=label, bg=WHITE,
                     fg=TEXT_MID, font=FONT_SMALL, width=18,
                     anchor="w").pack(side="left")
            tk.Label(row, text=":", bg=WHITE,
                     fg=TEXT_MID, font=FONT_NORMAL).pack(side="left")
            tk.Label(row, text=value, bg=WHITE,
                     fg=TEXT_DARK, font=FONT_TITLE).pack(side="left", padx=6)

    # ──────────────────────────────────────────
    #  SESSION ROW
    # ──────────────────────────────────────────

    def _add_session_row(self, data=None):
        """Add one session row to the sessions table."""
        idx = len(self._session_rows) + 1
        row_frame = tk.Frame(self._sessions_frame, bg=WHITE,
                             pady=3, padx=2)
        row_frame.pack(fill="x")
        tk.Frame(self._sessions_frame, bg=MID_GREY,
                 height=1).pack(fill="x")

        # Sr. number
        tk.Label(row_frame, text=f"{idx:02d}", bg=WHITE,
                 fg=TEXT_MID, font=FONT_MONO,
                 width=4, anchor="center").pack(side="left")

        def entry(width, val=""):
            e = tk.Entry(row_frame, font=FONT_NORMAL,
                         relief="solid", bd=1, width=width)
            e.pack(side="left", padx=2, ipady=3)
            if val:
                e.insert(0, val)
            return e

        act   = entry(22, data.get("activity",   "Locum GP session") if data else "Locum GP session")
        jdate = entry(12, data.get("job_date",   today_str())        if data else today_str())
        rate  = entry(10, str(data.get("hour_rate",  350))           if data else "350")
        hours = entry(13, str(data.get("work_hours", "Duty Session")) if data else "Duty Session")

        # Session total (read-only)
        total_var = tk.StringVar(value="£0.00")
        total_lbl = tk.Label(row_frame, textvariable=total_var,
                             bg=LIGHT_GREY, fg=TEXT_DARK,
                             font=FONT_TITLE, width=11, anchor="e",
                             relief="solid", bd=1)
        total_lbl.pack(side="left", padx=2, ipady=3)

        # Delete button
        row_data = {
            "frame": row_frame,
            "act":   act,
            "jdate": jdate,
            "rate":  rate,
            "hours": hours,
            "total": total_var,
        }
        del_btn = self._btn(row_frame, "✖", lambda rd=row_data: self._remove_row(rd),
                            bg=WHITE, fg=RED, bd=0)
        del_btn.pack(side="left", padx=2)

        # Bind recalc
        for widget in (rate, hours):
            widget.bind("<KeyRelease>", lambda e: self._recalc())
            widget.bind("<FocusOut>",   lambda e: self._recalc())

        # Set initial total
        if data:
            total_var.set(format_currency(data.get("session_total", 0)))
        else:
            self._recalc_row(row_data)

        self._session_rows.append(row_data)
        self._recalc()

    def _remove_row(self, row_data):
        if len(self._session_rows) <= 1:
            messagebox.showwarning("Cannot Remove",
                                   "At least one session is required.")
            return
        row_data["frame"].destroy()
        self._session_rows.remove(row_data)
        self._renumber_rows()
        self._recalc()

    def _renumber_rows(self):
        """Update Sr. numbers after a row is deleted."""
        for widget in self._sessions_frame.winfo_children():
            widget.destroy()
        rows_copy = list(self._session_rows)
        self._session_rows.clear()
        for rd in rows_copy:
            saved = {
                "activity":      rd["act"].get(),
                "job_date":      rd["jdate"].get(),
                "hour_rate":     rd["rate"].get(),
                "work_hours":    rd["hours"].get(),
                "session_total": 0,
            }
            self._add_session_row(saved)

    # ──────────────────────────────────────────
    #  CALCULATIONS
    # ──────────────────────────────────────────

    def _recalc_row(self, row_data):
        try:
            rate  = float(row_data["rate"].get() or 0)
            hours = row_data["hours"].get().strip()
            total = calculate_session_total(rate, hours)
            row_data["total"].set(format_currency(total))
        except Exception:
            row_data["total"].set("£0.00")

    def _recalc(self):
        """Recalculate all rows and update summary totals."""
        for rd in self._session_rows:
            self._recalc_row(rd)
        sessions = self._get_raw_sessions()
        net, due = calculate_totals(sessions)
        self._net_label.config(text=format_currency(net))
        self._due_label.config(text=format_currency(due))

    def _on_inv_date_change(self, event=None):
        """Auto-set due date to invoice date + 14 days."""
        try:
            from datetime import timedelta
            dt  = datetime.strptime(self._inv_date.get().strip(), "%Y-%m-%d")
            due = (dt + timedelta(days=14)).strftime("%Y-%m-%d")
            self._due_date.delete(0, "end")
            self._due_date.insert(0, due)
        except ValueError:
            pass

    # ──────────────────────────────────────────
    #  LOAD / SAVE
    # ──────────────────────────────────────────

    def _load_invoice(self, invoice_id):
        """Pre-fill the form with an existing invoice for editing."""
        invoice = db.get_invoice_by_id(invoice_id)
        if not invoice:
            messagebox.showerror("Error", "Invoice not found.")
            self.on_cancel()
            return

        self._inv_no.delete(0, "end")
        self._inv_no.insert(0, invoice["inv_no"])

        self._inv_date.delete(0, "end")
        self._inv_date.insert(0, invoice["inv_date"])

        self._due_date.delete(0, "end")
        self._due_date.insert(0, invoice["due_date"])

        self._ref.delete(0, "end")
        self._ref.insert(0, invoice.get("ref", "") or "")

        for s in invoice.get("sessions", []):
            self._add_session_row(s)

        self._recalc()

    def _get_raw_sessions(self):
        return [
            {
                "activity":   rd["act"].get().strip(),
                "job_date":   rd["jdate"].get().strip(),
                "hour_rate":  rd["rate"].get().strip(),
                "work_hours": rd["hours"].get().strip(),
            }
            for rd in self._session_rows
        ]

    def _save(self):
        inv_no   = self._inv_no.get().strip().upper()
        inv_date = self._inv_date.get().strip()
        due_date = self._due_date.get().strip()
        ref      = self._ref.get().strip()
        raw      = self._get_raw_sessions()

        # Validate
        ok, msg = validate_invoice_data(inv_no, inv_date, due_date, raw)
        if not ok:
            messagebox.showerror("Validation Error", msg)
            return

        # Check duplicate invoice number
        if db.invoice_number_exists(inv_no, exclude_id=self.invoice_id):
            messagebox.showerror("Duplicate Invoice Number",
                                 f"Invoice number {inv_no} already exists.\n"
                                 "Please use a different number.")
            return

        sessions       = build_session_list(raw)
        net_amt, due_amt = calculate_totals(raw)

        if self.invoice_id:
            # Update existing
            ok = db.update_invoice(
                self.invoice_id, inv_no, inv_date, due_date,
                ref, net_amt, due_amt, sessions
            )
            if ok:
                messagebox.showinfo("Saved", f"Invoice {inv_no} updated.")
                self.on_save()
            else:
                messagebox.showerror("Error",
                                     "Could not update invoice. "
                                     "Duplicate invoice number?")
        else:
            # New invoice
            new_id = db.save_invoice(
                inv_no, inv_date, due_date,
                ref, net_amt, due_amt, sessions
            )
            if new_id:
                messagebox.showinfo("Saved",
                                    f"Invoice {inv_no} saved successfully.")
                self.on_save()
            else:
                messagebox.showerror("Error",
                                     "Could not save invoice. "
                                     "Duplicate invoice number?")

    # ──────────────────────────────────────────
    #  SCROLL HELPERS
    # ──────────────────────────────────────────

    def _on_body_configure(self, event):
        self._canvas.configure(
            scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self._canvas.itemconfig(self._body_id, width=event.width)

    def _on_mousewheel(self, event):
        self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    # ──────────────────────────────────────────
    #  WIDGET HELPERS
    # ──────────────────────────────────────────

    def _card(self, parent, title):
        """Titled white card section."""
        outer = tk.Frame(parent, bg=LIGHT_GREY)
        outer.pack(fill="x", padx=16, pady=6)

        tk.Label(outer, text=title.upper(),
                 bg=LIGHT_GREY, fg=TEXT_MID,
                 font=("Segoe UI", 8, "bold")).pack(anchor="w", pady=(0, 4))

        inner = tk.Frame(outer, bg=WHITE,
                         relief="flat", bd=0,
                         highlightbackground=MID_GREY,
                         highlightthickness=1)
        inner.pack(fill="x")

        content = tk.Frame(inner, bg=WHITE, padx=14, pady=10)
        content.pack(fill="x")
        return content

    def _btn(self, parent, text, cmd,
             bg=WHITE, fg=TEXT_DARK, bd=1, hl=MID_GREY):
        return tk.Button(parent, text=text, command=cmd,
                         bg=bg, fg=fg,
                         font=FONT_NORMAL,
                         relief="flat", bd=0,
                         padx=10, pady=4,
                         cursor="hand2",
                         highlightbackground=hl,
                         highlightthickness=bd,
                         activebackground=bg,
                         activeforeground=fg)
