import customtkinter as ctk

class Card(ctk.CTkFrame):
    """
    A stylized container with a title.
    """
    def __init__(self, master, title, **kwargs):
        super().__init__(master, fg_color=("#e0e0e0", "#2b2b2b"), corner_radius=10, **kwargs)

        self.title_label = ctk.CTkLabel(self, text=title, font=ctk.CTkFont(size=16, weight="bold"))
        self.title_label.pack(anchor="w", padx=15, pady=(10, 5))

        self.content = ctk.CTkFrame(self, fg_color="transparent")
        self.content.pack(fill="both", expand=True, padx=15, pady=(0, 15))

class ServerStatusWidget(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.status_icon = ctk.CTkLabel(self, text="●", text_color="grey", font=ctk.CTkFont(size=20))
        self.status_icon.pack(side="left", padx=(0, 5))

        self.status_text = ctk.CTkLabel(self, text="Ожидание...", font=ctk.CTkFont(size=14))
        self.status_text.pack(side="left")

    def update_status(self, online, text):
        color = "#28a745" if online else "#dc3545"
        self.status_icon.configure(text_color=color)
        self.status_text.configure(text=text)

class Dialog(ctk.CTkToplevel):
    """
    Simple modal dialog for alerts or prompts.
    """
    def __init__(self, title, message, master=None):
        super().__init__(master)
        self.title(title)
        self.geometry("300x150")
        self.resizable(False, False)
        self.grab_set()

        ctk.CTkLabel(self, text=message, wraplength=260).pack(pady=20, padx=20, expand=True)
        ctk.CTkButton(self, text="OK", command=self.destroy, width=100).pack(pady=(0, 20))
