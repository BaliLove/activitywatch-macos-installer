# 🍎 macOS Installer - Troubleshooting Guide

## Quick Solutions Summary

### ✅ Working Solution (Recommended)
```bash
cd ActivityWatch-Mac-Installer
python3 activitywatch_installer_terminal.py
```
**Status**: Fully working terminal installer with no dependencies

### ⚠️ GUI Issues (Need tkinter fix)
- **Problem**: Blank window when running GUI installer
- **Solution**: `brew install python-tk` then retry

---

## Detailed Issue Analysis

### Issue 1: GUI Installer Shows Blank Window

**Symptoms:**
- App launches and shows window title
- Window content is completely blank
- No buttons or text visible

**Root Cause:**
```
Missing dependency: No module named '_tkinter'
```

**Solutions (Pick one):**

#### Solution A: Use Terminal Installer (Easiest)
```bash
python3 activitywatch_installer_terminal.py
```
- ✅ Works immediately
- ✅ No additional dependencies
- ✅ Same functionality as GUI version

#### Solution B: Fix tkinter for GUI
```bash
# Option 1: Homebrew
brew install python-tk

# Option 2: Use system Python
/usr/bin/python3 run_installer_mac.py

# Option 3: Pyenv with framework
pyenv install 3.11.10 --enable-framework
```

### Issue 2: Shell Script Permission Errors

**Symptoms:**
```
zsh: operation not permitted: ./build_mac.sh
```

**Solutions:**
```bash
# Remove quarantine flags
xattr -r -d com.apple.quarantine .

# Fix permissions
chmod +x build_mac.sh

# Alternative: Use Python builder
python3 build_simple.py
```

### Issue 3: PyInstaller Build Issues

**Symptoms:**
- Build succeeds but app doesn't work
- "Onefile mode deprecated" warnings

**Solutions:**
```bash
# Use correct flags for macOS
pyinstaller --onedir --windowed --name="ActivityWatch-Team-Installer" activitywatch_installer_mac.py

# Clean build
rm -rf dist build *.spec
python3 build_simple.py
```

---

## File Status and Locations

### ✅ Working Files
- `activitywatch_installer_terminal.py` - Terminal installer (works on all Macs)
- `build_simple.py` - Python-based builder (avoids shell permission issues)
- `run_installer_mac.py` - Direct Python runner (needs tkinter fix)

### ⚠️ Problematic Files
- `activitywatch_installer_mac.py` - GUI version (needs tkinter)
- `build_mac.sh` - Shell script (permission issues on some systems)

### 📁 Expected Outputs
- `ActivityWatch-Team-Installer.app` - Native Mac app (24.6 MB when built)
- `ActivityWatch-Team-Installer.dmg` - Professional installer package

---

## Development Workflow

### For Future macOS Installer Work:

1. **Test Terminal Version First**
   ```bash
   python3 activitywatch_installer_terminal.py
   ```

2. **Fix tkinter if GUI Needed**
   ```bash
   brew install python-tk
   python3 run_installer_mac.py
   ```

3. **Build Native App (Optional)**
   ```bash
   python3 build_simple.py
   ```

4. **Create DMG for Distribution**
   ```bash
   mkdir dmg-temp
   cp -r ActivityWatch-Team-Installer.app dmg-temp/
   hdiutil create -volname "ActivityWatch Team Installer" -srcfolder dmg-temp -ov -format UDZO ActivityWatch-Team-Installer.dmg
   rm -rf dmg-temp
   ```

---

## Technical Root Causes

### tkinter Issue
- **Problem**: Many Python installations on macOS don't include tkinter
- **Scope**: Affects GUI applications only
- **Impact**: GUI installer shows blank window
- **Workaround**: Use terminal installer (no GUI dependencies)

### PyInstaller Compatibility
- **Problem**: `--onefile` + `--windowed` deprecated on macOS
- **Solution**: Use `--onedir` for app bundles
- **Status**: Fixed in current build scripts

### Font Availability
- **Problem**: "SF Pro Display" not available in bundled apps
- **Solution**: Use "Arial" (fixed in current code)

---

## Next Steps for Claude

When continuing work on macOS installer:

1. **Priority 1**: Focus on terminal installer (it works perfectly)
2. **Priority 2**: Fix tkinter dependency for GUI version
3. **Priority 3**: Optimize PyInstaller build process

### Commands to Remember:
```bash
# Test working solution
python3 activitywatch_installer_terminal.py

# Fix GUI dependencies
brew install python-tk

# Build with correct flags
python3 build_simple.py
```

### Key Files:
- `activitywatch_installer_terminal.py` ← **Primary working solution**
- `build_simple.py` ← **Reliable builder**
- `BUILDING_INSTRUCTIONS.md` ← **Updated with all solutions**