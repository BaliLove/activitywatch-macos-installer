# Windows Installer Build Process - Reference for macOS

## How the Working Windows .exe is Built

### Build Command
```bash
cd ActivityWatch-Standalone-EXE
python -m PyInstaller --onedir --windowed --name="ActivityWatch-Team-Installer" activitywatch_installer.py
```

### Output Structure
```
dist/ActivityWatch-Team-Installer/
├── ActivityWatch-Team-Installer.exe (3.9MB)
├── _internal/ (all dependencies)
└── [various DLL and support files]
```

### PyInstaller Spec File Analysis
See `ActivityWatch-Team-Installer.spec`:
- **Entry Point**: `activitywatch_installer.py`
- **Mode**: `--windowed` (no console window)
- **Type**: `--onedir` (directory with exe + dependencies)
- **Name**: `ActivityWatch-Team-Installer`

### Dependencies Bundled
The Windows installer includes:
- Python runtime
- tkinter (GUI framework)
- requests (HTTP client)
- json, os, subprocess (standard libraries)
- All ActivityWatch components

## macOS Equivalent Build Process

### Recommended Tools
1. **PyInstaller** (same as Windows)
   ```bash
   pip install pyinstaller
   pyinstaller --onedir --windowed --name="ActivityWatch-Team-Installer" activitywatch_installer_mac.py
   ```

2. **py2app** (macOS native)
   ```bash
   pip install py2app
   python setup.py py2app
   ```

3. **cx_Freeze** (cross-platform)
   ```bash
   pip install cx_freeze
   python setup.py build
   ```

### Target Output Structure
```
ActivityWatch-Team-Installer.app/
├── Contents/
│   ├── Info.plist
│   ├── MacOS/
│   │   └── ActivityWatch-Team-Installer
│   └── Resources/
       └── [dependencies]
```

### DMG Creation (macOS Distribution)
```bash
# Create DMG installer
hdiutil create -volname "ActivityWatch Team Installer" \
  -srcfolder ActivityWatch-Team-Installer.app \
  -ov -format UDZO ActivityWatch-Team-Installer.dmg
```

## Key Files Included

### 1. `ActivityWatch-Team-Installer.spec`
- PyInstaller configuration
- Shows exact build parameters used
- Dependencies and exclusions

### 2. `build_exe.bat`
- Windows build script
- Cleanup and build commands
- Error handling

### 3. `bali_love_categories.json`
- Application categorization rules
- Used by sync client for productivity tracking
- Must be included in macOS build

## Build Requirements

### Windows Requirements (Reference)
- Python 3.13+
- PyInstaller 6.16.0
- tkinter (GUI)
- Windows 10/11

### macOS Requirements (Target)
- Python 3.10+
- PyInstaller or py2app
- tkinter or native macOS GUI framework
- macOS 12+ (Monterey, Ventura, Sonoma)

## Size and Performance

### Windows Results
- **Installer Size**: 3.9MB
- **Installation Time**: ~2 minutes
- **Memory Usage**: ~50MB runtime
- **Dependencies**: All bundled, no external requirements

### macOS Targets
- **App Bundle Size**: 5-10MB (estimated)
- **DMG Size**: 8-15MB (estimated)
- **Installation**: Drag & drop or automated
- **Dependencies**: Self-contained app bundle

## Distribution Method

### Windows
- Single `.exe` file
- Email/download distribution
- Double-click to install

### macOS Options
1. **App Bundle** (`.app` file)
2. **DMG Installer** (recommended)
3. **PKG Installer** (advanced)

## Signing and Notarization (macOS)

For production distribution:
```bash
# Code signing
codesign --deep --force --verify --verbose --sign "Developer ID Application: Your Name" ActivityWatch-Team-Installer.app

# Notarization (Apple requirement)
xcrun notarytool submit ActivityWatch-Team-Installer.dmg --keychain-profile "notarytool-profile" --wait
```

## Testing the Build

### Verification Steps
1. **Size Check**: Reasonable file size (< 20MB)
2. **Dependencies**: No external requirements
3. **Functionality**: All features work after build
4. **Performance**: Similar to Windows version
5. **Distribution**: Easy sharing and installation

### Cross-Reference
Compare your macOS build with:
- Windows installer behavior documented in `../windows_installer_behavior.md`
- Success criteria in `../TESTING_GUIDE.md`
- API compatibility with `../successful_sync_example.json`