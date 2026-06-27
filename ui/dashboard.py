import os
import tkinter as tk
from tkinter import ttk, messagebox
from PIL import Image, ImageTk

from database import db
from logic.invoice_logic import format_date_for_display, format_currency
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


class Dashboard(tk.Frame):
    """
    Main home screen — shows all invoice records in a table
    with toolbar buttons and a status bar.
    """

    def __init__(self, parent, on_new, on_open, on_edit, on_customers,
                 *args, **kwargs):
        super().__init__(parent, bg=LIGHT_GREY, *args, **kwargs)
        self._logo_image = load_logo_image(size=(52, 52))

        # Callbacks injected from main.py
        self.on_new       = on_new
        self.on_open      = on_open
        self.on_edit      = on_edit
        self.on_customers = on_customers

        self._checked     = set()   # iids that are checkbox-checked
        self._all_checked = False   # tracks header checkbox state

        # Init search var early so refresh() can always read it
        self._search_var = tk.StringVar()

        self._build_topbar()
        self._build_statusbar()   # statusbar first → sits just above toolbar
        self._build_toolbar()     # toolbar last → goes to very bottom
        self._build_table()       # table fills remaining space

        self._search_var.trace_add("write", lambda *_: self.refresh())
        self.refresh()

    # ──────────────────────────────────────────
    #  TOP BAR
    # ──────────────────────────────────────────

    def _build_topbar(self):
        bar = tk.Frame(self, bg=NAVY, height=78)
        bar.pack(fill="x")
        bar.pack_propagate(False)

        left = tk.Frame(bar, bg=NAVY)
        left.pack(side="left", padx=14, pady=8)

        if self._logo_image:
            tk.Label(left, image=self._logo_image, bg=NAVY,
                     relief="flat").pack(side="left", padx=(0, 8))
        else:
            tk.Label(left, text="✚", bg=NAVY, fg=WHITE,
                     font=("Segoe UI", 13, "bold"),
                     width=2, relief="flat").pack(side="left", padx=(0, 8))

        title_frame = tk.Frame(left, bg=NAVY)
        title_frame.pack(side="left")
        tk.Label(title_frame, text="Twickenham Health Limited",
                 bg=NAVY, fg=WHITE,
                 font=("Segoe UI", 14, "bold")).pack(anchor="w")
        tk.Label(title_frame, text="Locum GP Invoice Manager",
                 bg=NAVY, fg="#aab8cc",
                 font=("Segoe UI", 10)).pack(anchor="w")

        tk.Label(bar, text="Reg. No: 16271052",
                 bg=NAVY, fg="#aab8cc",
                 font=FONT_SMALL).pack(side="right", padx=14)

    # ──────────────────────────────────────────
    #  TOOLBAR
    # ──────────────────────────────────────────

    def _build_toolbar(self):
        bar = tk.Frame(self, bg=WHITE, pady=2)
        bar.pack(side="bottom", fill="x")

        # Thin separator above toolbar
        tk.Frame(self, bg=MID_GREY, height=1).pack(side="bottom", fill="x")

        # Load icons at 16×16
        project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        icon_dir     = os.path.join(project_root, "assets", "icons")
        self._toolbar_icons = {}
        icon_files = {
            "customers":    "icon_customer.png",
            "new_invoice":  "icon_new_invoice.png",
            "open":         "icon_open_invoice.png",
            "generate_pdf": "icon_generate_pdf.png",
            "print":        "icon_print-record.png",
            "delete":       "icon_delete_record.png",
        }
        for key, fname in icon_files.items():
            path = os.path.join(icon_dir, fname)
            try:
                img = Image.open(path).resize((16, 16), Image.LANCZOS)
                self._toolbar_icons[key] = ImageTk.PhotoImage(img)
            except Exception:
                self._toolbar_icons[key] = None

        def btn(text, cmd, icon_key):
            icon = self._toolbar_icons.get(icon_key)
            b = tk.Button(
                bar,
                text=f"  {text}",
                image=icon,
                compound="left",
                command=cmd,
                fg=WHITE,
                bg=NAVY,
                font=FONT_NORMAL,
                relief="groove",
                bd=2,
                padx=10, pady=5,
                cursor="hand2",
                activebackground="#243d6b",
                activeforeground=WHITE,
                overrelief="ridge",
            )
            if icon:
                b._icon = icon
            b.pack(side="right", padx=4, pady=4)
            return b

        # Search on LEFT
        search_frame = tk.Frame(bar, bg=WHITE)
        search_frame.pack(side="left", padx=10)
        tk.Label(search_frame, text="🔍", bg=WHITE, fg=TEXT_DARK,
                 font=FONT_NORMAL).pack(side="left")
        tk.Entry(search_frame,
                 textvariable=self._search_var,
                 font=FONT_NORMAL, width=22,
                 relief="solid", bd=1,
                 bg=WHITE, fg=TEXT_DARK).pack(side="left", padx=(4, 0))

        # Buttons on RIGHT
        self._delete_btn = btn("Delete Records", self._delete_selected, "delete")
        btn("Print Records", self._print_selected,   "print")
        btn("Generate PDF",  self._generate_pdf,     "generate_pdf")
        btn("Open Invoice",  self._open_selected,    "open")
        btn("New Invoice",   self.on_new,            "new_invoice")
        btn("Customers",     self.on_customers,      "customers")

    # ──────────────────────────────────────────
    #  STATUS BAR
    # ──────────────────────────────────────────

    def _build_statusbar(self):
        tk.Frame(self, bg=MID_GREY, height=1).pack(side="bottom", fill="x")
        bar = tk.Frame(self, bg=WHITE, pady=5)
        bar.pack(side="bottom", fill="x")

        def stat(label):
            f = tk.Frame(bar, bg=WHITE)
            f.pack(side="left", padx=14)
            tk.Label(f, text=label, bg=WHITE,
                     fg=TEXT_MID, font=FONT_SMALL).pack(side="left")
            val = tk.Label(f, text="0", bg=WHITE,
                           fg=TEXT_DARK, font=FONT_TITLE)
            val.pack(side="left", padx=(3, 0))
            return val

        self._stat_total   = stat("Total invoices:")
        self._stat_paid    = stat("Paid:")
        self._stat_pending = stat("Pending:")

        right = tk.Frame(bar, bg=WHITE)
        right.pack(side="right", padx=14)
        tk.Label(right, text="Total earned:",
                 bg=WHITE, fg=TEXT_MID,
                 font=FONT_SMALL).pack(side="left")
        self._stat_earned = tk.Label(right, text="£0.00",
                                     bg=WHITE, fg=TEXT_DARK,
                                     font=FONT_TITLE)
        self._stat_earned.pack(side="left", padx=(3, 0))

    # ──────────────────────────────────────────
    #  RECORDS TABLE
    # ──────────────────────────────────────────

    def _build_table(self):
        container = tk.Frame(self, bg=LIGHT_GREY)
        container.pack(fill="both", expand=True)

        vsb = ttk.Scrollbar(container, orient="vertical")
        hsb = ttk.Scrollbar(container, orient="horizontal")

        columns = (
            "check", "inv_no", "inv_date", "due_date",
            "customer", "sessions", "net_amount", "due_amount", "status"
        )
        self._tree = ttk.Treeview(
            container,
            columns=columns,
            show="headings",
            selectmode="browse",
            yscrollcommand=vsb.set,
            xscrollcommand=hsb.set,
        )

        vsb.config(command=self._tree.yview)
        hsb.config(command=self._tree.xview)

        # Column headings & widths
        col_cfg = {
            "check":      ("☐",              80, "center"),
            "inv_no":     ("Invoice No.",    110, "center"),
            "inv_date":   ("Invoice Date",   110, "center"),
            "due_date":   ("Due Date",       110, "center"),
            "customer":   ("Customer",       200, "w"),
            "sessions":   ("Sessions",        75, "center"),
            "net_amount": ("Net Amount",     110, "e"),
            "due_amount": ("Due Amount",     110, "e"),
            "status":     ("Status",          95, "center"),
        }
        for col, (heading, width, anchor) in col_cfg.items():
            if col == "check":
                self._tree.heading(col, text=heading,
                                   command=self._toggle_all_checkboxes)
            else:
                self._tree.heading(col, text=heading,
                                   command=lambda c=col: self._sort(c))
            self._tree.column(col, width=width, anchor=anchor,
                              minwidth=width,
                              stretch=col == "customer")

        # Style
        style = ttk.Style()
        style.theme_use("clam")
        style.configure("Treeview",
                        background=WHITE,
                        foreground=TEXT_DARK,
                        rowheight=28,
                        fieldbackground=WHITE,
                        font=FONT_NORMAL)
        style.configure("Treeview.Heading",
                        background=NAVY,
                        foreground=WHITE,
                        font=FONT_TITLE,
                        relief="flat")
        style.map("Treeview",
                  background=[("selected", "#d0e4f7")],
                  foreground=[("selected", TEXT_DARK)])
        style.map("Treeview.Heading",
                  background=[("active", "#243d6b")])

        self._tree.tag_configure("odd",     background=WHITE)
        self._tree.tag_configure("even",    background=LIGHT_GREY)
        self._tree.tag_configure("paid",    foreground=GREEN)
        self._tree.tag_configure("overdue", foreground=RED)

        self._tree.bind("<Double-1>",       self._on_double_click)
        self._tree.bind("<ButtonRelease-1>", self._on_click)

        self._tree.grid(row=0, column=0, sticky="nsew")
        vsb.grid(row=0, column=1, sticky="ns")
        hsb.grid(row=1, column=0, sticky="ew")
        container.grid_rowconfigure(0, weight=1)
        container.grid_columnconfigure(0, weight=1)

        self._sort_col = None
        self._sort_asc = True

    # ──────────────────────────────────────────
    #  DATA LOADING
    # ──────────────────────────────────────────

    def refresh(self, *_):
        """Reload invoices from DB and repopulate the table."""
        search   = self._search_var.get().strip()
        invoices = db.get_all_invoices(search)

        for row in self._tree.get_children():
            self._tree.delete(row)

        first_id = None
        for i, inv in enumerate(invoices):
            tag  = "even" if i % 2 == 0 else "odd"
            tags = [tag]
            if inv["status"] == "paid":
                tags.append("paid")
            elif inv["status"] == "overdue":
                tags.append("overdue")

            status_label = {
                "pending": "⏳ Pending",
                "paid":    "✅ Paid",
                "overdue": "⚠ Overdue",
            }.get(inv["status"], inv["status"].title())

            item_id = str(inv["id"])
            if first_id is None:
                first_id = item_id

            self._tree.insert("", "end",
                iid=item_id,
                values=(
                    "☑" if item_id in self._checked else "☐",
                    inv["inv_no"],
                    format_date_for_display(inv["inv_date"]),
                    format_date_for_display(inv["due_date"]),
                    inv.get("customer_name", "Unknown"),
                    inv.get("session_count", 0),
                    format_currency(inv["net_amount"]),
                    format_currency(inv["due_amount"]),
                    status_label,
                ),
                tags=tags,
            )

        if search and first_id is not None:
            self._tree.selection_set(first_id)
            self._tree.focus(first_id)
            self._tree.see(first_id)

        stats = db.get_stats()
        self._stat_total.config(text=str(stats["total"]))
        self._stat_paid.config(text=str(stats["paid"]))
        self._stat_pending.config(text=str(stats["pending"]))
        self._stat_earned.config(text=format_currency(stats["total_earned"]))

    # ──────────────────────────────────────────
    #  CHECKBOX HELPERS
    # ──────────────────────────────────────────

    def _toggle_all_checkboxes(self):
        all_iids = self._tree.get_children("")
        if not all_iids:
            return
        if self._all_checked:
            self._checked.clear()
            for iid in all_iids:
                self._tree.set(iid, "check", "☐")
            self._all_checked = False
            self._tree.heading("check", text="☐")
        else:
            for iid in all_iids:
                self._checked.add(iid)
                self._tree.set(iid, "check", "☑")
            self._all_checked = True
            self._tree.heading("check", text="☑")

    def _on_click(self, event):
        region = self._tree.identify_region(event.x, event.y)
        if region != "cell":
            return
        col = self._tree.identify_column(event.x)
        if col != "#1":
            return
        iid = self._tree.identify_row(event.y)
        if not iid:
            return
        if iid in self._checked:
            self._checked.discard(iid)
            self._tree.set(iid, "check", "☐")
        else:
            self._checked.add(iid)
            self._tree.set(iid, "check", "☑")
        all_iids = set(self._tree.get_children(""))
        self._all_checked = all_iids.issubset(self._checked) and bool(all_iids)
        self._tree.heading("check", text="☑" if self._all_checked else "☐")

    def _on_double_click(self, event):
        col = self._tree.identify_column(event.x)
        if col == "#1":
            return
        self._open_selected()

    def _checked_ids(self):
        return [int(iid) for iid in self._checked]

    def _selected_id(self):
        sel = self._tree.selection()
        if not sel:
            messagebox.showwarning("No Selection",
                                   "Please select an invoice first.")
            return None
        return int(sel[0])

    def _sort(self, col):
        items = [(self._tree.set(k, col), k)
                 for k in self._tree.get_children("")]
        if self._sort_col == col:
            self._sort_asc = not self._sort_asc
        else:
            self._sort_asc = True
        self._sort_col = col
        items.sort(reverse=not self._sort_asc)
        for index, (_, k) in enumerate(items):
            self._tree.move(k, "", index)

    # ──────────────────────────────────────────
    #  TOOLBAR ACTIONS
    # ──────────────────────────────────────────

    def _open_selected(self):
        inv_id = self._selected_id()
        if inv_id:
            self.on_open(inv_id)

    def _generate_pdf(self):
        inv_id = self._selected_id()
        if not inv_id:
            return
        invoice = db.get_invoice_by_id(inv_id)
        if not invoice:
            return
        from logic.pdf_generator import generate_and_open
        ok, result = generate_and_open(invoice)
        if ok:
            messagebox.showinfo("PDF Generated",
                                f"PDF saved and opened:\n{result}")
        else:
            messagebox.showerror("PDF Error", result)

    def _print_selected(self):
        """Print checked invoices; fallback to single selected row."""
        checked = self._checked_ids()

        if checked:
            all_invoices = db.get_all_invoices("")
            invoices     = [inv for inv in all_invoices if inv["id"] in checked]
            label_mode   = f"{len(invoices)} checked invoice(s)"
        else:
            inv_id = self._selected_id()
            if not inv_id:
                return
            invoice    = db.get_invoice_by_id(inv_id)
            if not invoice:
                return
            invoices   = [invoice]
            label_mode = f"1 selected invoice ({invoice['inv_no']})"

        if not invoices:
            messagebox.showwarning("No Records", "No invoices to print.")
            return

        confirm = messagebox.askyesno(
            "Print Records",
            f"Print {label_mode} as a PDF report?\n\n"
            f"Company : Twickenham Health Limited\n\n"
            "A PDF will be generated and opened for printing.",
        )
        if not confirm:
            return

        try:
            from logic.records_report import generate_records_pdf
            from logic.pdf_generator import open_pdf
            title    = "Invoice Records Report"
            if len(invoices) == 1:
                title = f"Invoice Report — {invoices[0]['inv_no']}"
            pdf_path = generate_records_pdf(invoices, title=title)
            opened   = open_pdf(pdf_path)
            if opened:
                messagebox.showinfo(
                    "Print — Records Report",
                    f"✅ PDF generated and opened successfully.\n\n"
                    f"Records : {len(invoices)} invoice(s)\n"
                    f"File    : {pdf_path}\n\n"
                    "Use File → Print inside your PDF viewer to send to printer."
                )
            else:
                messagebox.showwarning(
                    "Print — PDF Saved",
                    f"✅ PDF saved but could not open automatically.\n\n"
                    f"File : {pdf_path}\n\n"
                    "Please open it manually and print from there."
                )
        except Exception as e:
            messagebox.showerror(
                "Print Error",
                f"❌ Could not generate records report:\n\n{str(e)}"
            )

    def _delete_selected(self):
        inv_id = self._selected_id()
        if not inv_id:
            return
        invoice = db.get_invoice_by_id(inv_id)
        if not invoice:
            return

        confirm = messagebox.askyesno(
            "Delete Invoice",
            f"Delete invoice {invoice['inv_no']}?\n\n"
            f"Customer : {invoice.get('customer_name', 'Unknown')}\n"
            f"Date     : {format_date_for_display(invoice['inv_date'])}\n"
            f"Amount   : {format_currency(invoice['due_amount'])}\n\n"
            "This action cannot be undone.",
            icon="warning",
        )
        if confirm:
            db.delete_invoice(inv_id)
            self.refresh()
            messagebox.showinfo("Deleted",
                                f"Invoice {invoice['inv_no']} has been deleted.")