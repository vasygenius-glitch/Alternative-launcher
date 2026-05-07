@echo off
echo Building Cat Launcher V2...

pip install -r requirements.txt

:: Clean old build
if exist "dist" rmdir /s /q "dist"
if exist "build" rmdir /s /q "build"

:: Run PyInstaller with proper CustomTkinter hook and hidden imports
pyinstaller --noconfirm ^
    --onedir ^
    --windowed ^
    --name "CatLauncherV2" ^
    --hidden-import "customtkinter" ^
    --hidden-import "PIL" ^
    --hidden-import "minecraft_launcher_lib" ^
    --hidden-import "requests" ^
    --hidden-import "pypresence" ^
    --add-data "launcher/assets;launcher/assets" ^
    launcher/launcher.py

echo Build complete! Check the 'dist' folder.
pause
