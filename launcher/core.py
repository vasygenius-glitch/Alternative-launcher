import os
import minecraft_launcher_lib
import subprocess
import platform

MINECRAFT_VERSION = "1.20.1"
FORGE_VERSION = "1.20.1-47.3.0" # A stable forge version for 1.20.1
CLIENT_ID = "YOUR_CLIENT_ID" # Placeholder for MS Login

def get_minecraft_dir():
    if platform.system() == "Windows":
        return os.path.join(os.environ["APPDATA"], ".minecraft")
    elif platform.system() == "Darwin":
        return os.path.join(os.path.expanduser("~"), "Library", "Application Support", "minecraft")
    else:
        return os.path.join(os.path.expanduser("~"), ".minecraft")

def install_forge(mc_dir, callback=None):
    if callback:
        callback("Проверка Vanilla Minecraft...", 0.05)

    callback_dict_vanilla = {}
    if callback:
        callback_dict_vanilla = {
            "setStatus": lambda text: callback(f"Minecraft: {text}", None),
            "setProgress": lambda progress: callback(None, 0.05 + (progress / 100) * 0.1),
            "setMax": lambda max_val: None
        }

    minecraft_launcher_lib.install.install_minecraft_version(MINECRAFT_VERSION, mc_dir, callback=callback_dict_vanilla)

    if callback:
        callback("Проверка Forge...", 0.15)

    # Find exact forge id, and install if not exist
    forge_id = minecraft_launcher_lib.forge.find_forge_version(FORGE_VERSION)
    if not forge_id:
        forge_id = f"{MINECRAFT_VERSION}-forge-{FORGE_VERSION}" # Fallback

    installed_versions = [v['id'] for v in minecraft_launcher_lib.utils.get_installed_versions(mc_dir)]

    # Simple check if Forge is already installed.
    if forge_id in installed_versions:
        if callback:
             callback("Forge уже установлен.", 0.3)
        return forge_id

    # Install Forge
    if callback:
        callback("Установка Forge (это может занять время)...", 0.15)

    # Setup callbacks for minecraft_launcher_lib
    callback_dict = {}
    if callback:
        callback_dict = {
            "setStatus": lambda text: callback(f"Forge: {text}", None),
            "setProgress": lambda progress: callback(None, 0.15 + (progress / 100) * 0.35),
            "setMax": lambda max_val: None
        }

    minecraft_launcher_lib.forge.install_forge_version(FORGE_VERSION, mc_dir, callback=callback_dict)

    # Try finding exact id again after install
    forge_id = minecraft_launcher_lib.forge.find_forge_version(FORGE_VERSION)
    if not forge_id:
        forge_id = f"{MINECRAFT_VERSION}-forge-{FORGE_VERSION}" # Fallback

    return forge_id

def get_aikar_flags():
    return [
        "-XX:+UseG1GC",
        "-XX:+ParallelRefProcEnabled",
        "-XX:MaxGCPauseMillis=200",
        "-XX:+UnlockExperimentalVMOptions",
        "-XX:+DisableExplicitGC",
        "-XX:+AlwaysPreTouch",
        "-XX:G1NewSizePercent=30",
        "-XX:G1MaxNewSizePercent=40",
        "-XX:G1HeapRegionSize=8M",
        "-XX:G1ReservePercent=20",
        "-XX:G1HeapWastePercent=5",
        "-XX:G1MixedGCCountTarget=4",
        "-XX:InitiatingHeapOccupancyPercent=15",
        "-XX:G1MixedGCLiveThresholdPercent=90",
        "-XX:G1RSetUpdatingPauseTimePercent=5",
        "-XX:SurvivorRatio=32",
        "-XX:+PerfDisableSharedMem",
        "-XX:MaxTenuringThreshold=1",
        "-Dusing.aikars.flags=https://mcflags.emc.gs",
        "-Daikars.new.flags=true"
    ]

def launch_game(username, is_offline=True, token_dict=None, callback=None, ram_min=2048, ram_max=4096, java_path=""):
    from logger import log
    mc_dir = get_minecraft_dir()

    if callback:
        callback("Подготовка к запуску...", 0.0)

    # Install Forge
    forge_version_id = install_forge(mc_dir, callback)

    # Launch Options
    jvm_arguments = get_aikar_flags()
    jvm_arguments.append(f"-Xms{ram_min}M")
    jvm_arguments.append(f"-Xmx{ram_max}M")

    options = {
        "username": username,
        "uuid": "",
        "token": "",
        "jvmArguments": jvm_arguments
    }
    if java_path:
        options["executablePath"] = java_path

    if is_offline:
        options["uuid"] = "00000000-0000-0000-0000-000000000000"
    elif token_dict:
        options["uuid"] = token_dict["id"]
        options["token"] = token_dict["access_token"]
        options["username"] = token_dict["name"]

    if callback:
        callback("Генерация команды запуска...", 0.95)

    minecraft_command = minecraft_launcher_lib.command.get_minecraft_command(forge_version_id, mc_dir, options)

    if callback:
        callback("Запуск игры!", 1.0)

    log.info(f"Launching Minecraft with options: RAM {ram_min}-{ram_max}MB, Java: {java_path or 'auto'}")
    subprocess.Popen(minecraft_command)

import requests
import hashlib
from concurrent.futures import ThreadPoolExecutor, as_completed

def download_file(url, path):
    response = requests.get(url, stream=True)
    if response.status_code == 200:
        with open(path, 'wb') as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        return True
    return False

def check_file_hash(path, expected_hash, hash_algo='sha512'):
    if not os.path.exists(path):
        return False

    hash_obj = hashlib.new(hash_algo)
    with open(path, "rb") as f:
        for chunk in iter(lambda: f.read(4096), b""):
            hash_obj.update(chunk)
    return hash_obj.hexdigest() == expected_hash

def _process_single_mod(mod_name, mods_dir, loader, version):
    from logger import log

    # Get mod info
    search_url = f"https://api.modrinth.com/v2/project/{mod_name}"
    res = requests.get(search_url)
    if res.status_code != 200:
        return mod_name, False, "не найден"

    # Get versions for this mod
    versions_url = f"https://api.modrinth.com/v2/project/{mod_name}/version"
    params = {
        "loaders": f'["{loader}"]',
        "game_versions": f'["{version}"]'
    }
    res_versions = requests.get(versions_url, params=params)

    if res_versions.status_code != 200 or not res_versions.json():
        return mod_name, False, "версия не найдена"

    latest_version = res_versions.json()[0]
    file_info = latest_version['files'][0]
    download_url = file_info['url']
    filename = file_info['filename']
    expected_hash = file_info['hashes']['sha512']

    filepath = os.path.join(mods_dir, filename)

    # Check if already downloaded and valid
    if os.path.exists(filepath):
        if check_file_hash(filepath, expected_hash, 'sha512'):
            return mod_name, True, "уже установлен"
        else:
            log.warning(f"Mod {mod_name} corrupted. Redownloading...")
            os.remove(filepath) # Remove corrupted file

    if download_file(download_url, filepath):
        # Verify hash after download
        if check_file_hash(filepath, expected_hash, 'sha512'):
            return mod_name, True, "скачан успешно"
        else:
            os.remove(filepath)
            return mod_name, False, "ошибка проверки хэша"
    else:
        return mod_name, False, "ошибка скачивания"

def download_modrinth_mods(mod_names, mc_dir, callback=None):
    from logger import log
    mods_dir = os.path.join(mc_dir, "mods")
    os.makedirs(mods_dir, exist_ok=True)

    loader = "forge"
    version = MINECRAFT_VERSION
    total_mods = len(mod_names)

    if total_mods == 0:
        return

    if callback:
        callback("Синхронизация модов...", 0.5)

    completed_mods = 0
    with ThreadPoolExecutor(max_workers=5) as executor:
        future_to_mod = {executor.submit(_process_single_mod, mod_name, mods_dir, loader, version): mod_name for mod_name in mod_names}
        for future in as_completed(future_to_mod):
            mod_name = future_to_mod[future]
            try:
                name, success, msg = future.result()
                completed_mods += 1
                progress = 0.5 + (completed_mods / total_mods) * 0.4
                if callback:
                    callback(f"Мод {name}: {msg}", progress)
                if not success:
                    log.error(f"Failed to process mod {name}: {msg}")
                else:
                    log.debug(f"Successfully processed mod {name}: {msg}")
            except Exception as exc:
                log.error(f"Mod {mod_name} generated an exception: {exc}")
