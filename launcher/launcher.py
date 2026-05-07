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
        self.progress_frame = ctk.CTkFrame(self, fg_color="transparent", bg_color="transparent")
        self.progress_frame.place(relx=0.5, rely=0.85, anchor=ctk.CENTER)

        self.progress_bar = ctk.CTkProgressBar(self.progress_frame, width=500, height=15, corner_radius=10, progress_color="#28a745")
        self.progress_bar.set(0)
        self.progress_bar.pack(pady=(0, 10))
        self.progress_bar.pack_forget() # Hide initially

        # Status Label
        self.status_label = ctk.CTkLabel(self.progress_frame, text="", text_color="white", bg_color="transparent", font=ctk.CTkFont(size=14, weight="bold"))
        self.status_label.pack()

        self.is_launching = False

    def thread_safe_update(self, text, progress):
        if text is not None:
            self.status_label.configure(text=text)
        if progress is not None:
            self.progress_bar.pack(pady=(0, 10)) # Show progress bar
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

        if not username:
            self.update_status("Введите никнейм!")
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
