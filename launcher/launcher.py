import os
import sys
import threading
import customtkinter as ctk
from PIL import Image

import core
import config
from settings import load_settings, save_settings
from logger import log
import re

ctk.set_appearance_mode("dark")
ctk.set_default_color_theme("blue")

class LauncherApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        self.title("Cat Launcher")
        self.geometry("800x500")
        self.resizable(False, False)

        # Background setup
        if getattr(sys, 'frozen', False):
            base_path = sys._MEIPASS
        else:
            base_path = os.path.dirname(os.path.abspath(__file__))

        bg_path = os.path.join(base_path, "background.png")

        try:
            bg_image = Image.open(bg_path)
            self.bg_photo = ctk.CTkImage(light_image=bg_image, dark_image=bg_image, size=(800, 500))
            self.bg_label = ctk.CTkLabel(self, image=self.bg_photo, text="")
            self.bg_label.place(x=0, y=0, relwidth=1, relheight=1)
        except Exception as e:
            print(f"Error loading background image: {e}")

        # Login Frame
        # Added semi-transparent black background by styling the frame
        self.login_frame = ctk.CTkFrame(self, fg_color="#222222", corner_radius=20, border_width=2, border_color="#555555", bg_color="transparent")
        self.login_frame.place(relx=0.5, rely=0.5, anchor=ctk.CENTER)

        self.title_label = ctk.CTkLabel(self.login_frame, text="Cat Server Launcher", font=ctk.CTkFont(size=28, weight="bold"), text_color="#FFFFFF")
        self.title_label.pack(pady=(30, 15), padx=40)

        # Username
        self.username_entry = ctk.CTkEntry(self.login_frame, placeholder_text="Никнейм", width=280, height=45, font=ctk.CTkFont(size=18), corner_radius=10, fg_color="#333333", border_color="#555555")
        self.username_entry.pack(pady=(10, 25), padx=40)

        # Buttons
        self.play_button = ctk.CTkButton(self.login_frame, text="ИГРАТЬ", command=self.on_play_click, width=280, height=50, font=ctk.CTkFont(size=20, weight="bold"), fg_color="#28a745", hover_color="#218838", corner_radius=10)
        self.play_button.pack(pady=(10, 30), padx=40)

        # Progress Bar Frame (Hidden initially)
        # Added semi-transparent dark background so text is readable over any background image
        self.progress_frame = ctk.CTkFrame(self, fg_color="#222222", corner_radius=15, border_width=1, border_color="#555555", bg_color="transparent")

        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, width=480, height=15, corner_radius=10, progress_color="#28a745", fg_color="#444444")
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=(15, 5), padx=20)

        # Status Label
        self.status_label = ctk.CTkLabel(self.progress_frame, text="", text_color="#FFFFFF", bg_color="transparent", font=ctk.CTkFont(size=14, weight="bold"))
        self.status_label.pack(pady=(0, 15), padx=20)

        self.settings = load_settings()
        self.username_entry.insert(0, self.settings.get("username", ""))

        # Settings Button
        self.settings_button = ctk.CTkButton(self.login_frame, text="⚙", width=40, height=40, font=ctk.CTkFont(size=20), command=self.open_settings, fg_color="transparent", hover_color="#444444")
        self.settings_button.place(relx=0.9, rely=0.1, anchor=ctk.CENTER)

        self.is_launching = False
        log.info("Launcher UI initialized")

    def open_settings(self):
        settings_window = ctk.CTkToplevel(self)
        settings_window.title("Настройки")
        settings_window.geometry("400x300")
        settings_window.resizable(False, False)
        settings_window.grab_set() # Make modal

        ctk.CTkLabel(settings_window, text="Выделение памяти (MB)", font=ctk.CTkFont(weight="bold")).pack(pady=(20,5))

        ram_frame = ctk.CTkFrame(settings_window, fg_color="transparent")
        ram_frame.pack()

        ctk.CTkLabel(ram_frame, text="Min:").pack(side=ctk.LEFT, padx=5)
        min_ram_entry = ctk.CTkEntry(ram_frame, width=80)
        min_ram_entry.insert(0, str(self.settings.get("ram_min", 2048)))
        min_ram_entry.pack(side=ctk.LEFT, padx=5)

        ctk.CTkLabel(ram_frame, text="Max:").pack(side=ctk.LEFT, padx=5)
        max_ram_entry = ctk.CTkEntry(ram_frame, width=80)
        max_ram_entry.insert(0, str(self.settings.get("ram_max", 4096)))
        max_ram_entry.pack(side=ctk.LEFT, padx=5)

        ctk.CTkLabel(settings_window, text="Путь к Java (оставьте пустым для авто)", font=ctk.CTkFont(weight="bold")).pack(pady=(20,5))
        java_entry = ctk.CTkEntry(settings_window, width=300)
        java_entry.insert(0, self.settings.get("java_path", ""))
        java_entry.pack(pady=5)

        def save_and_close():
            try:
                self.settings["ram_min"] = int(min_ram_entry.get())
                self.settings["ram_max"] = int(max_ram_entry.get())
                self.settings["java_path"] = java_entry.get().strip()
                save_settings(self.settings)
                log.info("Settings saved via UI")
                settings_window.destroy()
            except ValueError:
                log.error("Invalid RAM value entered in settings")

        ctk.CTkButton(settings_window, text="Сохранить", command=save_and_close).pack(pady=30)

    def thread_safe_update(self, text, progress):
        # Show the frame when we start updating
        if not self.progress_frame.winfo_ismapped():
            self.progress_frame.place(relx=0.5, rely=0.85, anchor=ctk.CENTER)

        if text is not None:
            self.status_label.configure(text=text)
            log.debug(f"UI Status Update: {text}")
        if progress is not None:
            self.progress_bar.set(progress)

    def update_status(self, text, progress=None):
        # Schedule the UI update on the main thread
        self.after(0, lambda: self.thread_safe_update(text, progress))

    def launch_sequence(self, username, is_offline):
        try:
            # 1. Get Directory
            mc_dir = core.get_minecraft_dir()

            # 2. Download Mods
            core.download_modrinth_mods(config.MODS_LIST, mc_dir, self.update_status)

            # 3. Launch Game
            core.launch_game(
                username,
                is_offline=is_offline,
                callback=self.update_status,
                ram_min=self.settings.get("ram_min", 2048),
                ram_max=self.settings.get("ram_max", 4096),
                java_path=self.settings.get("java_path", "")
            )

            self.update_status("Игра запущена!", 1.0)
            log.info("Game launched successfully.")

            # Close launcher after 3 seconds if setting allows
            if self.settings.get("close_on_launch", True):
                self.after(3000, self.destroy)
            else:
                self.is_launching = False
                self.after(3000, lambda: self.progress_frame.place_forget())

        except Exception as e:
            error_msg = f"Ошибка запуска: {str(e)}"
            log.error(error_msg, exc_info=True)
            self.update_status(error_msg)
            self.is_launching = False

    def on_play_click(self):
        if self.is_launching:
            return

        username = self.username_entry.get().strip()

        # Validate Nickname (3-16 chars, alphanumeric and underscore)
        if not username:
            self.update_status("Введите никнейм!")
            return
        if not re.match(r"^[a-zA-Z0-9_]{3,16}$", username):
            self.update_status("Никнейм должен быть от 3 до 16 символов (A-Z, 0-9, _)")
            return

        # Save valid username
        self.settings["username"] = username
        save_settings(self.settings)

        self.is_launching = True
        log.info(f"Starting launch sequence for user: {username}")
        self.update_status(f"Подготовка к запуску для {username}...")

        # Run in thread so GUI doesn't freeze
        threading.Thread(target=self.launch_sequence, args=(username, True), daemon=True).start()


    def on_ms_login_click(self):
        # Placeholder for MS Login implementation
        self.update_status("Вход через Microsoft пока не реализован. Используйте 'Играть'.")

if __name__ == "__main__":
    app = LauncherApp()
    app.mainloop()
