import os
import platform

def get_default_minecraft_dir():
    """
    Smart discovery of the OS's default Minecraft installation path
    so we can re-use existing game files/assets.
    """
    os_name = platform.system()
    if os_name == "Windows":
        return os.path.join(os.environ.get("APPDATA", ""), ".minecraft")
    elif os_name == "Darwin": # macOS
        return os.path.expanduser("~/Library/Application Support/minecraft")
    else: # Linux
        return os.path.expanduser("~/.minecraft")

def get_launcher_mc_dir():
    """
    Isolated directory for instances but can symlink/fallback to default.
    """
    return os.path.abspath("launcher_data/game")
