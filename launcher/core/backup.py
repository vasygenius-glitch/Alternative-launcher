import os
import shutil
import zipfile
from datetime import datetime
from launcher.utils.logger import get_logger

log = get_logger("BackupSys")

class BackupSystem:
    def __init__(self, backups_dir="launcher_data/backups"):
        self.backups_dir = os.path.abspath(backups_dir)
        os.makedirs(self.backups_dir, exist_ok=True)

    def backup_folder(self, source_dir, backup_name=None):
        if not os.path.exists(source_dir):
            log.warning(f"Cannot backup, source doesn't exist: {source_dir}")
            return False

        if not backup_name:
            folder_name = os.path.basename(os.path.normpath(source_dir))
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            backup_name = f"{folder_name}_backup_{timestamp}.zip"

        dest_path = os.path.join(self.backups_dir, backup_name)
        log.info(f"Creating backup of {source_dir} -> {dest_path}")

        try:
            with zipfile.ZipFile(dest_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                for root, dirs, files in os.walk(source_dir):
                    for file in files:
                        file_path = os.path.join(root, file)
                        arcname = os.path.relpath(file_path, source_dir)
                        zipf.write(file_path, arcname)
            log.info("Backup completed successfully.")
            return True
        except Exception as e:
            log.error(f"Backup failed: {e}")
            return False

    def get_backups(self):
        return [f for f in os.listdir(self.backups_dir) if f.endswith('.zip')]
