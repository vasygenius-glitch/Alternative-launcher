import customtkinter as ctk
from launcher.ui.components.dialogs import Dialog

class AccountsTab(ctk.CTkFrame):
    def __init__(self, master, app_logic):
        super().__init__(master, fg_color="transparent")
        self.app = app_logic

        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        from launcher.ui.components.modern_widgets import ModernCard, GlassButton
        # Add Account Card
        self.add_card = ModernCard(self, "Добавить аккаунт", icon_name="accounts")
        self.add_card.grid(row=0, column=0, sticky="nsew", padx=(0, 10), pady=(0, 20))

        ctk.CTkLabel(self.add_card.content, text="Оффлайн аккаунт (без лицензии)").pack(pady=5)
        self.username_entry = ctk.CTkEntry(self.add_card.content, placeholder_text="Никнейм")
        self.username_entry.pack(pady=10, fill="x")

        GlassButton(self.add_card.content, text="Добавить", command=self.add_offline).pack(pady=15)

        # List Card
        self.list_card = ModernCard(self, "Список аккаунтов", icon_name="accounts")
        self.list_card.grid(row=0, column=1, sticky="nsew", pady=(0, 20))

        self.list_frame = ctk.CTkScrollableFrame(self.list_card.content, fg_color="transparent")
        self.list_frame.pack(fill="both", expand=True)

        self.refresh_list()

    def on_show(self):
        self.refresh_list()

    def add_offline(self):
        name = self.username_entry.get().strip()
        if not name or len(name) < 3:
            Dialog("Ошибка", "Никнейм должен быть больше 3 символов.", self)
            return

        self.app.auth.add_offline_account(name)
        self.username_entry.delete(0, 'end')
        self.refresh_list()

    def refresh_list(self):
        for widget in self.list_frame.winfo_children():
            widget.destroy()

        accounts = self.app.auth.get_all_accounts()
        active_id = self.app.auth.active_account_id

        if not accounts:
            ctk.CTkLabel(self.list_frame, text="Нет аккаунтов").pack(pady=20)
            return

        for acc_id, acc in accounts.items():
            f = ctk.CTkFrame(self.list_frame, fg_color="#000000", border_width=1, border_color="#333333", corner_radius=0)
            f.pack(fill="x", pady=5, padx=5)

            name_lbl = ctk.CTkLabel(f, text=f"{acc['username']} ({acc['type']})", font=ctk.CTkFont(weight="bold" if acc_id == active_id else "normal"))
            name_lbl.pack(side="left", padx=10, pady=10)

            if acc_id != active_id:
                ctk.CTkButton(f, text="ВЫБРАТЬ", width=60, command=lambda i=acc_id: self.select_account(i)).pack(side="right", padx=5, pady=5)
            else:
                ctk.CTkLabel(f, text="[X] АКТИВЕН", text_color="#FFFFFF").pack(side="right", padx=10)

            ctk.CTkButton(f, text="Удалить", width=60, fg_color="#dc3545", hover_color="#c82333", command=lambda i=acc_id: self.delete_account(i)).pack(side="right", padx=5, pady=5)

    def select_account(self, acc_id):
        self.app.auth.set_active_account(acc_id)
        self.refresh_list()

    def delete_account(self, acc_id):
        self.app.auth.remove_account(acc_id)
        self.refresh_list()
