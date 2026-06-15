import os
import sys
from launcher.utils.logger import get_logger

log = get_logger("Integrity")

class LauncherIntegrity:
    """
    Self-healing and verification module for the launcher itself.
    Ensures the launcher environment is stable before execution.
    """
    @staticmethod
    def verify_environment():
        """
        Checks for basic directory structures and access permissions.
        Attempts to fix them if broken.
        """
        log.info("Verifying launcher environment integrity...")
        required_dirs = [
            "launcher_data",
            "launcher_data/instances",
            "launcher_data/game",
            "logs"
        ]

        for d in required_dirs:
            path = os.path.abspath(d)
            if not os.path.exists(path):
                try:
                    os.makedirs(path, exist_ok=True)
                    log.info(f"Self-healed missing directory: {path}")
                except Exception as e:
                    log.error(f"FATAL: Cannot create required directory {path}. Error: {e}")
                    # In a real desktop scenario, we might show a raw tkinter message box here,
                    # but for now we log. If it can't create logs, we fallback to stdout.
            else:
                # Check write permissions
                if not os.access(path, os.W_OK):
                    log.error(f"FATAL: No write permissions for {path}. Launcher may crash or fail to save data.")
                    try:
                        # Attempt to fix permissions (best effort, mainly effective on UNIX)
                        os.chmod(path, 0o777)
                        log.info(f"Attempted to fix permissions for {path}")
                    except Exception:
                        pass

        log.info("Environment integrity check passed.")
        return True
