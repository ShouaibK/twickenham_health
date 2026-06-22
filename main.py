import os
import tkinter as tk

from database import db
from ui import load_logo_image
from ui.dashboard import Dashboard
from ui.invoice_form import InvoiceForm
from ui.invoice_view import InvoiceView


class App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("Twickenham Health Invoice Manager")
        self.configure(bg="#f5f5f5")

        screen_w = self.winfo_screenwidth()
        screen_h = self.winfo_screenheight()

        # 4% padding on every side; bottom excludes Windows taskbar (~40px)
        pad_x    = int(screen_w * 0.04)
        pad_top  = int(screen_h * 0.04)
        taskbar  = 40                          # typical Windows taskbar height
        pad_bot  = int(screen_h * 0.04) + taskbar

        target_w = screen_w - pad_x * 2
        target_h = screen_h - pad_top - pad_bot
        pos_x    = pad_x
        pos_y    = pad_top

        self.geometry(f"{target_w}x{target_h}+{pos_x}+{pos_y}")
        self.minsize(target_w, target_h)

        self._set_window_icon()

        db.initialise_db()

        self._container = tk.Frame(self, bg="#f5f5f5")
        self._container.pack(fill="both", expand=True)

        self._current_screen = None
        self.show_dashboard()

    def _show_screen(self, screen: tk.Frame):
        if self._current_screen is not None:
            self._current_screen.destroy()
        self._current_screen = screen
        self._current_screen.pack(fill="both", expand=True)

    def show_dashboard(self):
        dashboard = Dashboard(
            self._container,
            on_new=self.open_invoice_form,
            on_open=self.open_invoice_view,
            on_edit=self.open_invoice_form,
        )
        self._show_screen(dashboard)

    def open_invoice_form(self, invoice_id=None):
        form = InvoiceForm(
            self._container,
            on_save=self.show_dashboard,
            on_cancel=self.show_dashboard,
            invoice_id=invoice_id,
        )
        self._show_screen(form)

    def open_invoice_view(self, invoice_id):
        view = InvoiceView(
            self._container,
            on_close=self.show_dashboard,
            on_edit=self.open_invoice_form,
            invoice_id=invoice_id,
        )
        self._show_screen(view)

    def _set_window_icon(self):
        self._icon_image = load_logo_image(size=(64, 64))
        if self._icon_image:
            try:
                self.iconphoto(True, self._icon_image)
            except tk.TclError:
                pass


if __name__ == "__main__":
    app = App()
    app.mainloop()
