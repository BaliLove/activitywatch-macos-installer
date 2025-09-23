# 🍎 ActivityWatch Team Edition - macOS Installer

## 📦 What This Is

A **native macOS application** that installs ActivityWatch + team sync for Mac users. No Python installation required!

## 🎯 For Mac Team Members

**All they need:**
1. Download: `ActivityWatch-Team-Installer.dmg` or `ActivityWatch-Team-Installer.app`
2. Double-click to run (or drag from DMG to Applications)
3. Enter work email
4. Wait 2-3 minutes
5. Done!

**What it installs:**
- ✅ ActivityWatch time tracking (native Mac app)
- ✅ Automatic sync to company database
- ✅ Applications folder integration
- ✅ Privacy controls
- ✅ Launch Agent for auto-start

## 🛠️ How to Build the Mac Installer

**Prerequisites:**
- macOS (required for building Mac applications)
- Python 3.8+ installed
- Xcode Command Line Tools

**Build Steps:**
```bash
cd ActivityWatch-Mac-Installer
chmod +x build_mac.sh
./build_mac.sh
```

**Output:**
- `ActivityWatch-Team-Installer.app` (native Mac app)
- `ActivityWatch-Team-Installer.dmg` (professional installer)

## 📋 macOS-Specific Features

### **Native Integration:**
- **Applications Folder**: Installs to ~/Applications/ActivityWatch.app
- **Launch Agent**: Auto-starts via macOS LaunchAgents
- **System Preferences**: Proper macOS app behavior
- **SF Pro Font**: Uses system fonts for native look

### **macOS File Locations:**
- **App**: `~/Applications/ActivityWatch.app`
- **Config**: `~/Library/Application Support/ActivityWatch-Team/`
- **Launch Agent**: `~/Library/LaunchAgents/com.activitywatch.team.plist`

### **Privacy & Security:**
- ✅ **No hardcoded credentials**
- ✅ **Keychain integration** (future enhancement)
- ✅ **System permission requests** handled properly
- ✅ **App Notarization ready** (with Apple Developer account)

## 📊 macOS-Specific Tracking

**Included:**
- Application usage time (all Mac apps)
- Window titles (encrypted if sensitive)
- Browser activity (Safari, Chrome, Firefox)
- Focus time and productivity patterns

**macOS Excluded Apps:**
- Keychain Access
- 1Password
- Banking apps
- System Preferences (sensitive areas)

## 🔒 macOS Security

### **System Integration:**
- Uses macOS LaunchAgents (not cron jobs)
- Proper application bundle structure
- Follows Apple's app guidelines
- Ready for code signing & notarization

### **Permissions:**
- **Accessibility**: For window title tracking
- **Screen Recording**: If needed for advanced features
- **Network**: For sync to company server

## 🚀 Distribution Options

### **Option 1: DMG File (Recommended)**
```bash
# Professional installer experience
ActivityWatch-Team-Installer.dmg
```
- Drag & drop installation
- Professional appearance
- Standard Mac experience

### **Option 2: App Bundle**
```bash
# Direct executable
ActivityWatch-Team-Installer.app
```
- Double-click to run
- Easier for email distribution
- No mounting required

## 🔄 Installation Process

1. **Download Detection**: Automatically downloads ActivityWatch DMG
2. **DMG Mounting**: Mounts the disk image
3. **App Copying**: Copies to Applications folder
4. **Config Creation**: Sets up team sync configuration
5. **Launch Agent**: Creates auto-start service
6. **Testing**: Verifies installation works

## 🆘 macOS Troubleshooting

**Common Issues:**

1. **"App can't be opened" (Gatekeeper)**
   - Right-click → "Open" → "Open anyway"
   - Or disable Gatekeeper temporarily

2. **Permission denied errors**
   - Grant Accessibility permissions in System Preferences
   - Run installer with admin privileges if needed

3. **ActivityWatch won't start**
   - Check Applications folder installation
   - Verify launch agent is loaded: `launchctl list | grep activitywatch`

## 📱 Team Rollout for Mac

### **Email Template:**
```
Subject: ActivityWatch Setup for Mac Users

Hi Mac users!

Please install our team time tracking:

1. Download: ActivityWatch-Team-Installer.dmg
2. Double-click and drag to Applications
3. Run installer and enter your @company.com email
4. Done!

Dashboard: http://localhost:5600

Questions? Reply to this email.
```

## 🔄 Updates & Maintenance

**To update the installer:**
1. Modify `activitywatch_installer_mac.py`
2. Run `./build_mac.sh`
3. Distribute new DMG/app

**To update team members:**
- Send new installer (auto-replaces old installation)
- No uninstall needed

## 🎉 Result for Mac Teams

**Your Mac users get:**
- Native macOS application experience
- One-click installation (familiar to Mac users)
- Proper system integration
- Professional installer appearance

**You get:**
- Easy Mac distribution
- Native macOS compatibility
- Proper system service integration
- Enterprise-ready deployment

**Perfect for Mac-focused teams!** 🍎