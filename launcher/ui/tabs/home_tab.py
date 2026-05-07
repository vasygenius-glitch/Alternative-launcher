import customtkinter as ctk
import threading
from launcher.ui.components.widgets import Card, ServerStatusWidget

class HomeTab(ctk.CTkFrame):
    def __init__(self, master, app_logic):
        super().__init__(master, fg_color="transparent")
        self.app = app_logic

        self.grid_columnconfigure(0, weight=3)
        self.grid_columnconfigure(1, weight=1)
        self.grid_rowconfigure(0, weight=1)

        # Left Column (Banner, Play Button, Progress)
        self.left_col = ctk.CTkFrame(self, fg_color="transparent")
        self.left_col.grid(row=0, column=0, sticky="nsew", padx=(0, 10))
        self.left_col.grid_rowconfigure(0, weight=1)

        # Banner/Welcome area
        self.banner = Card(self.left_col, "Добро пожаловать в Cat Launcher!")
        self.banner.grid(row=0, column=0, sticky="nsew", pady=(0, 20))

        self.welcome_label = ctk.CTkLabel(self.banner.content, text="Готов к игре?", font=ctk.CTkFont(size=24, weight="bold"))
        self.welcome_label.pack(expand=True)

        # Progress Area
        self.progress_frame = ctk.CTkFrame(self.left_col, fg_color="transparent")
        self.progress_frame.grid(row=1, column=0, sticky="ew", pady=(0, 20))

        self.status_label = ctk.CTkLabel(self.progress_frame, text="")
        self.status_label.pack(anchor="w")

        self.progress_bar = ctk.CTkProgressBar(self.progress_frame)
        self.progress_bar.set(0)
        self.progress_bar.pack(fill="x", pady=(5,0))
        self.progress_bar.pack_forget() # Hide initially

        # Play Button Area
        self.play_btn = ctk.CTkButton(self.left_col, text="ИГРАТЬ", height=60, font=ctk.CTkFont(size=24, weight="bold"),
                                      fg_color="#28a745", hover_color="#218838", command=self.on_play)
        self.play_btn.grid(row=2, column=0, sticky="ew")

        # Right Column (Server Status, Info)
        self.right_col = ctk.CTkFrame(self, fg_color="transparent")
        self.right_col.grid(row=0, column=1, sticky="nsew")

        self.server_card = Card(self.right_col, "Статус сервера")
        self.server_card.pack(fill="x", pady=(0, 20))

        self.server_status = ServerStatusWidget(self.server_card.content)
        self.server_status.pack(pady=10)

        self.info_card = Card(self.right_col, "Информация")
        self.info_card.pack(fill="x")
        self.account_lbl = ctk.CTkLabel(self.info_card.content, text="Аккаунт: Не выбран")
        self.account_lbl.pack(anchor="w", pady=5)
        self.instance_lbl = ctk.CTkLabel(self.info_card.content, text="Сборка: Не выбрана")
        self.instance_lbl.pack(anchor="w", pady=5)

    def on_show(self):
        self.update_info()
        # Ping server async
        threading.Thread(target=self._ping, daemon=True).start()

    def update_info(self):
        acc = self.app.auth.get_active_account()
        if acc:
            self.account_lbl.configure(text=f"Аккаунт: {acc['username']}")
            self.welcome_label.configure(text=f"С возвращением, {acc['username']}!")
        else:
            self.account_lbl.configure(text="Аккаунт: Не выбран")
            self.welcome_label.configure(text="Привет! Выбери аккаунт.")

        inst_id = self.app.config.get("last_instance", "default")
        inst = self.app.im.get_instance(inst_id)
        if inst:
            self.instance_lbl.configure(text=f"Сборка: {inst['name']} ({inst['mc_version']})")
        else:
            self.instance_lbl.configure(text="Сборка: Не выбрана")

    def _ping(self):
        # We can ping hypixel or a configured server
        res = self.app.ping_server('mc.hypixel.net')
        if res and 'players' in res:
            self.server_status.update_status(True, f"Онлайн: {res['players']['online']}/{res['players']['max']}")
        else:
            self.server_status.update_status(False, "Оффлайн")

    def on_play(self):
        self.play_btn.configure(state="disabled", text="Запуск...")
        self.progress_bar.pack(fill="x", pady=(5,0))
        self.progress_bar.set(0)

        def update_ui(prog, text):
            # Must run on main thread
            self.after(0, lambda: self._sync_ui(prog, text))

        threading.Thread(target=self.app.launch_game, args=(update_ui,), daemon=True).start()

    def _sync_ui(self, prog, text):
        self.progress_bar.set(prog / 100)
        self.status_label.configure(text=text)
        if prog >= 100 or "Ошибка" in text:
            self.play_btn.configure(state="normal", text="ИГРАТЬ")
            if "Ошибка" in text:
                self.progress_bar.configure(progress_color="#dc3545")
            else:
                # Optionally hide progress bar or reset
                self.after(3000, lambda: self.progress_bar.pack_forget())
