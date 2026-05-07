import json
import os
import threading
from launcher.utils.logger import get_logger

log = get_logger("Config")

class ConfigManager:
    _instance = None
    _lock = threading.Lock()

    def __new__(cls, config_path="launcher_data/config.json"):
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ConfigManager, cls).__new__(cls)
                cls._instance._init_config(config_path)
            return cls._instance

    def _init_config(self, config_path):
        self.config_path = config_path
        self.data = {}

        # Default settings
        self.defaults = {
            "launcher": {
                "theme": "dark",
                "color": "blue",
                "close_on_launch": True,
                "discord_rpc": True,
                "language": "ru"
            },
            "java": {
                "ram_min": 2048,
                "ram_max": 4096,
                "java_path": "",
                "custom_args": ""
            },
            "last_instance": "default",
            "active_account": None
        }

        self.load()

    def load(self):
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        if not os.path.exists(self.config_path):
            self.data = self.defaults.copy()
            self.save()
            return

        try:
            with open(self.config_path, "r", encoding="utf-8") as f:
                loaded_data = json.load(f)

            # Merge defaults with loaded data to ensure new keys exist
            self.data = self._merge_dicts(self.defaults.copy(), loaded_data)
            log.info("Configuration loaded successfully.")
        except Exception as e:
            log.error(f"Failed to load config, using defaults. Error: {e}")
            self.data = self.defaults.copy()

    def _merge_dicts(self, default, custom):
        for key, value in default.items():
            if isinstance(value, dict):
                node = custom.setdefault(key, {})
                self._merge_dicts(value, node)
            else:
                custom.setdefault(key, value)
        return custom

    def save(self):
        try:
            with open(self.config_path, "w", encoding="utf-8") as f:
                json.dump(self.data, f, indent=4)
            log.debug("Configuration saved.")
        except Exception as e:
            log.error(f"Failed to save config: {e}")

    def get(self, section, key, default=None):
        return self.data.get(section, {}).get(key, default)

    def set(self, section, key, value):
        if section not in self.data:
            self.data[section] = {}
        self.data[section][key] = value
        self.save()

    def get_all(self):
        return self.data
