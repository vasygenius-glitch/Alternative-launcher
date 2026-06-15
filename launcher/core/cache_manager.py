import os
import shutil
import time
import hashlib
from launcher.utils.logger import get_logger

log = get_logger("CacheManager")

class CacheManager:
    """
    Industrial-grade garbage collector and integrity verification module.
    """
    def __init__(self, launcher_data_dir="launcher_data"):
        self.base_dir = os.path.abspath(launcher_data_dir)
        self.logs_dir = os.path.join(os.getcwd(), "logs")
        self.temp_dir = os.path.join(self.base_dir, "temp")

        # Ensure base directories exist
        os.makedirs(self.temp_dir, exist_ok=True)

    def _safe_remove(self, path):
        """Removes a file or directory safely with permissions check."""
        try:
            if not os.path.exists(path):
                return True

            if os.path.isfile(path):
                # Try to ensure write permissions before deleting
                os.chmod(path, 0o777)
                os.remove(path)
            elif os.path.isdir(path):
                shutil.rmtree(path)
            return True
        except PermissionError:
            log.error(f"Permission denied: Could not delete {path}. It might be in use by another process (e.g., Antivirus or Java).")
            return False
        except Exception as e:
            log.error(f"Failed to remove {path}: {e}")
            return False

    def clean_old_logs(self, max_days=7):
        """Deletes log files older than max_days."""
        if not os.path.exists(self.logs_dir): return

        now = time.time()
        count = 0
        try:
            for f in os.listdir(self.logs_dir):
                if f.endswith(".log"):
                    path = os.path.join(self.logs_dir, f)
                    if os.stat(path).st_mtime < now - (max_days * 86400):
                        if self._safe_remove(path):
                            count += 1
            if count > 0:
                log.info(f"Cleaned {count} old log files.")
        except Exception as e:
            log.error(f"Error during log cleanup: {e}")

    def clean_temp_data(self, max_days=3):
        """Cleans up leftover temporary files."""
        if not os.path.exists(self.temp_dir): return

        now = time.time()
        count = 0
        try:
            for root, dirs, files in os.walk(self.temp_dir, topdown=False):
                for name in files:
                    path = os.path.join(root, name)
                    if os.stat(path).st_mtime < now - (max_days * 86400):
                        if self._safe_remove(path):
                            count += 1
                for name in dirs:
                    path = os.path.join(root, name)
                    # Remove empty directories
                    if not os.listdir(path):
                        self._safe_remove(path)
            if count > 0:
                log.info(f"Cleaned {count} old temporary files/folders.")
        except Exception as e:
            log.error(f"Error during temp data cleanup: {e}")

    def _calculate_sha1(self, filepath):
        if not os.path.exists(filepath):
            return None
        hash_obj = hashlib.sha1()
        try:
            with open(filepath, "rb") as f:
                for chunk in iter(lambda: f.read(4096), b""):
                    hash_obj.update(chunk)
            return hash_obj.hexdigest()
        except Exception as e:
            log.error(f"Failed to calculate hash for {filepath}: {e}")
            return None

    def verify_integrity(self, instance_dir, expected_libraries=None):
        """
        Deep scan of game libraries. Deletes 0-byte files or files with mismatched hashes.
        `expected_libraries` should be a dict of {relative_path: expected_sha1}.
        Returns the number of corrupted files found and deleted.
        """
        log.info(f"Starting integrity verification for {instance_dir}...")
        corrupted_count = 0

        libraries_dir = os.path.join(instance_dir, "libraries")
        if not os.path.exists(libraries_dir):
            log.warning(f"Libraries directory not found at {libraries_dir}")
            return 0

        # Scan all jar files
        for root, dirs, files in os.walk(libraries_dir):
            for file in files:
                if not file.endswith(".jar"): continue

                filepath = os.path.join(root, file)

                try:
                    # 1. Check for 0-byte files
                    if os.path.getsize(filepath) == 0:
                        log.warning(f"Corrupted file found (0 bytes): {filepath}")
                        if self._safe_remove(filepath):
                            corrupted_count += 1
                        continue

                    # 2. Check hash if reference is provided
                    if expected_libraries:
                        rel_path = os.path.relpath(filepath, libraries_dir).replace('\\', '/')
                        expected_hash = expected_libraries.get(rel_path)

                        if expected_hash:
                            actual_hash = self._calculate_sha1(filepath)
                            if actual_hash != expected_hash:
                                log.warning(f"Hash mismatch for {rel_path}. Expected: {expected_hash}, Got: {actual_hash}")
                                if self._safe_remove(filepath):
                                    corrupted_count += 1

                except Exception as e:
                    log.error(f"Error checking integrity of {filepath}: {e}")

        if corrupted_count > 0:
            log.warning(f"Integrity check finished. Removed {corrupted_count} corrupted library files.")
        else:
            log.info("Integrity check passed perfectly. No corrupted files found.")

        return corrupted_count

    def perform_full_cleanup(self):
        """Runs all cleanup routines safely in a background thread context."""
        log.info("Starting full cache cleanup...")
        self.clean_old_logs()
        self.clean_temp_data()
        log.info("Full cache cleanup finished.")
