import os
import sys
import threading
import customtkinter as ctk
from PIL import Image

import core
import config

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
        self.login_frame = ctk.CTkFrame(self, fg_color="gray20", corner_radius=15, bg_color="transparent")
        self.login_frame.place(relx=0.5, rely=0.5, anchor=ctk.CENTER)

        self.title_label = ctk.CTkLabel(self.login_frame, text="Cat Server Launcher", font=ctk.CTkFont(size=24, weight="bold"))
        self.title_label.pack(pady=(20, 10), padx=20)

        # Username
        self.username_entry = ctk.CTkEntry(self.login_frame, placeholder_text="Никнейм", width=200)
        self.username_entry.pack(pady=10, padx=20)

        # Access Key
        self.key_entry = ctk.CTkEntry(self.login_frame, placeholder_text="Ключ доступа", show="*", width=200)
        self.key_entry.pack(pady=10, padx=20)

        # Buttons
        self.play_button = ctk.CTkButton(self.login_frame, text="Играть", command=self.on_play_click)
        self.play_button.pack(pady=(10, 5), padx=20)

        # MS Login (Placeholder)
        self.ms_login_button = ctk.CTkButton(self.login_frame, text="Вход Microsoft", command=self.on_ms_login_click, fg_color="#00a4ef", hover_color="#008ecc")
        self.ms_login_button.pack(pady=(5, 20), padx=20)

        # Status Label
        self.status_label = ctk.CTkLabel(self, text="", text_color="white", bg_color="transparent", font=ctk.CTkFont(size=14, weight="bold"))
        self.status_label.place(relx=0.5, rely=0.9, anchor=ctk.CENTER)

        self.is_launching = False

    def update_status(self, text):
        self.status_label.configure(text=text)
        self.update()

    def launch_sequence(self, username, is_offline):
        try:
            # 1. Get Directory
            mc_dir = core.get_minecraft_dir()

            # 2. Download Mods
            core.download_modrinth_mods(config.MODS_LIST, mc_dir, self.update_status)

            # 3. Launch Game
            core.launch_game(username, is_offline=is_offline, callback=self.update_status)

            self.update_status("Игра запущена!")

            # Close launcher after 3 seconds
            self.after(3000, self.destroy)
        except Exception as e:
            self.update_status(f"Ошибка: {e}")
        finally:
            self.is_launching = False

    def on_play_click(self):
        if self.is_launching:
            return

        username = self.username_entry.get().strip()
        key = self.key_entry.get().strip()

        if not username:
            self.update_status("Введите никнейм!")
            return

        if not key:
            self.update_status("Введите ключ доступа!")
            return

        if key != config.SERVER_KEY:
            self.update_status("Неверный ключ доступа!")
            return

        self.is_launching = True
        self.update_status(f"Подготовка к запуску для {username}...")

        # Run in thread so GUI doesn't freeze
        threading.Thread(target=self.launch_sequence, args=(username, True), daemon=True).start()


    def on_ms_login_click(self):
        # Placeholder for MS Login implementation
        self.update_status("Вход через Microsoft пока не реализован. Используйте 'Играть'.")

if __name__ == "__main__":
    app = LauncherApp()
    app.mainloop()
