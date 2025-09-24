# ActivityWatch macOS Installer - Development Guide

## Overview

This guide covers developing, building, and distributing a macOS installer for ActivityWatch Team Edition from a Windows environment using cloud-based macOS services.

## Project Structure

```
activity_watch/
├── activitywatch_installer_macos_enhanced.py  # Enhanced macOS installer
├── build_macos.sh                             # Build script for macOS
├── .github/workflows/build-macos.yml          # GitHub Actions CI/CD
├── existing_mac_attempts/                     # Previous attempts (reference)
├── windows_build_process/                     # Windows reference
├── requirements.txt                           # Python dependencies
├── DEVELOPMENT_GUIDE.md                       # This file
└── dist/                                     # Build outputs (created during build)
```

## Development Environment Setup

### On Windows (Your Current Environment)

1. **Clone and prepare the repository:**
   ```cmd
   cd C:\Users\User\apps\activitywatch\activity_watch
   ```

2. **Install development dependencies:**
   ```cmd
   pip install requests certifi PyInstaller
   ```

3. **Test the installer logic:**
   ```cmd
   python activitywatch_installer_macos_enhanced.py --terminal
   ```
   Note: This will fail on Windows but will validate the Python syntax and imports.

### On macOS (Cloud or Local)

1. **Install system dependencies:**
   ```bash
   # macOS comes with Python 3, but ensure it's recent
   python3 --version  # Should be 3.8+
   
   # Install pip dependencies
   pip3 install --user requests certifi PyInstaller
   ```

2. **Make build script executable:**
   ```bash
   chmod +x build_macos.sh
   ```

## Building the Installer

### Method 1: GitHub Actions (Recommended)

1. **Push code to GitHub repository:**
   ```cmd
   git add .
   git commit -m "Add macOS installer and build system"
   git push origin main
   ```

2. **Trigger build manually:**
   - Go to GitHub → Actions tab
   - Click "Build ActivityWatch macOS Installer"
   - Click "Run workflow"
   - Select options (create release, sign & notarize)
   - Click "Run workflow"

3. **Download artifacts:**
   - Wait for build to complete (~10 minutes)
   - Download artifacts from the workflow run
   - Extract and test the DMG file

### Method 2: Local macOS Build

1. **On a Mac (local, cloud, or borrowed):**
   ```bash
   ./build_macos.sh
   ```

2. **Build outputs:**
   ```
   dist/
   ├── ActivityWatch Team Installer.app    # Native macOS app bundle
   ├── ActivityWatch-Team-Installer-macOS-[arch].dmg  # Installer DMG
   ├── entitlements.plist                  # Code signing entitlements
   └── BUILD_INFO.txt                      # Build metadata
   ```

### Method 3: Cloud macOS Services

Popular options for cloud macOS access:
- **GitHub Actions** (free, automated)
- **MacStadium** (paid, on-demand)
- **AWS EC2 Mac instances** (paid, hourly)
- **Scaleway** (paid, affordable)

## Code Signing and Notarization

### Prerequisites

1. **Apple Developer Account** ($99/year)
2. **Developer ID Application Certificate**
3. **App-specific password for notarization**

### GitHub Secrets Setup

Add these secrets to your GitHub repository:

```
APPLE_CERTIFICATE_P12: [base64 encoded .p12 certificate]
P12_PASSWORD: [certificate password]
KEYCHAIN_PASSWORD: [temporary keychain password]
APPLE_ID: [your Apple ID]
APP_PASSWORD: [app-specific password]
TEAM_ID: [your team ID]
```

### Manual Signing Process

```bash
# Sign the app bundle
codesign --deep --force --verify --verbose \
         --sign "Developer ID Application: Your Name" \
         --options runtime \
         --entitlements entitlements.plist \
         "dist/ActivityWatch Team Installer.app"

# Create and sign DMG
./build_macos.sh
codesign --sign "Developer ID Application: Your Name" \
         "dist/ActivityWatch-Team-Installer-macOS-*.dmg"

# Notarize
xcrun notarytool submit "dist/ActivityWatch-Team-Installer-macOS-*.dmg" \
  --apple-id "your@apple.id" \
  --password "app-specific-password" \
  --team-id "TEAMID123" \
  --wait

# Staple
xcrun stapler staple "dist/ActivityWatch-Team-Installer-macOS-*.dmg"
```

## Testing Strategy

### Automated Testing (CI)

The GitHub Actions workflow includes:
- ✅ App bundle structure validation
- ✅ Python syntax and import testing
- ✅ Email validation testing
- ✅ System verification testing
- ✅ Build artifact integrity checks

### Manual Testing

1. **Test on clean macOS systems:**
   - macOS 12 (Monterey)
   - macOS 13 (Ventura)  
   - macOS 14 (Sonoma)

2. **Installation testing:**
   ```bash
   # Mount DMG
   open dist/ActivityWatch-Team-Installer-macOS-*.dmg
   
   # Run installer
   # Test both GUI and terminal modes
   
   # Verify installation
   ls ~/Applications/ActivityWatch.app
   ls ~/Library/LaunchAgents/com.activitywatch.team.plist
   ls ~/Library/Application\ Support/ActivityWatch-Team/
   ```

3. **Functionality testing:**
   ```bash
   # Check if ActivityWatch starts
   open ~/Applications/ActivityWatch.app
   
   # Verify web interface
   open http://localhost:5600
   
   # Check sync logs
   tail -f ~/Library/Application\ Support/ActivityWatch-Team/logs/sync_*.log
   ```

## Development Workflow

### Windows Development → macOS Building

1. **Develop on Windows:**
   - Edit Python code
   - Test logic (where possible)
   - Update documentation
   - Commit changes

2. **Build on macOS (automated):**
   - Push to GitHub
   - GitHub Actions builds automatically
   - Download and test artifacts

3. **Iterate quickly:**
   - Make small changes on Windows
   - Test via GitHub Actions
   - Fast feedback cycle (~10 minutes per iteration)

### Local Development (if you have Mac access)

1. **Standard development cycle:**
   ```bash
   # Edit code
   vim activitywatch_installer_macos_enhanced.py
   
   # Test directly
   python3 activitywatch_installer_macos_enhanced.py --terminal
   
   # Build when ready
   ./build_macos.sh
   
   # Test installer
   open dist/ActivityWatch-Team-Installer-macOS-*.dmg
   ```

## Debugging Common Issues

### Build Failures

1. **PyInstaller import errors:**
   ```bash
   # Check hidden imports in build_macos.sh
   # Add missing modules to hiddenimports list
   ```

2. **Code signing failures:**
   ```bash
   # Check certificate validity
   security find-identity -v -p codesigning
   
   # Verify keychain access
   security unlock-keychain -p password build.keychain
   ```

3. **DMG creation issues:**
   ```bash
   # Check disk space
   df -h
   
   # Verify app bundle structure
   ls -la "dist/ActivityWatch Team Installer.app/Contents/"
   ```

### Runtime Issues

1. **"App can't be opened" warnings:**
   - Expected for unsigned builds
   - Right-click → Open → Open anyway
   - Or use code signing

2. **Permission errors:**
   ```bash
   # Check file permissions
   ls -la ~/Applications/ActivityWatch.app/
   
   # Fix if needed
   chmod +x ~/Applications/ActivityWatch.app/Contents/MacOS/*
   ```

3. **Launch Agent not working:**
   ```bash
   # Check plist file
   cat ~/Library/LaunchAgents/com.activitywatch.team.plist
   
   # Reload if needed
   launchctl unload ~/Library/LaunchAgents/com.activitywatch.team.plist
   launchctl load ~/Library/LaunchAgents/com.activitywatch.team.plist
   ```

## Deployment Strategy

### For Development/Testing

1. **Use GitHub Actions artifacts:**
   - Build automatically on every push
   - Download unsigned DMG for testing
   - Share with team members for testing

### For Production Release

1. **Sign and notarize:**
   - Enable signing in GitHub Actions
   - Or use manual signing process
   - Creates trusted installer

2. **Distribution methods:**
   - **GitHub Releases**: Automatic via workflow
   - **Direct download**: Host DMG file
   - **Internal distribution**: Email/file sharing

## File Size Optimization

### Current sizes (estimated):
- App bundle: ~30-50MB
- DMG installer: ~20-35MB

### Optimization techniques:
1. **Exclude unnecessary files:**
   ```bash
   # Add to PyInstaller excludes
   excludes=['test*', 'unittest*', 'distutils*']
   ```

2. **Compress DMG more aggressively:**
   ```bash
   # In build_macos.sh
   hdiutil convert temp.dmg -format UDZO -imagekey zlib-level=9
   ```

3. **Strip debugging symbols:**
   ```bash
   # In PyInstaller spec
   strip=True
   ```

## Security Considerations

### API Key Management

The installer includes the API key `aw-team-2025-secure-key-v1`. For production:

1. **Rotate keys regularly**
2. **Use environment variables in CI**
3. **Consider server-side key validation**

### Privacy Controls

The installer implements:
- ✅ Window title filtering
- ✅ Sensitive app exclusion
- ✅ Keyword-based filtering
- ✅ Work hours restrictions (optional)

### Audit Logging

All installer and sync activities are logged:
- Installation events
- Sync operations
- Error conditions
- Security events

## Performance Monitoring

### Key metrics to monitor:

1. **Installation success rate**
2. **Sync reliability** 
3. **Resource usage**
4. **Error rates**

### Logging locations:
```
~/Library/Application Support/ActivityWatch-Team/logs/
├── installer_YYYYMMDD_HHMMSS.log  # Installation logs
├── sync_YYYYMMDD.log              # Daily sync logs
├── sync_stdout.log                # Launch Agent stdout
└── sync_stderr.log                # Launch Agent stderr
```

## Support and Troubleshooting

### Common user issues:

1. **Security warnings**: Expected for unsigned builds
2. **Network connectivity**: Required for sync
3. **Permissions**: May need manual approval
4. **ActivityWatch not starting**: Check system requirements

### Support workflow:
1. Check logs in `~/Library/Application Support/ActivityWatch-Team/logs/`
2. Verify system requirements (macOS 12+)
3. Test network connectivity to sync server
4. Check Launch Agent status: `launchctl list | grep activitywatch`

## Next Steps for Production

1. **Get Apple Developer account**
2. **Set up code signing pipeline**
3. **Create proper app icons**
4. **Add update mechanism**
5. **Implement telemetry/analytics**
6. **Create uninstaller**
7. **Add crash reporting**

## Timeline Estimate

From current state to production-ready installer:

- **Week 1**: Setup GitHub Actions, test builds
- **Week 2**: Code signing, basic testing  
- **Week 3**: Comprehensive testing, bug fixes
- **Week 4**: Production release, documentation

Total: ~4 weeks with 1-2 hours/day development time.

## Contact and Support

For development questions or issues:
1. Check existing logs and error messages
2. Review this guide and troubleshooting section
3. Create GitHub issues for bugs
4. Contact team leads for production deployment decisions