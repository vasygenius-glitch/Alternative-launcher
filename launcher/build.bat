@echo off
echo Building Cat Launcher...
pip install -r requirements.txt
pyinstaller --noconfirm --onedir --windowed --add-data "background.png;." --name "CatLauncher" launcher.py
echo Build complete! Check the 'dist' folder.
pause
