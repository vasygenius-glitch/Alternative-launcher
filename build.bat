@echo off
echo Building Cat Launcher V2...

pip install -r requirements.txt

:: Clean old build
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"

:: Run PyInstaller with proper CustomTkinter hook and hidden imports
pyinstaller --noconfirm ^
    --onefile ^
    --windowed ^
    --name "CatLauncherV2" ^
    --hidden-import "customtkinter" ^
    --hidden-import "PIL" ^
    --hidden-import "minecraft_launcher_lib" ^
    --hidden-import "requests" ^
    --hidden-import "pypresence" ^
    --hidden-import "logging.handlers" ^
    --hidden-import "launcher.app" ^
    --hidden-import "launcher.utils.logger" ^
    --hidden-import "launcher.utils.config" ^
    --hidden-import "launcher.core.auth" ^
    --hidden-import "launcher.core.instance" ^
    --hidden-import "launcher.core.launcher_engine" ^
    --hidden-import "launcher.core.discord_rpc" ^
    --hidden-import "launcher.core.server_status" ^
    --hidden-import "launcher.ui.main_window" ^
    --hidden-import "launcher.ui.tabs.home_tab" ^
    --hidden-import "launcher.ui.tabs.instances_tab" ^
    --hidden-import "launcher.ui.tabs.mods_tab" ^
    --hidden-import "launcher.ui.tabs.accounts_tab" ^
    --hidden-import "launcher.ui.tabs.settings_tab" ^
    --add-data "launcher;launcher" ^
    --add-data "launcher/assets;launcher/assets" ^
    launcher/launcher.py

echo Build complete! Check the 'dist' folder.
pause
