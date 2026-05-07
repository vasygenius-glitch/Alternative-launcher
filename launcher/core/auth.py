import json
import os
import uuid
from launcher.utils.logger import get_logger

log = get_logger("AuthManager")

class AuthManager:
    """
    Manages user accounts (offline and placeholders for Microsoft/Online).
    Stores accounts securely in accounts.json.
    """
    def __init__(self, accounts_file="launcher_data/accounts.json"):
        self.accounts_file = accounts_file
        self.accounts = {}
        self.active_account_id = None
        self.load_accounts()

    def load_accounts(self):
        os.makedirs(os.path.dirname(self.accounts_file), exist_ok=True)
        if not os.path.exists(self.accounts_file):
            self.save_accounts()
            return

        try:
            with open(self.accounts_file, "r", encoding="utf-8") as f:
                data = json.load(f)
                self.accounts = data.get("accounts", {})
                self.active_account_id = data.get("active_account_id")
        except Exception as e:
            log.error(f"Failed to load accounts: {e}")

    def save_accounts(self):
        try:
            with open(self.accounts_file, "w", encoding="utf-8") as f:
                json.dump({
                    "accounts": self.accounts,
                    "active_account_id": self.active_account_id
                }, f, indent=4)
        except Exception as e:
            log.error(f"Failed to save accounts: {e}")

    def add_offline_account(self, username):
        account_id = str(uuid.uuid4())
        # Generate offline UUID (MD5 hash based like vanilla offline mode)
        import hashlib
        offline_uuid = str(uuid.UUID(bytes=hashlib.md5(f"OfflinePlayer:{username}".encode('utf-8')).digest()[:16], version=3))

        self.accounts[account_id] = {
            "type": "offline",
            "username": username,
            "uuid": offline_uuid,
            "access_token": "null"
        }
        self.active_account_id = account_id
        self.save_accounts()
        log.info(f"Added offline account: {username}")
        return account_id

    def add_microsoft_account(self, username, uuid_str, access_token, refresh_token):
        """Placeholder for Microsoft Auth."""
        account_id = str(uuid.uuid4())
        self.accounts[account_id] = {
            "type": "microsoft",
            "username": username,
            "uuid": uuid_str,
            "access_token": access_token,
            "refresh_token": refresh_token
        }
        self.active_account_id = account_id
        self.save_accounts()
        log.info(f"Added Microsoft account: {username}")
        return account_id

    def remove_account(self, account_id):
        if account_id in self.accounts:
            username = self.accounts[account_id]['username']
            del self.accounts[account_id]
            if self.active_account_id == account_id:
                self.active_account_id = list(self.accounts.keys())[0] if self.accounts else None
            self.save_accounts()
            log.info(f"Removed account: {username}")

    def get_active_account(self):
        if not self.active_account_id or self.active_account_id not in self.accounts:
            return None
        return self.accounts[self.active_account_id]

    def set_active_account(self, account_id):
        if account_id in self.accounts:
            self.active_account_id = account_id
            self.save_accounts()
            log.info(f"Active account set to: {self.accounts[account_id]['username']}")

    def get_all_accounts(self):
        return self.accounts
