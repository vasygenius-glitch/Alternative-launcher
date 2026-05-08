import customtkinter as ctk
import os
from PIL import Image
from launcher.utils.config import ConfigManager

class MainWindow(ctk.CTk):
    def __init__(self, app_logic):
        super().__init__()
        self.app = app_logic
        self.config = ConfigManager()

        self.title("Cat Launcher V2")
        self.geometry("1000x600")
        self.minsize(900, 500)

        # Hardcode stark appearance for the Vent/Monochrome aesthetic
        ctk.set_appearance_mode("dark")

        # Override default colors
        self.configure(fg_color="#050505")

        # Setup Layout
        self.grid_rowconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=1)

        # Navigation Bar (Left)
        self.nav_frame = ctk.CTkFrame(self, corner_radius=0, width=200, fg_color="#000000", border_width=1, border_color="#333333")
        self.nav_frame.grid(row=0, column=0, sticky="nsew")
        self.nav_frame.grid_rowconfigure(5, weight=1)

        self.logo_label = ctk.CTkLabel(self.nav_frame, text="Cat Launcher\n⚡", font=ctk.CTkFont(size=20, weight="bold"))
        self.logo_label.grid(row=0, column=0, padx=20, pady=(20, 30))

        self.tabs = {}
        self.current_tab_name = None

        self._create_nav_button("Главная", 1, "home")
        self._create_nav_button("Сборки", 2, "instances")
        self._create_nav_button("Новости", 3, "news")
        self._create_nav_button("Моды", 4, "mods")
        self._create_nav_button("Аккаунты", 5, "accounts")

        self._create_nav_button("Настройки", 7, "settings")

        # Main Content Area (Right)
        self.main_frame = ctk.CTkFrame(self, fg_color="transparent")
        self.main_frame.grid(row=0, column=1, sticky="nsew", padx=20, pady=20)
        self.main_frame.grid_rowconfigure(0, weight=1)
        self.main_frame.grid_columnconfigure(0, weight=1)

    def _create_nav_button(self, text, row, tab_id):
        btn = ctk.CTkButton(self.nav_frame, corner_radius=0, height=40, border_spacing=10, text=text.upper(),
                            fg_color="transparent", text_color="#FFFFFF", hover_color="#1a1a1a",
                            font=ctk.CTkFont(family="Courier", weight="bold"),
                            anchor="w", command=lambda: self.select_tab(tab_id))
        btn.grid(row=row, column=0, sticky="ew")
        # Store button ref to change color
        if not hasattr(self, 'nav_buttons'):
            self.nav_buttons = {}
        self.nav_buttons[tab_id] = btn

    def register_tab(self, tab_id, tab_frame):
        self.tabs[tab_id] = tab_frame

    def select_tab(self, tab_id):
        if self.current_tab_name == tab_id:
            return

        # Update button colors
        for name, btn in self.nav_buttons.items():
            if name == tab_id:
                btn.configure(fg_color="#333333")
            else:
                btn.configure(fg_color="transparent")

        # Hide current
        if self.current_tab_name and self.current_tab_name in self.tabs:
            self.tabs[self.current_tab_name].grid_forget()

        # Show new
        if tab_id in self.tabs:
            self.tabs[tab_id].grid(row=0, column=0, sticky="nsew")
            # If tab has an on_show method, call it
            if hasattr(self.tabs[tab_id], 'on_show'):
                self.tabs[tab_id].on_show()

        self.current_tab_name = tab_id
