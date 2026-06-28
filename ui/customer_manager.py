import tkinter as tk
from tkinter import ttk, messagebox

from database import db
from ui import load_logo_image


# ──────────────────────────────────────────────
#  COLOURS & FONTS  (mirrors dashboard.py)
# ──────────────────────────────────────────────
NAVY       = "#1a2c4e"
WHITE      = "#ffffff"
LIGHT_GREY = "#f5f5f5"
MID_GREY   = "#e0e0e0"
GREEN      = "#0F6E56"
RED        = "#A32D2D"
TEXT_DARK  = "#1a1a1a"
TEXT_MID   = "#555555"

FONT_TITLE  = ("Segoe UI", 10, "bold")
FONT_NORMAL = ("Segoe UI", 9)
FONT_SMALL  = ("Segoe UI", 8)
FONT_LABEL  = ("Segoe UI", 9, "bold")


class CustomerManager(tk.Frame):
    """
    Full-screen customer management panel.
    Left side  : customer list table
    Right side : add / edit form
    """

    def __init__(self, parent, on_close, *args, **kwargs):
        super().__init__(parent, bg=LIGHT_GREY, *args, **kwargs)
        self._logo_image = load_logo_image(size=(52, 52))
        self.on_close    = on_close
        self._editing_id = None   # None = adding new, int = editing existing

        self._build_topbar()
        self._build_body()
        self._build_toolbar()

        self._load_customers()

    # ──────────────────────────────────────────
    #  TOP BAR  (same style as dashboard)
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
        tk.Label(title_frame, text="Customer Manager",
                 bg=NAVY, fg="#aab8cc",
                 font=("Segoe UI", 10)).pack(anchor="w")

        tk.Label(bar, text="Reg. No: 16271052",
                 bg=NAVY, fg="#aab8cc",
                 font=FONT_SMALL).pack(side="right", padx=14)

    # ──────────────────────────────────────────
    #  BODY  (table LEFT + form RIGHT)
    # ──────────────────────────────────────────

    def _build_body(self):
        body = tk.Frame(self, bg=LIGHT_GREY)
        body.pack(fill="both", expand=True, padx=12, pady=10)
        body.columnconfigure(0, weight=3)
        body.columnconfigure(1, weight=2)
        body.rowconfigure(0, weight=1)

        self._build_list_panel(body)
        self._build_form_panel(body)

    # ── LEFT: customer list ──

    def _build_list_panel(self, parent):
        frame = tk.Frame(parent, bg=WHITE, relief="flat",
                         highlightbackground=MID_GREY, highlightthickness=1)
        frame.grid(row=0, column=0, sticky="nsew", padx=(0, 6))
        frame.rowconfigure(1, weight=1)
        frame.columnconfigure(0, weight=1)

        # Header row
        hdr = tk.Frame(frame, bg=NAVY, height=34)
        hdr.grid(row=0, column=0, columnspan=2, sticky="ew")
        hdr.pack_propagate(False)
        tk.Label(hdr, text="  Customers", bg=NAVY, fg=WHITE,
                 font=FONT_TITLE, anchor="w").pack(side="left",
                                                    fill="y", padx=6)

        # Treeview
        vsb = ttk.Scrollbar(frame, orient="vertical")
        vsb.grid(row=1, column=1, sticky="ns")

        columns = ("name", "address", "contact")
        self._tree = ttk.Treeview(frame, columns=columns,
                                  show="headings", selectmode="browse",
                                  yscrollcommand=vsb.set)
        vsb.config(command=self._tree.yview)

        col_cfg = {
            "name":    ("Customer Name",    180, "w"),
            "address": ("Address",          260, "w"),
            "contact": ("Contact",          120, "center"),
        }
        for col, (heading, width, anchor) in col_cfg.items():
            self._tree.heading(col, text=heading)
            self._tree.column(col, width=width, anchor=anchor, minwidth=80)

        style = ttk.Style()
        style.configure("Treeview",
                        background=WHITE, foreground=TEXT_DARK,
                        rowheight=28, fieldbackground=WHITE,
                        font=FONT_NORMAL)
        style.configure("Treeview.Heading",
                        background=NAVY, foreground=WHITE,
                        font=FONT_TITLE, relief="flat")
        style.map("Treeview",
                  background=[("selected", "#d0e4f7")],
                  foreground=[("selected", TEXT_DARK)])
        style.map("Treeview.Heading",
                  background=[("active", "#243d6b")])

        self._tree.tag_configure("odd",  background=WHITE)
        self._tree.tag_configure("even", background=LIGHT_GREY)

        self._tree.grid(row=1, column=0, sticky="nsew")
        self._tree.bind("<<TreeviewSelect>>", self._on_row_select)

    # ── RIGHT: add / edit form ──

    def _build_form_panel(self, parent):
        outer = tk.Frame(parent, bg=WHITE, relief="flat",
                         highlightbackground=MID_GREY, highlightthickness=1)
        outer.grid(row=0, column=1, sticky="nsew", padx=(6, 0))
        outer.rowconfigure(1, weight=1)
        outer.columnconfigure(0, weight=1)

        # Panel header
        hdr = tk.Frame(outer, bg=NAVY, height=34)
        hdr.grid(row=0, column=0, sticky="ew")
        hdr.pack_propagate(False)
        self._form_title_lbl = tk.Label(hdr, text="  Add Customer",
                                         bg=NAVY, fg=WHITE,
                                         font=FONT_TITLE, anchor="w")
        self._form_title_lbl.pack(side="left", fill="y", padx=6)

        # Form fields
        form = tk.Frame(outer, bg=WHITE, padx=18, pady=16)
        form.grid(row=1, column=0, sticky="nsew")
        form.columnconfigure(1, weight=1)

        def field(row, label, var, height=1):
            tk.Label(form, text=label, bg=WHITE, fg=TEXT_DARK,
                     font=FONT_LABEL, anchor="w").grid(
                row=row, column=0, sticky="nw", pady=(10, 2), padx=(0, 12))
            if height == 1:
                e = tk.Entry(form, textvariable=var, font=FONT_NORMAL,
                             relief="solid", bd=1,
                             highlightthickness=1,
                             highlightcolor=NAVY,
                             highlightbackground=MID_GREY)
                e.grid(row=row, column=1, sticky="ew", pady=(10, 2))
            else:
                e = tk.Text(form, font=FONT_NORMAL, relief="solid", bd=1,
                            height=height, wrap="word",
                            highlightthickness=1,
                            highlightcolor=NAVY,
                            highlightbackground=MID_GREY)
                e.grid(row=row, column=1, sticky="ew", pady=(10, 2))
            return e

        self._var_name    = tk.StringVar()
        self._var_contact = tk.StringVar()

        field(0, "Customer Name *", self._var_name)
        self._address_box = field(1, "Address", None, height=4)
        field(2, "Contact", self._var_contact)

        # Required note
        tk.Label(form, text="* Required field", bg=WHITE,
                 fg=TEXT_MID, font=FONT_SMALL).grid(
            row=3, column=0, columnspan=2, sticky="w", pady=(14, 0))

        # Action buttons
        btn_frame = tk.Frame(form, bg=WHITE)
        btn_frame.grid(row=4, column=0, columnspan=2,
                       sticky="ew", pady=(18, 0))
        btn_frame.columnconfigure(0, weight=1)
        btn_frame.columnconfigure(1, weight=1)
        btn_frame.columnconfigure(2, weight=1)

        self._save_btn = tk.Button(
            btn_frame, text="💾  Save Customer",
            command=self._save_customer,
            bg=NAVY, fg=WHITE, font=FONT_NORMAL,
            relief="flat", bd=0, padx=10, pady=6,
            cursor="hand2",
            activebackground="#243d6b", activeforeground=WHITE)
        self._save_btn.grid(row=0, column=0, sticky="ew", padx=(0, 4))

        self._clear_btn = tk.Button(
            btn_frame, text="✖  Clear",
            command=self._clear_form,
            bg=LIGHT_GREY, fg=TEXT_DARK, font=FONT_NORMAL,
            relief="flat", bd=0, padx=10, pady=6,
            cursor="hand2",
            activebackground=MID_GREY, activeforeground=TEXT_DARK)
        self._clear_btn.grid(row=0, column=1, sticky="ew", padx=4)

        self._delete_btn = tk.Button(
            btn_frame, text="🗑  Delete",
            command=self._delete_customer,
            bg=WHITE, fg=RED, font=FONT_NORMAL,
            relief="flat", bd=0, padx=10, pady=6,
            cursor="hand2",
            activebackground=LIGHT_GREY, activeforeground=RED,
            state="disabled")
        self._delete_btn.grid(row=0, column=2, sticky="ew", padx=(4, 0))

    # ──────────────────────────────────────────
    #  BOTTOM TOOLBAR
    # ──────────────────────────────────────────

    def _build_toolbar(self):
        tk.Frame(self, bg=MID_GREY, height=1).pack(side="bottom", fill="x")
        bar = tk.Frame(self, bg=WHITE, pady=6)
        bar.pack(side="bottom", fill="x")

        # Customer count label on far right
        self._count_lbl = tk.Label(bar, text="", bg=WHITE,
                                    fg=TEXT_MID, font=FONT_SMALL)
        self._count_lbl.pack(side="right", padx=14)

        # Back to Dashboard after Delete — on the right
        tk.Button(bar, text="← Back to Dashboard",
                  command=self.on_close,
                  bg=WHITE, fg=TEXT_DARK, font=FONT_NORMAL,
                  relief="flat", bd=0, padx=10, pady=4,
                  cursor="hand2",
                  activebackground=LIGHT_GREY,
                  activeforeground=TEXT_DARK).pack(side="right", padx=4)

    # ──────────────────────────────────────────
    #  DATA LOADING
    # ──────────────────────────────────────────

    def _load_customers(self):
        for row in self._tree.get_children():
            self._tree.delete(row)

        customers = db.get_all_customers()
        for i, c in enumerate(customers):
            tag = "even" if i % 2 == 0 else "odd"
            self._tree.insert("", "end",
                iid=str(c["id"]),
                values=(c["name"], c["address"], c["contact"]),
                tags=(tag,))

        total = len(customers)
        self._count_lbl.config(
            text=f"Total customers: {total}")

    # ──────────────────────────────────────────
    #  FORM HELPERS
    # ──────────────────────────────────────────

    def _on_row_select(self, _event=None):
        sel = self._tree.selection()
        if not sel:
            return
        iid = sel[0]
        customer = db.get_customer_by_id(int(iid))
        if not customer:
            return

        self._editing_id = int(iid)
        self._var_name.set(customer["name"])
        self._var_contact.set(customer["contact"] or "")
        self._address_box.delete("1.0", "end")
        self._address_box.insert("1.0", customer["address"] or "")

        self._form_title_lbl.config(text="  Edit Customer")
        self._delete_btn.config(state="normal")

    def _clear_form(self):
        self._editing_id = None
        self._var_name.set("")
        self._var_contact.set("")
        self._address_box.delete("1.0", "end")
        self._form_title_lbl.config(text="  Add Customer")
        self._delete_btn.config(state="disabled")
        self._tree.selection_remove(self._tree.selection())

    def _get_address(self):
        return self._address_box.get("1.0", "end").strip()

    # ──────────────────────────────────────────
    #  CRUD ACTIONS
    # ──────────────────────────────────────────

    def _save_customer(self):
        name    = self._var_name.get().strip()
        address = self._get_address()
        contact = self._var_contact.get().strip()

        if not name:
            messagebox.showwarning("Validation",
                                   "Customer Name is required.")
            return

        if self._editing_id is None:
            db.add_customer(name, address, contact)
            messagebox.showinfo("Saved",
                                f"Customer '{name}' added successfully.")
        else:
            db.update_customer(self._editing_id, name, address, contact)
            messagebox.showinfo("Updated",
                                f"Customer '{name}' updated successfully.")

        self._clear_form()
        self._load_customers()

    def _delete_customer(self):
        if self._editing_id is None:
            return
        name = self._var_name.get().strip()
        confirm = messagebox.askyesno(
            "Delete Customer",
            f"Delete customer '{name}'?\n\n"
            "This will not delete existing invoices.\n"
            "This action cannot be undone.",
            icon="warning")
        if confirm:
            db.delete_customer(self._editing_id)
            self._clear_form()
            self._load_customers()
            messagebox.showinfo("Deleted",
                                f"Customer '{name}' has been deleted.")