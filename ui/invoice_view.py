import tkinter as tk
from tkinter import ttk, messagebox
from datetime import datetime

from database import db
from logic.invoice_logic import format_currency, format_date_for_display
from logic.printer import generate_and_open, generate_and_print
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


class InvoiceView(tk.Frame):
    """
    Read-only invoice view screen.
    Pass invoice_id for the invoice to display.
    """

    def __init__(self, parent, on_close, on_edit, invoice_id=None,
                 *args, **kwargs):
        super().__init__(parent, bg=LIGHT_GREY, *args, **kwargs)
        self._logo_image = load_logo_image(size=(40, 40))

        self.on_close   = on_close
        self.on_edit    = on_edit
        self.invoice_id = invoice_id
        self.invoice    = None

        self._build_topbar()

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
        self._load_invoice(self.invoice_id)

    def _build_topbar(self):
        bar = tk.Frame(self, bg=NAVY, height=64)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        left = tk.Frame(bar, bg=NAVY)
        left.pack(side="left", padx=14, pady=8)
        if self._logo_image:
            tk.Label(left, image=self._logo_image, bg=NAVY).pack(side="left", padx=(0, 8))
        else:
            tk.Label(left, text="👁", bg=NAVY, fg=WHITE,
                     font=("Segoe UI", 14)).pack(side="left", padx=(0, 8))
        title_f = tk.Frame(left, bg=NAVY)
        title_f.pack(side="left")
        tk.Label(title_f, text="Invoice View",
                 bg=NAVY, fg=WHITE,
                 font=("Segoe UI", 11, "bold")).pack(anchor="w")
        tk.Label(title_f, text="Twickenham Health Limited",
                 bg=NAVY, fg="#aab8cc",
                 font=FONT_SMALL).pack(anchor="w")

        right = tk.Frame(bar, bg=NAVY)
        right.pack(side="right", padx=14)
        self._btn(right, "✖  Close", self.on_close,
                  bg=NAVY, fg=WHITE, bd=1,
                  hl="#aab8cc").pack(side="left", padx=4)
        self._btn(right, "✎  Edit", self._on_edit,
                  bg=WHITE, fg=TEXT_DARK).pack(side="left", padx=4)
        self._mark_btn = self._btn(right, "Mark as Paid", self._toggle_paid,
                                   bg=GREEN, fg=WHITE)
        self._mark_btn.pack(side="left", padx=4)
        self._btn(right, "🗑  Delete", self._delete_invoice,
                  bg=WHITE, fg=RED).pack(side="left", padx=4)

    def _build_body(self):
        self._info_card = self._card(self._body, "Invoice Summary")
        self._sessions_card = self._card(self._body, "Sessions")
        self._totals_card = self._card(self._body, "Totals")

        self._build_invoice_summary(self._info_card)
        self._build_sessions_table(self._sessions_card)
        self._build_totals(self._totals_card)

    def _build_invoice_summary(self, parent):
        content = tk.Frame(parent, bg=WHITE)
        content.pack(fill="x")

        left = tk.Frame(content, bg=WHITE)
        left.pack(side="left", fill="both", expand=True, padx=(0, 8))
        right = tk.Frame(content, bg=WHITE)
        right.pack(side="left", fill="both", expand=True)

        self._status_label = self._summary_row(left, "Status")
        self._invoice_no = self._summary_row(left, "Invoice No.")
        self._invoice_date = self._summary_row(left, "Invoice Date")
        self._due_date = self._summary_row(left, "Due Date")
        self._ref_value = self._summary_row(left, "Ref")

        self._customer_label = self._summary_row(right, "Customer")
        self._customer_address = self._summary_row(right, "Address")
        self._created_at = self._summary_row(right, "Created At")

    def _build_sessions_table(self, parent):
        headers = (
            "Sr.", "Activity", "Job Date",
            "Hour Rate", "Working Hours", "Session Total"
        )

        hdr = tk.Frame(parent, bg=NAVY)
        hdr.pack(fill="x", pady=(0, 4))
        widths = [6, 28, 16, 12, 16, 14]
        for text, w in zip(headers, widths):
            tk.Label(hdr, text=text, bg=NAVY, fg=WHITE,
                     font=FONT_SMALL, width=w,
                     anchor="center").pack(side="left", padx=2, pady=4)

        self._sessions_frame = tk.Frame(parent, bg=WHITE)
        self._sessions_frame.pack(fill="x")

    def _build_totals(self, parent):
        content = tk.Frame(parent, bg=WHITE)
        content.pack(fill="x")

        left = tk.Frame(content, bg=WHITE)
        left.pack(side="left", fill="both", expand=True)
        right = tk.Frame(content, bg=WHITE)
        right.pack(side="left", fill="both", expand=True)

        self._net_label = self._summary_row(right, "Net Amount", value="£0.00")
        self._due_label = self._summary_row(right, "Due Amount", value="£0.00")

        info = (
            ("Bank Name", "MONZO"),
            ("Account No.", "99909112"),
            ("Sort Code", "04-00-03"),
        )
        for label, value in info:
            self._summary_row(left, label, value=value)

    def _summary_row(self, parent, label, value=""):
        row = tk.Frame(parent, bg=WHITE)
        row.pack(fill="x", pady=4)
        tk.Label(row, text=f"{label}", bg=WHITE,
                 fg=TEXT_MID, font=FONT_SMALL, width=15,
                 anchor="w").pack(side="left")
        label_value = tk.Label(row, text=value, bg=WHITE,
                               fg=TEXT_DARK, font=FONT_TITLE,
                               anchor="w")
        label_value.pack(side="left", fill="x", expand=True)
        return label_value

    def _load_invoice(self, invoice_id):
        if not invoice_id:
            messagebox.showerror("Error", "Invoice not specified.")
            self.on_close()
            return

        invoice = db.get_invoice_by_id(invoice_id)
        if not invoice:
            messagebox.showerror("Error", "Invoice not found.")
            self.on_close()
            return

        self.invoice = invoice
        self._invoice_no.config(text=invoice["inv_no"])
        self._invoice_date.config(text=format_date_for_display(invoice["inv_date"]))
        self._due_date.config(text=format_date_for_display(invoice["due_date"]))
        self._ref_value.config(text=invoice.get("ref", ""))
        self._created_at.config(text=format_date_for_display(invoice.get("created_at", "")))
        self._customer_label.config(text="Allen Street Clinic")
        self._customer_address.config(text="Allen Street, Stoke-On-Trent ST10 1HJ, United Kingdom")

        status = invoice.get("status", "pending")
        self._status_label.config(text=status.title())
        self._update_mark_button(status)

        for child in self._sessions_frame.winfo_children():
            child.destroy()

        for s in invoice.get("sessions", []):
            self._render_session_row(s)

        self._net_label.config(text=format_currency(invoice.get("net_amount", 0)))
        self._due_label.config(text=format_currency(invoice.get("due_amount", 0)))

    def _render_session_row(self, session):
        row = tk.Frame(self._sessions_frame, bg=WHITE, pady=3)
        row.pack(fill="x")
        values = [
            str(session.get("sr_no", "")),
            session.get("activity", ""),
            format_date_for_display(session.get("job_date", "")),
            format_currency(session.get("hour_rate", 0)),
            session.get("work_hours", ""),
            format_currency(session.get("session_total", 0)),
        ]
        widths = [6, 28, 16, 12, 16, 14]
        for value, w in zip(values, widths):
            tk.Label(row, text=value, bg=WHITE, fg=TEXT_DARK,
                     font=FONT_NORMAL, width=w,
                     anchor="center").pack(side="left", padx=2)

    def _on_edit(self):
        if self.invoice_id and self.on_edit:
            self.on_edit(self.invoice_id)

    def _toggle_paid(self):
        if not self.invoice:
            return
        if self.invoice.get("status") == "paid":
            db.mark_as_pending(self.invoice_id)
            self.invoice["status"] = "pending"
            messagebox.showinfo("Status Updated", "Invoice marked as pending.")
        else:
            db.mark_as_paid(self.invoice_id)
            self.invoice["status"] = "paid"
            messagebox.showinfo("Status Updated", "Invoice marked as paid.")

        self._status_label.config(text=self.invoice["status"].title())
        self._update_mark_button(self.invoice["status"])

    def _update_mark_button(self, status):
        if status == "paid":
            self._mark_btn.config(text="Mark as Pending", bg=RED)
        else:
            self._mark_btn.config(text="Mark as Paid", bg=GREEN)

    def _delete_invoice(self):
        if not self.invoice:
            return

        confirm = messagebox.askyesno(
            "Delete Invoice",
            f"Delete invoice {self.invoice['inv_no']}?\n\n"
            f"Customer : Allen Street Clinic\n"
            f"Date     : {format_date_for_display(self.invoice['inv_date'])}\n"
            f"Amount   : {format_currency(self.invoice['due_amount'])}\n\n"
            "This action cannot be undone.",
            icon="warning",
        )
        if not confirm:
            return

        db.delete_invoice(self.invoice_id)
        messagebox.showinfo("Deleted",
                            f"Invoice {self.invoice['inv_no']} has been deleted.")
        self.on_close()

    def generate_pdf(self):
        if not self.invoice:
            return
        ok, result = generate_and_open(self.invoice)
        if ok:
            messagebox.showinfo("PDF Generated",
                                f"PDF saved and opened:\n{result}")
        else:
            messagebox.showerror("PDF Error", result)

    def print_invoice(self):
        if not self.invoice:
            return
        ok, result = generate_and_print(self.invoice)
        if ok:
            messagebox.showinfo("Print", "Invoice sent to printer.")
        else:
            messagebox.showerror("Print Error", result)

    def _on_body_configure(self, event):
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self._canvas.itemconfig(self._body_id, width=event.width)

    def _on_mousewheel(self, event):
        self._canvas.yview_scroll(int(-1 * (event.delta / 120)), "units")

    def _card(self, parent, title):
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
