import customtkinter as ctk
from launcher.ui.components.widgets import Card

class SettingsTab(ctk.CTkFrame):
    def __init__(self, master, app_logic):
        super().__init__(master, fg_color="transparent")
        self.app = app_logic
        self.config = self.app.config

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        from launcher.ui.components.modern_widgets import ModernCard, GlassButton
        # Java Settings
        self.java_card = ModernCard(self, "Настройки Java", icon="☕")
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

        # GC Selection
        ctk.CTkLabel(self.java_card.content, text="Сборщик мусора (Garbage Collector)").pack(anchor="w", pady=(10,0))
        self.gc_var = ctk.StringVar(value=self.config.get("java", "gc_type", "G1GC"))
        self.gc_menu = ctk.CTkOptionMenu(
            self.java_card.content,
            variable=self.gc_var,
            values=["G1GC", "ZGC", "ShenandoahGC"],
            command=self.update_gc_desc
        )
        self.gc_menu.pack(fill="x", pady=5)

        self.gc_desc = ctk.CTkLabel(self.java_card.content, text="", font=ctk.CTkFont(size=11, slant="italic"), text_color="gray", wraplength=400, justify="left")
        self.gc_desc.pack(fill="x", pady=(0, 10))
        self.update_gc_desc(self.gc_var.get())

        # Launcher Settings
        self.launcher_card = ModernCard(self, "Настройки лаунчера", icon="⚙️")
        self.launcher_card.grid(row=0, column=1, sticky="nsew", pady=(0, 20))

        self.close_var = ctk.BooleanVar(value=self.config.get("launcher", "close_on_launch", True))
        ctk.CTkSwitch(self.launcher_card.content, text="Закрывать при запуске", variable=self.close_var).pack(anchor="w", pady=10)

        self.rpc_var = ctk.BooleanVar(value=self.config.get("launcher", "discord_rpc", True))
        ctk.CTkSwitch(self.launcher_card.content, text="Discord RPC", variable=self.rpc_var).pack(anchor="w", pady=10)

        # Auto-configure button
        ctk.CTkButton(self.java_card.content, text="Автонастройка ОЗУ", command=self.auto_configure_ram, fg_color="#17a2b8", hover_color="#138496").pack(fill="x", pady=15)

        GlassButton(self, text="Сохранить настройки", command=self.save_settings, height=40).grid(row=1, column=0, columnspan=2, pady=10)

    def update_gc_desc(self, choice):
        descs = {
            "G1GC": "Сбалансированный вариант по умолчанию. Отлично подходит для большинства сборок.",
            "ZGC": "Обеспечивает минимальные задержки (фризы). Рекомендуется для мощных ПК и Java 17+.",
            "ShenandoahGC": "Идеально подходит для огромных сборок (200+ модов) и серверов. Требует Java 11+."
        }
        self.gc_desc.configure(text=descs.get(choice, ""))

    def auto_configure_ram(self):
        from launcher.core.system_info import SystemInfo
        SystemInfo.auto_configure(self.config)
        self.ram_min.delete(0, 'end')
        self.ram_min.insert(0, str(self.config.get("java", "ram_min", 2048)))
        self.ram_max.delete(0, 'end')
        self.ram_max.insert(0, str(self.config.get("java", "ram_max", 4096)))

        from launcher.ui.components.modern_widgets import ToastNotification
        ToastNotification(self.master, "ОЗУ автоматически настроено!", type="success")

    def save_settings(self):
        try:
            self.config.set("java", "ram_min", int(self.ram_min.get()))
            self.config.set("java", "ram_max", int(self.ram_max.get()))
        except ValueError:
            pass
        self.config.set("java", "java_path", self.java_path.get())
        self.config.set("java", "gc_type", self.gc_var.get())
        self.config.set("launcher", "close_on_launch", self.close_var.get())
        self.config.set("launcher", "discord_rpc", self.rpc_var.get())

        # Update RPC status
        if self.rpc_var.get():
            self.app.rpc.connect()
        else:
            self.app.rpc.disconnect()

        from launcher.ui.components.modern_widgets import ToastNotification
        ToastNotification(self.master, "Настройки успешно сохранены", type="success")
