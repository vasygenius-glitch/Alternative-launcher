import os
import subprocess
import shutil

def build():
    print("Building Cat Launcher V2...")

    subprocess.check_call(["pip", "install", "-r", "launcher/requirements.txt"])

    if os.path.exists("dist"): shutil.rmtree("dist")
    if os.path.exists("build"): shutil.rmtree("build")

    # Needs to run in project root context
    os.environ['PYTHONPATH'] = os.getcwd()

    cmd = [
        "pyinstaller", "--noconfirm", "--onedir", "--windowed",
        "--paths", os.getcwd(),
        "--name", "CatLauncherV2",
        "--hidden-import", "customtkinter",
        "--hidden-import", "PIL",
        "--hidden-import", "minecraft_launcher_lib",
        "--hidden-import", "requests",
        "--hidden-import", "pypresence",
        "--hidden-import", "launcher.app",
        "--hidden-import", "launcher.utils.logger",
        "--hidden-import", "launcher.utils.config",
        "--hidden-import", "launcher.core.auth",
        "--hidden-import", "launcher.core.instance",
        "--hidden-import", "launcher.core.launcher_engine",
        "--hidden-import", "launcher.core.discord_rpc",
        "--hidden-import", "launcher.core.server_status",
        "--hidden-import", "launcher.ui.main_window",
        "--hidden-import", "launcher.ui.tabs.home_tab",
        "--hidden-import", "launcher.ui.tabs.instances_tab",
        "--hidden-import", "launcher.ui.tabs.mods_tab",
        "--hidden-import", "launcher.ui.tabs.accounts_tab",
        "--hidden-import", "launcher.ui.tabs.settings_tab",
        "--hidden-import", "logging.handlers",
        "--add-data", "launcher:launcher",
        "--add-data", "launcher/assets:launcher/assets" if os.name != 'nt' else "launcher/assets;launcher/assets",
        "launcher/launcher.py"
    ]

    subprocess.check_call(cmd)
    print("Build complete! Check the 'dist' folder.")

if __name__ == "__main__":
    build()
