import customtkinter as ctk
from launcher.ui.components.modern_widgets import GlassButton

class Dialog(ctk.CTkToplevel):
    """
    Simple modal dialog for alerts or prompts.
    """
    def __init__(self, title, message, master=None):
        super().__init__(master)
        self.title(title)
        self.geometry("400x200")
        self.resizable(False, False)

        # In newer customtkinter, wait_visibility might be needed before grabbing on some OSes
        try:
            self.grab_set()
        except:
            pass

        lbl = ctk.CTkLabel(self, text=message, wraplength=360, justify="left", font=ctk.CTkFont(size=14))
        lbl.pack(pady=20, padx=20, expand=True, fill="both")

        GlassButton(self, text="Понятно", command=self.destroy, width=120).pack(pady=(0, 20))
