#!/bin/bash
# ActivityWatch macOS Build Script
# Creates .app bundle and .dmg installer

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Configuration
APP_NAME="ActivityWatch Team Installer"
BUNDLE_ID="watch.activity.team.installer"
VERSION="1.0.0"
ARCH=$(uname -m)

# Paths
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
BUILD_DIR="${SCRIPT_DIR}/build"
DIST_DIR="${SCRIPT_DIR}/dist"
APP_DIR="${DIST_DIR}/${APP_NAME}.app"
DMG_NAME="ActivityWatch-Team-Installer-macOS-${ARCH}.dmg"

echo -e "${BLUE}🍎 ActivityWatch macOS Builder${NC}"
echo -e "${BLUE}================================${NC}"
echo

# Function to print status
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARN]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check if we're on macOS
if [[ "$OSTYPE" != "darwin"* ]]; then
    print_error "This script must be run on macOS"
    exit 1
fi

# Check requirements
print_status "Checking requirements..."

# Check Python
if ! command -v python3 &> /dev/null; then
    print_error "Python 3 is required"
    exit 1
fi

python_version=$(python3 -c "import sys; print(f'{sys.version_info.major}.{sys.version_info.minor}')")
print_status "Found Python ${python_version}"

# Check if PyInstaller is available
if ! python3 -c "import PyInstaller" 2>/dev/null; then
    print_status "Installing PyInstaller..."
    python3 -m pip install --user PyInstaller
fi

# Check for required tools
for tool in hdiutil codesign; do
    if ! command -v $tool &> /dev/null; then
        print_error "$tool is required but not found"
        exit 1
    fi
done

# Clean previous builds
print_status "Cleaning previous builds..."
rm -rf "${BUILD_DIR}"
rm -rf "${DIST_DIR}"
mkdir -p "${BUILD_DIR}"
mkdir -p "${DIST_DIR}"

# Create requirements.txt for bundling
print_status "Creating requirements file..."
cat > "${SCRIPT_DIR}/requirements.txt" << EOF
requests>=2.31.0
certifi>=2023.7.22
PyInstaller>=6.0.0
EOF

# Install requirements
print_status "Installing requirements..."
python3 -m pip install --user -r "${SCRIPT_DIR}/requirements.txt"

# Create app icon (if we have one)
ICON_PATH="${SCRIPT_DIR}/app_icon.icns"
if [[ ! -f "$ICON_PATH" ]]; then
    print_warning "No app icon found, creating placeholder..."
    # Create a simple icon using system tools
    mkdir -p "${BUILD_DIR}/icon.iconset"
    # Use system icon as base (ActivityWatch-like)
    sips -z 16 16 /System/Library/CoreServices/CoreTypes.bundle/Contents/Resources/Clock.icns --out "${BUILD_DIR}/icon.iconset/icon_16x16.png" 2>/dev/null || true
    sips -z 32 32 /System/Library/CoreServices/CoreTypes.bundle/Contents/Resources/Clock.icns --out "${BUILD_DIR}/icon.iconset/icon_32x32.png" 2>/dev/null || true
    sips -z 128 128 /System/Library/CoreServices/CoreTypes.bundle/Contents/Resources/Clock.icns --out "${BUILD_DIR}/icon.iconset/icon_128x128.png" 2>/dev/null || true
    sips -z 256 256 /System/Library/CoreServices/CoreTypes.bundle/Contents/Resources/Clock.icns --out "${BUILD_DIR}/icon.iconset/icon_256x256.png" 2>/dev/null || true
    sips -z 512 512 /System/Library/CoreServices/CoreTypes.bundle/Contents/Resources/Clock.icns --out "${BUILD_DIR}/icon.iconset/icon_512x512.png" 2>/dev/null || true
    iconutil -c icns "${BUILD_DIR}/icon.iconset" -o "$ICON_PATH" 2>/dev/null || true
fi

# Build with PyInstaller
print_status "Building application with PyInstaller..."

# Create PyInstaller spec file
cat > "${BUILD_DIR}/installer.spec" << EOF
# -*- mode: python ; coding: utf-8 -*-
import sys
from pathlib import Path

a = Analysis(
    ['${SCRIPT_DIR}/activitywatch_installer_macos_enhanced.py'],
    pathex=['${SCRIPT_DIR}'],
    binaries=[],
    datas=[],
    hiddenimports=[
        'tkinter',
        'tkinter.ttk',
        'tkinter.messagebox',
        'requests',
        'certifi',
        'plistlib',
        'ssl',
        'urllib.request'
    ],
    hookspath=[],
    hooksconfig={},
    runtime_hooks=[],
    excludes=[],
    noarchive=False,
)

pyz = PYZ(a.pure, a.zipped_data, cipher=None)

exe = EXE(
    pyz,
    a.scripts,
    [],
    exclude_binaries=True,
    name='${APP_NAME}',
    debug=False,
    bootloader_ignore_signals=False,
    strip=False,
    upx=True,
    console=False,
    disable_windowed_traceback=False,
    argv_emulation=False,
    target_arch=None,
    codesign_identity=None,
    entitlements_file=None,
)

coll = COLLECT(
    exe,
    a.binaries,
    a.zipfiles,
    a.datas,
    strip=False,
    upx=True,
    upx_exclude=[],
    name='${APP_NAME}',
)

app = BUNDLE(
    coll,
    name='${APP_NAME}.app',
    icon='${ICON_PATH}',
    bundle_identifier='${BUNDLE_ID}',
    version='${VERSION}',
    info_plist={
        'CFBundleName': '${APP_NAME}',
        'CFBundleDisplayName': '${APP_NAME}',
        'CFBundleVersion': '${VERSION}',
        'CFBundleShortVersionString': '${VERSION}',
        'CFBundleIdentifier': '${BUNDLE_ID}',
        'CFBundleExecutable': '${APP_NAME}',
        'CFBundlePackageType': 'APPL',
        'CFBundleSignature': 'AWTI',
        'NSHighResolutionCapable': True,
        'NSHumanReadableCopyright': 'Copyright © 2025 Bali Love',
        'LSMinimumSystemVersion': '12.0',
        'NSRequiresAquaSystemAppearance': False,
        'LSApplicationCategoryType': 'public.app-category.productivity',
        'NSAppleEventsUsageDescription': 'ActivityWatch needs access to system events for time tracking.',
        'NSSystemAdministrationUsageDescription': 'ActivityWatch may need admin access to install system services.',
    }
)
EOF

# Run PyInstaller
cd "${BUILD_DIR}"
python3 -m PyInstaller installer.spec --clean --noconfirm

# Move the app to dist directory
if [[ -d "${BUILD_DIR}/dist/${APP_NAME}.app" ]]; then
    mv "${BUILD_DIR}/dist/${APP_NAME}.app" "${APP_DIR}"
    print_status "App bundle created successfully"
else
    print_error "Failed to create app bundle"
    exit 1
fi

# Set proper permissions
print_status "Setting permissions..."
chmod -R 755 "${APP_DIR}"
chmod +x "${APP_DIR}/Contents/MacOS/${APP_NAME}"

# Optional: Code signing (if certificates are available)
if security find-identity -v -p codesigning | grep -q "Developer ID Application"; then
    print_status "Code signing available, signing app..."
    
    # Get the first available Developer ID
    DEVELOPER_ID=$(security find-identity -v -p codesigning | grep "Developer ID Application" | head -1 | sed -n 's/.*"\(.*\)".*/\1/p')
    
    if [[ -n "$DEVELOPER_ID" ]]; then
        print_status "Signing with: $DEVELOPER_ID"
        codesign --deep --force --verify --verbose --sign "$DEVELOPER_ID" \
                 --options runtime \
                 --entitlements "${SCRIPT_DIR}/entitlements.plist" \
                 "${APP_DIR}" 2>/dev/null || {
            print_warning "Code signing failed, continuing with unsigned app..."
        }
    fi
else
    print_warning "No Developer ID found, app will be unsigned"
    print_warning "Users may see security warnings when running the app"
fi

# Create DMG installer
print_status "Creating DMG installer..."

# Create temporary DMG directory
DMG_TEMP_DIR="${BUILD_DIR}/dmg_temp"
mkdir -p "${DMG_TEMP_DIR}"

# Copy app to temp directory
cp -R "${APP_DIR}" "${DMG_TEMP_DIR}/"

# Create Applications symlink
ln -s /Applications "${DMG_TEMP_DIR}/Applications"

# Create background and styling (optional)
DMG_BACKGROUND="${SCRIPT_DIR}/dmg_background.png"
if [[ -f "$DMG_BACKGROUND" ]]; then
    mkdir -p "${DMG_TEMP_DIR}/.background"
    cp "$DMG_BACKGROUND" "${DMG_TEMP_DIR}/.background/background.png"
fi

# Create DS_Store for nice DMG layout (if available)
DS_STORE_FILE="${SCRIPT_DIR}/DS_Store_template"
if [[ -f "$DS_STORE_FILE" ]]; then
    cp "$DS_STORE_FILE" "${DMG_TEMP_DIR}/.DS_Store"
fi

# Calculate size needed for DMG
DMG_SIZE=$(du -sm "${DMG_TEMP_DIR}" | cut -f1)
DMG_SIZE=$((DMG_SIZE + 50))  # Add 50MB buffer

print_status "Creating DMG (${DMG_SIZE}MB)..."

# Create writable DMG
hdiutil create \
    -srcfolder "${DMG_TEMP_DIR}" \
    -volname "${APP_NAME}" \
    -fs HFS+ \
    -fsargs "-c c=64,a=16,e=16" \
    -format UDRW \
    -size "${DMG_SIZE}m" \
    "${BUILD_DIR}/temp.dmg"

# Mount the DMG
MOUNT_POINT=$(hdiutil attach "${BUILD_DIR}/temp.dmg" -readwrite -noverify -noautoopen | grep -E '^/dev/' | sed 1q | awk '{print $3}')

if [[ -z "$MOUNT_POINT" ]]; then
    print_error "Failed to mount temp DMG"
    exit 1
fi

print_status "DMG mounted at: $MOUNT_POINT"

# Set DMG window properties (if AppleScript is available)
if command -v osascript &> /dev/null; then
    print_status "Configuring DMG appearance..."
    
    osascript << EOF
    tell application "Finder"
        tell disk "${APP_NAME}"
            open
            set current view of container window to icon view
            set toolbar visible of container window to false
            set statusbar visible of container window to false
            set the bounds of container window to {400, 100, 900, 400}
            set viewOptions to the icon view options of container window
            set arrangement of viewOptions to not arranged
            set icon size of viewOptions to 72
            try
                set background picture of viewOptions to file ".background:background.png"
            end try
            set position of item "${APP_NAME}.app" of container window to {150, 200}
            set position of item "Applications" of container window to {350, 200}
            close
            open
            update without registering applications
            delay 2
        end tell
    end tell
EOF
fi

# Unmount the DMG
hdiutil detach "$MOUNT_POINT"

# Convert to compressed, read-only DMG
print_status "Compressing DMG..."
hdiutil convert "${BUILD_DIR}/temp.dmg" \
    -format UDZO \
    -imagekey zlib-level=9 \
    -o "${DIST_DIR}/${DMG_NAME}"

# Clean up
rm -f "${BUILD_DIR}/temp.dmg"
rm -rf "${DMG_TEMP_DIR}"

# Verify the final DMG
if [[ -f "${DIST_DIR}/${DMG_NAME}" ]]; then
    DMG_FILE_SIZE=$(du -h "${DIST_DIR}/${DMG_NAME}" | cut -f1)
    print_status "DMG created successfully: ${DMG_NAME} (${DMG_FILE_SIZE})"
    
    # Optional: Verify DMG integrity
    print_status "Verifying DMG integrity..."
    hdiutil verify "${DIST_DIR}/${DMG_NAME}" && print_status "DMG verification passed" || print_warning "DMG verification failed"
else
    print_error "Failed to create DMG"
    exit 1
fi

# Create entitlements file for future code signing
cat > "${DIST_DIR}/entitlements.plist" << EOF
<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>com.apple.security.automation.apple-events</key>
    <true/>
    <key>com.apple.security.network.client</key>
    <true/>
    <key>com.apple.security.files.user-selected.read-write</key>
    <true/>
</dict>
</plist>
EOF

# Summary
echo
echo -e "${GREEN}✅ Build completed successfully!${NC}"
echo
echo "📦 Generated files:"
echo "   • App Bundle: ${APP_DIR}"
echo "   • DMG Installer: ${DIST_DIR}/${DMG_NAME}"
echo "   • Entitlements: ${DIST_DIR}/entitlements.plist"
echo
echo "📋 Next steps:"
echo "   1. Test the app bundle: open '${APP_DIR}'"
echo "   2. Test the DMG: open '${DIST_DIR}/${DMG_NAME}'"
echo "   3. For distribution, consider code signing and notarization"
echo
echo "🔐 Code signing notes:"
echo "   • Unsigned apps will show security warnings"
echo "   • For distribution, get Apple Developer ID certificates"
echo "   • Use 'codesign' and 'xcrun notarytool' for notarization"
echo

# Optional: Open the dist directory
if [[ "${1:-}" == "--open" ]]; then
    open "${DIST_DIR}"
fi