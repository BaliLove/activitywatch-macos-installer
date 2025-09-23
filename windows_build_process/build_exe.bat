@echo off
echo ================================================
echo Building ActivityWatch Team Edition Standalone
echo ================================================

echo Installing required packages...
pip install -r requirements.txt

echo Building standalone executable...
pyinstaller --onefile --windowed --icon=icon.ico --name="ActivityWatch-Team-Installer" activitywatch_installer.py

echo Copying executable to output...
copy dist\ActivityWatch-Team-Installer.exe .\ActivityWatch-Team-Installer.exe

echo ================================================
echo Build complete!
echo ================================================
echo.
echo Your team members need only:
echo 1. ActivityWatch-Team-Installer.exe (single file)
echo 2. Double-click to install
echo 3. Enter work email
echo 4. Done!
echo.
echo No Python installation required!
echo File size: ~10-15MB
echo.
pause