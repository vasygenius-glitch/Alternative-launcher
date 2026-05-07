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
        callback("Проверка/Установка Forge...")

    # Find exact forge id, and install if not exist
    forge_id = minecraft_launcher_lib.forge.find_forge_version(FORGE_VERSION)
    if not forge_id:
        forge_id = f"{MINECRAFT_VERSION}-forge-{FORGE_VERSION}" # Fallback

    installed_versions = [v['id'] for v in minecraft_launcher_lib.utils.get_installed_versions(mc_dir)]

    # Simple check if Forge is already installed.
    if forge_id in installed_versions:
        if callback:
             callback("Forge уже установлен.")
        return forge_id

    # Install Forge
    minecraft_launcher_lib.forge.install_forge_version(FORGE_VERSION, mc_dir)

    # Try finding exact id again after install
    forge_id = minecraft_launcher_lib.forge.find_forge_version(FORGE_VERSION)
    if not forge_id:
        forge_id = f"{MINECRAFT_VERSION}-forge-{FORGE_VERSION}" # Fallback

    return forge_id

def launch_game(username, is_offline=True, token_dict=None, callback=None):
    mc_dir = get_minecraft_dir()

    if callback:
        callback("Подготовка к запуску...")

    # Install Forge
    forge_version_id = install_forge(mc_dir, callback)

    # Launch Options
    options = {
        "username": username,
        "uuid": "",
        "token": ""
    }

    if is_offline:
        options["uuid"] = "00000000-0000-0000-0000-000000000000"
    elif token_dict:
        options["uuid"] = token_dict["id"]
        options["token"] = token_dict["access_token"]
        options["username"] = token_dict["name"]

    if callback:
        callback("Генерация команды запуска...")

    minecraft_command = minecraft_launcher_lib.command.get_minecraft_command(forge_version_id, mc_dir, options)

    if callback:
        callback("Запуск игры!")

    subprocess.Popen(minecraft_command)

import requests
import hashlib

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

def download_modrinth_mods(mod_names, mc_dir, callback=None):
    mods_dir = os.path.join(mc_dir, "mods")
    os.makedirs(mods_dir, exist_ok=True)

    loader = "forge"
    version = MINECRAFT_VERSION

    for mod_name in mod_names:
        if callback:
            callback(f"Поиск мода {mod_name}...")

        # Get mod info
        search_url = f"https://api.modrinth.com/v2/project/{mod_name}"
        res = requests.get(search_url)
        if res.status_code != 200:
            if callback:
                callback(f"Мод {mod_name} не найден!")
            continue

        # Get versions for this mod
        versions_url = f"https://api.modrinth.com/v2/project/{mod_name}/version"
        params = {
            "loaders": f'["{loader}"]',
            "game_versions": f'["{version}"]'
        }
        res_versions = requests.get(versions_url, params=params)

        if res_versions.status_code != 200 or not res_versions.json():
            if callback:
                callback(f"Версия {mod_name} для {loader} {version} не найдена!")
            continue

        latest_version = res_versions.json()[0]
        file_info = latest_version['files'][0]
        download_url = file_info['url']
        filename = file_info['filename']
        expected_hash = file_info['hashes']['sha512']

        filepath = os.path.join(mods_dir, filename)

        # Check if already downloaded and valid
        if os.path.exists(filepath):
            if check_file_hash(filepath, expected_hash, 'sha512'):
                if callback:
                    callback(f"Мод {mod_name} уже установлен.")
                continue
            else:
                os.remove(filepath) # Remove corrupted file

        if callback:
            callback(f"Скачивание {mod_name}...")

        if download_file(download_url, filepath):
             if callback:
                callback(f"Мод {mod_name} успешно скачан.")
        else:
            if callback:
                callback(f"Ошибка при скачивании {mod_name}.")
