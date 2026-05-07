import requests
import hashlib
import os
import concurrent.futures
from launcher.utils.logger import get_logger

log = get_logger("Downloader")

class Downloader:
    """
    Advanced multi-threaded downloader with hash verification, retries, and progress tracking.
    """
    def __init__(self, max_workers=10):
        self.max_workers = max_workers

    def calculate_hash(self, filepath, algo='sha512'):
        if not os.path.exists(filepath):
            return None
        hash_obj = hashlib.new(algo)
        with open(filepath, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hash_obj.update(chunk)
        return hash_obj.hexdigest()

    def download_file(self, url, dest_path, expected_hash=None, hash_algo='sha512', retries=3):
        for attempt in range(retries):
            try:
                # Ensure directory exists
                os.makedirs(os.path.dirname(dest_path), exist_ok=True)

                # If file exists and hash matches, skip
                if expected_hash and os.path.exists(dest_path):
                    if self.calculate_hash(dest_path, hash_algo) == expected_hash:
                        log.debug(f"File already exists and is valid: {dest_path}")
                        return True

                log.debug(f"Downloading {url} to {dest_path} (Attempt {attempt+1}/{retries})")
                response = requests.get(url, stream=True, timeout=15)
                response.raise_for_status()

                with open(dest_path, 'wb') as f:
                    for chunk in response.iter_content(chunk_size=8192):
                        if chunk:
                            f.write(chunk)

                # Verify hash after download
                if expected_hash:
                    actual_hash = self.calculate_hash(dest_path, hash_algo)
                    if actual_hash != expected_hash:
                        log.warning(f"Hash mismatch for {dest_path}. Expected {expected_hash}, got {actual_hash}")
                        os.remove(dest_path)
                        continue # Retry

                return True

            except Exception as e:
                log.warning(f"Failed to download {url}: {e}")
                if attempt == retries - 1:
                    log.error(f"Max retries reached for {url}")
                    return False
        return False

    def download_batch(self, files_info, progress_callback=None):
        """
        files_info: List of dicts [{"url": "...", "path": "...", "hash": "...", "hash_algo": "sha512"}]
        """
        total = len(files_info)
        completed = 0
        success_count = 0

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            future_to_file = {}
            for item in files_info:
                future = executor.submit(
                    self.download_file,
                    item['url'],
                    item['path'],
                    item.get('hash'),
                    item.get('hash_algo', 'sha512')
                )
                future_to_file[future] = item

            for future in concurrent.futures.as_completed(future_to_file):
                item = future_to_file[future]
                try:
                    success = future.result()
                    if success:
                        success_count += 1
                except Exception as exc:
                    log.error(f"Batch download generated an exception for {item['url']}: {exc}")
                finally:
                    completed += 1
                    if progress_callback:
                        progress_callback(completed, total, item['path'].split(os.sep)[-1])

        return success_count == total
