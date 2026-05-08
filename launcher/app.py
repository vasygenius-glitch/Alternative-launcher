import sys
import os
import time
import threading

from launcher.utils.logger import get_logger
from launcher.utils.config import ConfigManager
from launcher.core.auth import AuthManager
from launcher.core.instance import InstanceManager
from launcher.core.launcher_engine import LauncherEngine
from launcher.core.discord_rpc import DiscordRPC
from launcher.core.server_status import ping_server

from launcher.ui.main_window import MainWindow
from launcher.ui.tabs.home_tab import HomeTab
from launcher.ui.tabs.instances_tab import InstancesTab
from launcher.ui.tabs.news_tab import NewsTab
from launcher.ui.tabs.mods_tab import ModsTab
from launcher.ui.tabs.accounts_tab import AccountsTab
from launcher.ui.tabs.settings_tab import SettingsTab

log = get_logger("App")

class CatLauncherApp:
    """
    Main controller tying core logic to UI.
    """
    def __init__(self):
        from launcher.core.launcher_integrity import LauncherIntegrity
        LauncherIntegrity.verify_environment()

        log.info("Initializing CatLauncherV2...")
        self.config = ConfigManager()
        self.auth = AuthManager()
        self.im = InstanceManager()
        self.engine = LauncherEngine(self.im)

        self.rpc = DiscordRPC()
        if self.config.get("launcher", "discord_rpc", True):
            self.rpc.connect()
            self.rpc.update("В меню", "Выбирает сервер")

    def run(self):
        self.ui = MainWindow(self)

        # Register Tabs
        self.ui.register_tab("home", HomeTab(self.ui.main_frame, self))
        self.ui.register_tab("instances", InstancesTab(self.ui.main_frame, self))
        self.ui.register_tab("news", NewsTab(self.ui.main_frame, self))
        self.ui.register_tab("mods", ModsTab(self.ui.main_frame, self))
        self.ui.register_tab("accounts", AccountsTab(self.ui.main_frame, self))
        self.ui.register_tab("settings", SettingsTab(self.ui.main_frame, self))

        # Initial Tab
        self.ui.select_tab("home")

        log.info("UI Started.")

        # If splash screen from PyInstaller exists, close it
        try:
            import pyi_splash
            pyi_splash.close()
            log.info("PyInstaller splash screen closed.")
        except ImportError:
            pass

        self.ui.mainloop()

        # Cleanup
        self.rpc.disconnect()

    def ping_server(self, ip):
        return ping_server(ip)

    def launch_game(self, progress_cb):
        account = self.auth.get_active_account()
        if not account:
            progress_cb(100, "Ошибка: Аккаунт не выбран")
            return

        instance_id = self.config.get("last_instance", default="default")
        instance = self.im.get_instance(instance_id)
        if not instance:
            progress_cb(100, "Ошибка: Сборка не выбрана")
            return

        try:
            # Install / verify files
            log.info(f"Preparing to launch instance {instance_id}")
            self.rpc.update("Подготовка к запуску...", instance['name'])

            # Step 1: Disk check
            from launcher.core.system_info import SystemInfo
            if not SystemInfo.check_disk_space(self.im.get_instance_dir(instance_id), 1024):
                progress_cb(100, "Ошибка: Недостаточно места на диске (минимум 1 ГБ)")
                return

            # Step 2: Cache cleanup and verification
            from launcher.core.cache_manager import CacheManager
            cm = CacheManager()
            cm.perform_full_cleanup()

            # Verification is best-effort. If we had an expected_hashes dict, we'd pass it here.
            progress_cb(10, "Проверка целостности файлов...")
            cm.verify_integrity(self.im.get_instance_dir(instance_id))

            # Step 3: Install
            ver_id = self.engine.install_and_get_version(instance_id, progress_cb)

            progress_cb(95, "Генерация параметров запуска...")

            # Start game process
            process = self.engine.build_command_and_launch(instance_id, account, ver_id)

            progress_cb(100, "Игра запущена!")
            self.rpc.update("Играет в Minecraft", f"Сборка: {instance['name']}", start_time=int(time.time()))

            if self.config.get("launcher", "close_on_launch", True):
                log.info("Closing launcher as requested.")
                # Give UI time to update then exit
                self.ui.after(2000, self.ui.destroy)
            else:
                # If we keep launcher open, monitor the process for crashes
                def monitor_process():
                    process.wait()
                    log.info(f"Minecraft process exited with code {process.returncode}")
                    if process.returncode != 0:
                        from launcher.core.crash_analyzer import CrashAnalyzer
                        analysis = CrashAnalyzer.analyze_crash(self.im.get_instance_dir(instance_id))
                        if analysis:
                            # Show crash dialog via UI thread
                            self.ui.after(0, lambda: self._show_crash_dialog(analysis))
                        else:
                            self.ui.after(0, lambda: self._show_crash_dialog({
                                "title": "Неизвестная ошибка",
                                "solution": f"Игра завершилась с кодом {process.returncode}."
                            }))

                    self.rpc.update("В меню", "Выбирает сервер")

                threading.Thread(target=monitor_process, daemon=True).start()

        except Exception as e:
            log.error(f"Launch failed: {e}", exc_info=True)
            progress_cb(100, f"Ошибка запуска: {e}")
            self.rpc.update("Ошибка запуска", instance['name'])

    def _show_crash_dialog(self, analysis):
        from launcher.ui.components.dialogs import Dialog
        msg = f"{analysis['title']}\n\n{analysis['solution']}"
        Dialog("Анализ вылета", msg, self.ui)
