from pypresence import Presence
import time
import threading
from launcher.utils.logger import get_logger

log = get_logger("DiscordRPC")

class DiscordRPC:
    def __init__(self, client_id="123456789012345678"): # Placeholder ID
        self.client_id = client_id
        self.rpc = None
        self.connected = False
        self._thread = None

    def connect(self):
        try:
            self.rpc = Presence(self.client_id)
            self.rpc.connect()
            self.connected = True
            log.info("Connected to Discord RPC.")
        except Exception as e:
            log.debug(f"Could not connect to Discord RPC (is Discord running?): {e}")

    def update(self, state, details, start_time=None):
        if not self.connected:
            return
        try:
            kwargs = {"state": state, "details": details}
            if start_time:
                kwargs["start"] = start_time
            # Try to add a large image key if you have one setup in dev portal
            # kwargs["large_image"] = "cat_logo"
            self.rpc.update(**kwargs)
        except Exception as e:
            log.debug(f"Failed to update RPC: {e}")

    def disconnect(self):
        if self.connected and self.rpc:
            try:
                self.rpc.close()
            except:
                pass
            self.connected = False
