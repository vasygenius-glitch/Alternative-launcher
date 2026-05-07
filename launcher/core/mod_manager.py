import os
import requests
from launcher.utils.logger import get_logger
from launcher.core.downloader import Downloader

log = get_logger("ModManager")

class ModManager:
    """
    Interacts with Modrinth API to search, install, and manage mods.
    """
    MODRINTH_API = "https://api.modrinth.com/v2"

    def __init__(self, mods_dir):
        self.mods_dir = mods_dir
        self.downloader = Downloader(max_workers=5)
        os.makedirs(self.mods_dir, exist_ok=True)

    def search_mods(self, query, loader="forge", version="1.20.1", limit=10):
        url = f"{self.MODRINTH_API}/search"
        params = {
            "query": query,
            "facets": f'[["categories:{loader}"],["versions:{version}"],["project_type:mod"]]',
            "limit": limit
        }
        try:
            res = requests.get(url, params=params, timeout=10)
            res.raise_for_status()
            return res.json().get('hits', [])
        except Exception as e:
            log.error(f"Search failed: {e}")
            return []

    def get_latest_version_for_mod(self, project_id, loader="forge", version="1.20.1"):
        url = f"{self.MODRINTH_API}/project/{project_id}/version"
        params = {
            "loaders": f'["{loader}"]',
            "game_versions": f'["{version}"]'
        }
        try:
            res = requests.get(url, params=params, timeout=10)
            res.raise_for_status()
            data = res.json()
            if not data:
                return None
            return data[0] # Latest version
        except Exception as e:
            log.error(f"Failed to fetch version for {project_id}: {e}")
            return None

    def install_mod(self, project_id, loader="forge", version="1.20.1"):
        version_data = self.get_latest_version_for_mod(project_id, loader, version)
        if not version_data or not version_data.get('files'):
            log.warning(f"No suitable files found for {project_id}")
            return False

        file_info = version_data['files'][0]
        url = file_info['url']
        filename = file_info['filename']
        expected_hash = file_info['hashes']['sha512']
        dest_path = os.path.join(self.mods_dir, filename)

        log.info(f"Installing mod: {filename}")
        return self.downloader.download_file(url, dest_path, expected_hash, 'sha512')

    def install_mods_batch(self, project_ids, loader="forge", version="1.20.1", progress_cb=None):
        files_to_download = []
        for pid in project_ids:
            ver_data = self.get_latest_version_for_mod(pid, loader, version)
            if ver_data and ver_data.get('files'):
                f_info = ver_data['files'][0]
                files_to_download.append({
                    "url": f_info['url'],
                    "path": os.path.join(self.mods_dir, f_info['filename']),
                    "hash": f_info['hashes']['sha512'],
                    "hash_algo": "sha512"
                })
            else:
                log.warning(f"Could not resolve version for mod {pid}")

        if not files_to_download:
            return True

        return self.downloader.download_batch(files_to_download, progress_cb)

    def get_installed_mods(self):
        mods = []
        if os.path.exists(self.mods_dir):
            for f in os.listdir(self.mods_dir):
                if f.endswith(".jar"):
                    mods.append(f)
        return mods

    def delete_mod(self, filename):
        path = os.path.join(self.mods_dir, filename)
        if os.path.exists(path):
            try:
                os.remove(path)
                log.info(f"Deleted mod: {filename}")
                return True
            except Exception as e:
                log.error(f"Failed to delete {filename}: {e}")
        return False
