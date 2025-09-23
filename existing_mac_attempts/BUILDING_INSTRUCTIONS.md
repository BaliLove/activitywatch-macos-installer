# 🚀 Building ActivityWatch Mac Installer

## Quick Start (5 minutes on any Mac)

### Step 1: Transfer Files to Mac
Copy the entire `ActivityWatch-Mac-Installer` folder to any Mac computer.

### Step 2: Fix macOS Security Issues
```bash
# Navigate to the folder
cd ActivityWatch-Mac-Installer

# Method 1: Try to fix permissions
chmod +x build_mac.sh
chmod 755 build_mac.sh

# Method 2: If still "operation not permitted", run with bash directly
bash build_mac.sh
```

### Step 3: If Still Getting Errors
**Common macOS Security Issues:**

#### A) Quarantine Attributes (Downloaded Files)
```bash
# Remove quarantine flag from all files
xattr -r -d com.apple.quarantine .
chmod +x build_mac.sh
./build_mac.sh
```

#### B) Terminal Permissions
1. Go to **System Preferences** → **Security & Privacy** → **Privacy**
2. Select **"Full Disk Access"** or **"Files and Folders"**
3. Add **Terminal** to the list
4. Restart Terminal and try again

#### C) Alternative: Use Python Builder (Recommended)
```bash
# This avoids shell script permission issues entirely
python3 build_simple.py
```

#### D) Manual Commands (If everything else fails)
```bash
# Install requirements manually
pip3 install requests pyinstaller

# Build manually (instead of using the script)
pyinstaller --onefile --windowed --name="ActivityWatch-Team-Installer" activitywatch_installer_mac.py

# Check the output
ls -la dist/
```

### Step 3: Results
You'll get:
- `ActivityWatch-Team-Installer.app` (native Mac app)
- `ActivityWatch-Team-Installer.dmg` (professional installer)

## What the Build Script Does

1. **Checks macOS environment**
2. **Installs Python dependencies** (`requests`, `pyinstaller`)
3. **Creates standalone app** using PyInstaller
4. **Generates DMG file** with professional appearance
5. **Tests the application**

## File Sizes (Expected)
- App bundle: ~15-20MB
- DMG file: ~10-15MB

## Distribution Ready
Both files will be ready to distribute to your Mac team members immediately after building.

## Alternative: GitHub Actions (Automated)
If you have a GitHub repository, you could set up automated building using GitHub Actions with macOS runners.