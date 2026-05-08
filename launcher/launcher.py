import sys
import os

# Adjust path for internal imports if frozen
if getattr(sys, 'frozen', False):
    sys.path.insert(0, os.path.dirname(sys.executable))
else:
    # Add project root to path so 'launcher' package can be imported
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from launcher.app import CatLauncherApp

if __name__ == "__main__":
    app = CatLauncherApp()
    app.run()
