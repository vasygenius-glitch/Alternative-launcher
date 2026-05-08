import customtkinter as ctk
import threading

class ServerStatusWidget(ctk.CTkFrame):
    def __init__(self, master, **kwargs):
        super().__init__(master, fg_color="transparent", **kwargs)

        self.status_icon = ctk.CTkLabel(self, text="●", text_color="grey", font=ctk.CTkFont(family="Courier", size=20))
        self.status_icon.pack(side="left", padx=(0, 5))

        self.status_text = ctk.CTkLabel(self, text="ОЖИДАНИЕ...", font=ctk.CTkFont(family="Courier", size=14, weight="bold"))
        self.status_text.pack(side="left")

    def update_status(self, online, text):
        color = "#FFFFFF" if online else "#FF0000"
        self.status_icon.configure(text_color=color)
        self.status_text.configure(text=text.upper(), text_color=color)

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

        from launcher.ui.components.modern_widgets import ModernCard, GlassButton
        # Banner/Welcome area
        self.banner = ModernCard(self.left_col, "Добро пожаловать в Cat Launcher!", icon_name="home")
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
        self.play_btn = GlassButton(self.left_col, text="ИГРАТЬ", height=60, font=ctk.CTkFont(family="Courier", size=24, weight="bold"),
                                      fg_color="#FF0000", hover_color="#990000", border_color="#FF0000", command=self.on_play)
        self.play_btn.grid(row=2, column=0, sticky="ew")

        # Right Column (Server Status, Info)
        self.right_col = ctk.CTkFrame(self, fg_color="transparent")
        self.right_col.grid(row=0, column=1, sticky="nsew")

        self.server_card = ModernCard(self.right_col, "СТАТУС СЕРВЕРА", icon_name="server")
        self.server_card.pack(fill="x", pady=(0, 20))

        self.server_status = ServerStatusWidget(self.server_card.content)
        self.server_status.pack(pady=10)

        self.info_card = ModernCard(self.right_col, "СИСТЕМА", icon_name="info")
        self.info_card.pack(fill="x")
        self.account_lbl = ctk.CTkLabel(self.info_card.content, text="АККАУНТ: НЕ ВЫБРАН", font=ctk.CTkFont(family="Courier", size=12))
        self.account_lbl.pack(anchor="w", pady=5)
        self.instance_lbl = ctk.CTkLabel(self.info_card.content, text="СБОРКА: НЕ ВЫБРАНА", font=ctk.CTkFont(family="Courier", size=12))
        self.instance_lbl.pack(anchor="w", pady=5)
        self.java_lbl = ctk.CTkLabel(self.info_card.content, text="JAVA: ОЖИДАНИЕ", font=ctk.CTkFont(family="Courier", size=12))
        self.java_lbl.pack(anchor="w", pady=5)
        self.ram_lbl = ctk.CTkLabel(self.info_card.content, text="ОЗУ: ОЖИДАНИЕ", font=ctk.CTkFont(family="Courier", size=12))
        self.ram_lbl.pack(anchor="w", pady=5)
        self.hash_lbl = ctk.CTkLabel(self.info_card.content, text="ХЕШ КЭША: ПРОВЕРКА", text_color="#FFFFFF", font=ctk.CTkFont(family="Courier", size=12, weight="bold"))
        self.hash_lbl.pack(anchor="w", pady=5)

    def on_show(self):
        self.update_info()
        # Ping server async
        threading.Thread(target=self._ping, daemon=True).start()

    def update_info(self):
        acc = self.app.auth.get_active_account()
        if acc:
            self.account_lbl.configure(text=f"АККАУНТ: {acc['username'].upper()}")
            self.welcome_label.configure(text=f"С ВОЗВРАЩЕНИЕМ, {acc['username'].upper()}!")
        else:
            self.account_lbl.configure(text="АККАУНТ: НЕ ВЫБРАН")
            self.welcome_label.configure(text="ПРИВЕТ! ВЫБЕРИ АККАУНТ.")

        inst_id = self.app.config.get("last_instance", default="default")
        inst = self.app.im.get_instance(inst_id)
        if inst:
            self.instance_lbl.configure(text=f"СБОРКА: {inst['name'].upper()} ({inst['mc_version']})")
        else:
            self.instance_lbl.configure(text="СБОРКА: НЕ ВЫБРАНА")

        j_path = self.app.config.get("java", "java_path", "AUTO")
        if not j_path: j_path = "AUTO"

        # Trim very long paths for UI
        if len(j_path) > 30: j_path = "..." + j_path[-27:]
        self.java_lbl.configure(text=f"JAVA: {j_path}")

        r_min = self.app.config.get("java", "ram_min", 2048)
        r_max = self.app.config.get("java", "ram_max", 4096)
        self.ram_lbl.configure(text=f"ОЗУ: {r_min}-{r_max} MB")
        self.hash_lbl.configure(text="ХЕШ КЭША: СОБРАН")

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
