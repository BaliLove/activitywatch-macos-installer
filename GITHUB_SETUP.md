# GitHub Actions Setup with Apple Developer Account

## ✅ Test Results Summary

All tests have been completed successfully on your Windows environment:

### Code Tests
- ✅ **Python syntax validation**: All files compile without errors
- ✅ **Import testing**: All modules import correctly
- ✅ **Email validation**: All test cases pass
- ✅ **System verification**: Correctly detects Windows and fails as expected
- ✅ **Server connectivity**: Your sync server is reachable (status 200)
- ✅ **API structure**: Payload format matches expected structure

### Build System Tests  
- ✅ **Git repository**: Initialized and ready
- ✅ **GitHub Actions workflow**: YAML syntax validated
- ✅ **Build script**: Bash syntax correct
- ✅ **File structure**: All components in place

## 🚀 Next Steps: GitHub Actions + Code Signing

Since you have an Apple Developer account, let's set up the complete signed build system.

### Step 1: Push to GitHub (2 minutes)

```cmd
# If you don't have a remote repository yet:
# 1. Go to github.com/new
# 2. Create repo named "activitywatch-macos-installer"
# 3. Copy the clone URL

# Add remote (replace YOUR_USERNAME):
git remote add origin https://github.com/YOUR_USERNAME/activitywatch-macos-installer.git

# Push everything:
git branch -M main
git push -u origin main
```

### Step 2: Prepare Apple Developer Certificates (5 minutes)

You'll need these from your Apple Developer account:

1. **Developer ID Application Certificate**
   - Go to developer.apple.com → Certificates
   - Create "Developer ID Application" certificate  
   - Download as .p12 file with password

2. **App-Specific Password**
   - Go to appleid.apple.com → Sign-In and Security → App-Specific Passwords
   - Generate password for "ActivityWatch Build"

3. **Team ID**
   - Go to developer.apple.com → Membership
   - Copy your Team ID (10-character string)

### Step 3: Add GitHub Secrets (3 minutes)

Go to your GitHub repo → Settings → Secrets and variables → Actions

Add these secrets:

| Secret Name | Value | Description |
|-------------|-------|-------------|
| `APPLE_CERTIFICATE_P12` | Base64 encoded .p12 file | Your Developer ID cert |
| `P12_PASSWORD` | Your certificate password | Password for .p12 file |
| `KEYCHAIN_PASSWORD` | Any secure password | Temp keychain password |
| `APPLE_ID` | Your Apple ID email | For notarization |
| `APP_PASSWORD` | App-specific password | For notarization |
| `TEAM_ID` | Your 10-char Team ID | For notarization |

#### Converting Certificate to Base64:
```cmd
# On Windows (PowerShell):
[Convert]::ToBase64String([IO.File]::ReadAllBytes("path\to\your\certificate.p12"))

# Or online converter: base64encode.org
```

### Step 4: Trigger Signed Build (1 minute)

1. **Go to Actions tab** in your GitHub repo
2. **Click "Build ActivityWatch macOS Installer"**
3. **Click "Run workflow"**
4. **Enable signing**:
   - ✅ Check "Sign and notarize the app"
   - ✅ Check "Create GitHub Release" (optional)
5. **Click "Run workflow"**

### Step 5: Wait and Download (10 minutes)

The build will:
- ✅ Build on macOS runner
- ✅ Create .app bundle  
- ✅ Generate DMG installer
- ✅ Sign with your Developer ID
- ✅ Submit to Apple for notarization
- ✅ Staple notarization ticket
- ✅ Upload artifacts
- ✅ Create GitHub release (if enabled)

**Result**: Fully trusted, signed macOS installer ready for distribution!

## 🎯 What You'll Get

### Signed Installer Features
- ✅ **No security warnings** when users install
- ✅ **Gatekeeper approved** by Apple
- ✅ **Notarized and trusted** 
- ✅ **Professional distribution** via GitHub Releases
- ✅ **Enterprise ready** for team deployment

### File Outputs
```
Artifacts:
├── ActivityWatch Team Installer.app     # Signed app bundle
├── ActivityWatch-Team-Installer-macOS-[arch].dmg  # Signed DMG
├── BUILD_INFO.txt                       # Build metadata
└── entitlements.plist                   # Signing entitlements

GitHub Release:
├── ActivityWatch-Team-Installer-macOS-[arch].dmg
├── Release notes with installation instructions
└── Automatic versioning and changelog
```

## 🔧 Testing the Signed Installer

### Internal Testing (Mac required)
```bash
# Download from GitHub releases or artifacts
curl -L -o installer.dmg "https://github.com/YOUR_USERNAME/activitywatch-macos-installer/releases/download/v1.0.0/ActivityWatch-Team-Installer-macOS-*.dmg"

# Mount and test
open installer.dmg

# Should open without security warnings!
# Test installation with team email address
```

### Verification Commands
```bash
# Verify code signing
codesign --verify --deep --strict --verbose=2 "ActivityWatch Team Installer.app"

# Verify notarization
spctl --assess --verbose "ActivityWatch Team Installer.app"

# Check DMG signature  
codesign -dv --verbose=4 "ActivityWatch-Team-Installer-macOS-*.dmg"
```

## 🚨 Troubleshooting

### Build Fails?
- **Check secrets**: Ensure all 6 GitHub secrets are set correctly
- **Certificate issues**: Verify .p12 file and password
- **Team ID**: Must be exactly 10 characters
- **App password**: Must be app-specific, not regular password

### Notarization Fails?
- **Bundle ID conflicts**: May need unique bundle ID
- **Entitlements**: Workflow includes correct entitlements
- **Apple ID**: Must be enrolled in Developer Program

### Common Fixes
```yaml
# If bundle ID conflicts, edit build_macos.sh:
BUNDLE_ID="watch.activity.team.installer.yourcompany"

# If notarization timeout, increase wait time in workflow:
--wait --timeout 30m
```

## 🎉 Success Metrics

You'll know everything worked when:

- [ ] **GitHub Actions shows green checkmark**
- [ ] **Artifacts contain signed .app and .dmg**  
- [ ] **DMG opens on Mac without warnings**
- [ ] **Installation completes successfully**
- [ ] **ActivityWatch starts and syncs data**
- [ ] **Team members can install without IT help**

## 📋 Distribution Checklist

### For Your Team
- [ ] **Download signed DMG** from GitHub releases
- [ ] **Test on internal Mac** before team distribution
- [ ] **Create installation guide** (template in PROJECT_SUMMARY.md)
- [ ] **Send DMG file** to Mac team members
- [ ] **Collect feedback** and iterate if needed

### For Production
- [ ] **Tag release** with version number (`git tag v1.0.0`)
- [ ] **Monitor logs** for any installation issues
- [ ] **Set up update mechanism** (future enhancement)
- [ ] **Document rollback** procedure if needed

## 💡 Pro Tips

1. **Start with unsigned build** to test functionality
2. **Use signed build** for actual team distribution  
3. **Monitor Apple Developer** for certificate expiration
4. **Keep secrets secure** - rotate app passwords regularly
5. **Test on clean Macs** before wide deployment

---

**Ready to build your signed macOS installer? Follow steps 1-4 above and you'll have it running in 15 minutes!** 🚀

**Need help with any step? The build logs in GitHub Actions are very detailed and will show exactly what's happening.**