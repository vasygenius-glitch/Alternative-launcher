import customtkinter as ctk
from launcher.ui.components.widgets import Card

class SettingsTab(ctk.CTkFrame):
    def __init__(self, master, app_logic):
        super().__init__(master, fg_color="transparent")
        self.app = app_logic
        self.config = self.app.config

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Java Settings
        self.java_card = Card(self, "Настройки Java")
        self.java_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=(0, 20))

        ctk.CTkLabel(self.java_card.content, text="RAM Min (MB)").pack(anchor="w", pady=(5,0))
        self.ram_min = ctk.CTkEntry(self.java_card.content)
        self.ram_min.insert(0, str(self.config.get("java", "ram_min", 2048)))
        self.ram_min.pack(fill="x", pady=5)

        ctk.CTkLabel(self.java_card.content, text="RAM Max (MB)").pack(anchor="w", pady=(5,0))
        self.ram_max = ctk.CTkEntry(self.java_card.content)
        self.ram_max.insert(0, str(self.config.get("java", "ram_max", 4096)))
        self.ram_max.pack(fill="x", pady=5)

        ctk.CTkLabel(self.java_card.content, text="Путь к Java (пусто = авто)").pack(anchor="w", pady=(5,0))
        self.java_path = ctk.CTkEntry(self.java_card.content)
        self.java_path.insert(0, self.config.get("java", "java_path", ""))
        self.java_path.pack(fill="x", pady=5)

        # Launcher Settings
        self.launcher_card = Card(self, "Настройки лаунчера")
        self.launcher_card.grid(row=0, column=1, sticky="nsew", pady=(0, 20))

        self.close_var = ctk.BooleanVar(value=self.config.get("launcher", "close_on_launch", True))
        ctk.CTkSwitch(self.launcher_card.content, text="Закрывать при запуске", variable=self.close_var).pack(anchor="w", pady=10)

        self.rpc_var = ctk.BooleanVar(value=self.config.get("launcher", "discord_rpc", True))
        ctk.CTkSwitch(self.launcher_card.content, text="Discord RPC", variable=self.rpc_var).pack(anchor="w", pady=10)

        ctk.CTkButton(self, text="Сохранить настройки", command=self.save_settings, height=40).grid(row=1, column=0, columnspan=2, pady=10)

    def save_settings(self):
        try:
            self.config.set("java", "ram_min", int(self.ram_min.get()))
            self.config.set("java", "ram_max", int(self.ram_max.get()))
        except ValueError:
            pass
        self.config.set("java", "java_path", self.java_path.get())
        self.config.set("launcher", "close_on_launch", self.close_var.get())
        self.config.set("launcher", "discord_rpc", self.rpc_var.get())

        # Update RPC status
        if self.rpc_var.get():
            self.app.rpc.connect()
        else:
            self.app.rpc.disconnect()

        print("Settings saved.")
