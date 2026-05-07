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
        "--name", "CatLauncherV2",
        "--hidden-import", "customtkinter",
        "--hidden-import", "PIL",
        "--hidden-import", "minecraft_launcher_lib",
        "--hidden-import", "requests",
        "--hidden-import", "pypresence",
        "--add-data", "launcher/assets:launcher/assets" if os.name != 'nt' else "launcher/assets;launcher/assets",
        "launcher/launcher.py"
    ]

    subprocess.check_call(cmd)
    print("Build complete! Check the 'dist' folder.")

if __name__ == "__main__":
    build()
