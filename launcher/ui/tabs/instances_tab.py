import customtkinter as ctk
from launcher.ui.components.widgets import Card
from launcher.ui.components.dialogs import Dialog

class InstancesTab(ctk.CTkFrame):
    def __init__(self, master, app_logic):
        super().__init__(master, fg_color="transparent")
        self.app = app_logic

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        self.create_card = Card(self, "Создать сборку")
        self.create_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=(0, 20))

        # Form
        self.name_entry = ctk.CTkEntry(self.create_card.content, placeholder_text="Название сборки")
        self.name_entry.pack(pady=5, fill="x")

        # Simple dropdown for versions
        self.version_var = ctk.StringVar(value="1.20.1")
        self.version_menu = ctk.CTkOptionMenu(self.create_card.content, variable=self.version_var, values=["1.20.1", "1.19.4", "1.18.2", "1.16.5", "1.12.2", "1.8.9"])
        self.version_menu.pack(pady=5, fill="x")

        self.loader_var = ctk.StringVar(value="forge")
        self.loader_menu = ctk.CTkOptionMenu(self.create_card.content, variable=self.loader_var, values=["vanilla", "forge", "fabric"])
        self.loader_menu.pack(pady=5, fill="x")

        ctk.CTkButton(self.create_card.content, text="Создать", command=self.create_instance).pack(pady=10)

        # List
        from launcher.ui.components.modern_widgets import ModernCard
        self.list_card = ModernCard(self, "Мои Сборки", icon_name="instances")
        self.list_card.grid(row=0, column=1, sticky="nsew", pady=(0, 20))

        self.list_frame = ctk.CTkScrollableFrame(self.list_card.content, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True)

    def on_show(self):
        self.refresh_list()

    def create_instance(self):
        name = self.name_entry.get().strip()
        if not name:
            Dialog("Ошибка", "Введите название", self)
            return

        ver = self.version_var.get()
        loader = self.loader_var.get()

        # Quick creation
        self.app.im.create_instance(name, ver, loader)
        self.name_entry.delete(0, 'end')
        self.refresh_list()

    def refresh_list(self):
        for w in self.list_frame.winfo_children():
            w.destroy()

        instances = self.app.im.get_instances()
        # use root level key since last_instance is saved at root
        active_id = self.app.config.get("last_instance", default="default")

        if not instances:
            ctk.CTkLabel(self.list_frame, text="Нет сборок").pack(pady=20)
            return

        for inst in instances:
            iid = inst['id']
            f = ctk.CTkFrame(self.list_frame, fg_color=("gray85", "gray25"), corner_radius=5)
            f.pack(fill="x", pady=5, padx=5)

            lbl_text = f"{inst['name']} ({inst['mc_version']} - {inst['loader']})"
            lbl = ctk.CTkLabel(f, text=lbl_text, font=ctk.CTkFont(weight="bold" if iid == active_id else "normal"))
            lbl.pack(side="left", padx=10, pady=10)

            if iid != active_id:
                ctk.CTkButton(f, text="Выбрать", width=60, command=lambda i=iid: self.select_instance(i)).pack(side="right", padx=5, pady=5)
            else:
                ctk.CTkLabel(f, text="✔ Текущая", text_color="#28a745").pack(side="right", padx=10)

            ctk.CTkButton(f, text="Удалить", width=60, fg_color="#dc3545", hover_color="#c82333", command=lambda i=iid: self.delete_instance(i)).pack(side="right", padx=5, pady=5)

    def select_instance(self, iid):
        self.app.config.set("last_instance", None, iid)
        self.refresh_list()

    def delete_instance(self, iid):
        self.app.im.delete_instance(iid)
        # Handle if we deleted the active one
        if self.app.config.get("last_instance", default="default") == iid:
            rem = self.app.im.get_instances()
            if rem:
                self.app.config.set("last_instance", None, rem[0]['id'])
            else:
                self.app.config.set("last_instance", None, "default")
        self.refresh_list()
