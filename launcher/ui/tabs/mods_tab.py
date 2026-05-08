import customtkinter as ctk
import threading
from launcher.ui.components.dialogs import Dialog
from launcher.core.mod_manager import ModManager

class ModsTab(ctk.CTkFrame):
    def __init__(self, master, app_logic):
        super().__init__(master, fg_color="transparent")
        self.app = app_logic
        self.mm = None

        self.grid_columnconfigure(0, weight=1)
        self.grid_rowconfigure(1, weight=1)

        # Search area
        search_frame = ctk.CTkFrame(self, fg_color="transparent")
        search_frame.grid(row=0, column=0, sticky="ew", pady=(0, 10))

        self.search_entry = ctk.CTkEntry(search_frame, placeholder_text="Поиск модов (Modrinth)...", width=300)
        self.search_entry.pack(side="left", padx=(0, 10))

        self.search_btn = ctk.CTkButton(search_frame, text="Найти", command=self.do_search)
        self.search_btn.pack(side="left")

        from launcher.ui.components.modern_widgets import ModernCard, GlassButton
        # Results area
        self.results_card = ModernCard(self, "Результаты поиска (Modrinth)", icon_name="mods")
        self.results_card.grid(row=1, column=0, sticky="nsew")

        self.results_frame = ctk.CTkScrollableFrame(self.results_card.content, fg_color="transparent")
        self.results_frame.pack(fill="both", expand=True)

    def on_show(self):
        # Initialize ModManager based on current instance
        inst_id = self.app.config.get("last_instance", default="default")
        inst = self.app.im.get_instance(inst_id)
        if inst:
            mods_dir = f"{self.app.im.get_instance_dir(inst_id)}/mods"
            self.mm = ModManager(mods_dir)
            self.current_loader = inst['loader']
            self.current_mc_version = inst['mc_version']
            self.search_entry.configure(placeholder_text=f"Поиск модов ({self.current_loader} {self.current_mc_version})...")
        else:
            self.mm = None
            self.search_entry.configure(placeholder_text="Выберите сборку сначала")

    def do_search(self):
        query = self.search_entry.get().strip()
        if not query or not self.mm:
            return

        for w in self.results_frame.winfo_children():
            w.destroy()

        ctk.CTkLabel(self.results_frame, text="Поиск...").pack(pady=20)
        self.search_btn.configure(state="disabled")

        threading.Thread(target=self._search_thread, args=(query,), daemon=True).start()

    def _search_thread(self, query):
        results = self.mm.search_mods(query, loader=self.current_loader, version=self.current_mc_version)
        self.after(0, lambda: self._update_results(results))

    def _update_results(self, results):
        self.search_btn.configure(state="normal")
        for w in self.results_frame.winfo_children():
            w.destroy()

        if not results:
            ctk.CTkLabel(self.results_frame, text="Ничего не найдено").pack(pady=20)
            return

        for mod in results:
            f = ctk.CTkFrame(self.results_frame, fg_color="#000000", border_width=1, border_color="#333333", corner_radius=0)
            f.pack(fill="x", pady=5, padx=5)

            info = ctk.CTkFrame(f, fg_color="transparent")
            info.pack(side="left", padx=10, pady=10, fill="x", expand=True)

            ctk.CTkLabel(info, text=mod['title'], font=ctk.CTkFont(weight="bold")).pack(anchor="w")
            ctk.CTkLabel(info, text=mod.get('description', '')[:100] + "...", font=ctk.CTkFont(size=11), text_color="gray").pack(anchor="w")

            ctk.CTkButton(f, text="Установить", width=80,
                          command=lambda pid=mod['project_id']: self.install_mod(pid)).pack(side="right", padx=10, pady=10)

    def install_mod(self, project_id):
        if not self.mm: return
        Dialog("Установка", "Установка началась (см. консоль/логи)", self)

        def _inst():
            from launcher.utils.logger import get_logger
            log = get_logger("ModsTab")
            success = self.mm.install_mod(project_id, self.current_loader, self.current_mc_version)
            if success:
                log.info(f"Mod {project_id} installed successfully.")

        threading.Thread(target=_inst, daemon=True).start()
