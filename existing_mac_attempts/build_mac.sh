#!/bin/bash

echo "================================================"
echo "Building ActivityWatch Team Edition for macOS"
echo "================================================"

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    echo "Error: This script must be run on macOS to build the Mac installer"
    echo "Please run this on a Mac computer"
    exit 1
fi

# Check Python version
python3 --version
if [ $? -ne 0 ]; then
    echo "Error: Python 3 is required but not found"
    echo "Please install Python 3 from https://python.org"
    exit 1
fi

echo "Installing required packages..."
pip3 install -r requirements.txt

if [ $? -ne 0 ]; then
    echo "Error: Failed to install requirements"
    exit 1
fi

echo "Building standalone application..."
pyinstaller --onefile \
    --windowed \
    --name="ActivityWatch-Team-Installer" \
    --icon=icon.icns \
    --osx-bundle-identifier=com.activitywatch.team.installer \
    activitywatch_installer_mac.py

if [ $? -ne 0 ]; then
    echo "Error: Failed to build application"
    exit 1
fi

echo "Creating disk image..."
# Create a temporary directory for the DMG
mkdir -p dmg-temp
cp dist/ActivityWatch-Team-Installer.app dmg-temp/
cp README.md dmg-temp/ 2>/dev/null || echo "No README found, skipping"

# Create the DMG
hdiutil create -volname "ActivityWatch Team Installer" \
    -srcfolder dmg-temp \
    -ov -format UDZO \
    ActivityWatch-Team-Installer.dmg

if [ $? -eq 0 ]; then
    echo "Copying app to current directory..."
    cp -r dist/ActivityWatch-Team-Installer.app ./

    echo "Cleaning up..."
    rm -rf dmg-temp

    echo "================================================"
    echo "Build complete!"
    echo "================================================"
    echo ""
    echo "Your team members need:"
    echo "1. ActivityWatch-Team-Installer.dmg (drag & drop installer)"
    echo "   OR"
    echo "2. ActivityWatch-Team-Installer.app (double-click to run)"
    echo ""
    echo "Distribution options:"
    echo "• DMG file: Professional installer experience"
    echo "• App bundle: Direct executable (easier for email)"
    echo ""
    echo "File sizes:"
    echo "• DMG: $(du -h ActivityWatch-Team-Installer.dmg | cut -f1)"
    echo "• App: $(du -sh ActivityWatch-Team-Installer.app | cut -f1)"
    echo ""
    echo "No Python installation required on target Macs!"
    echo ""
else
    echo "Error: Failed to create DMG"
    echo "App bundle is still available: ActivityWatch-Team-Installer.app"
fi

echo "Testing the application..."
echo "You can test by double-clicking ActivityWatch-Team-Installer.app"