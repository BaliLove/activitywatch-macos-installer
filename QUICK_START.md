# ActivityWatch macOS Installer - Quick Start

## Get a Working macOS Installer in 30 Minutes

This guide will get you from Windows to a working macOS installer as quickly as possible.

## ⚡ Immediate Next Steps (Do Now)

### 1. Test the Code on Windows (2 minutes)

```cmd
cd C:\Users\User\apps\activitywatch\activity_watch
python activitywatch_installer_macos_enhanced.py
```

This should show an error about Darwin (macOS) but validate that the Python code is correct.

### 2. Create GitHub Repository (5 minutes)

1. **Create new repo on GitHub:**
   - Go to github.com/new
   - Name: `activitywatch-macos-installer`
   - Public or Private (your choice)
   - Initialize with README

2. **Push your code:**
   ```cmd
   git init
   git add .
   git commit -m "Initial macOS installer with GitHub Actions"
   git remote add origin https://github.com/YOURUSERNAME/activitywatch-macos-installer.git
   git branch -M main
   git push -u origin main
   ```

### 3. Trigger Automated Build (1 minute)

1. **Go to GitHub Actions:**
   - Navigate to your repo → Actions tab
   - Click "Build ActivityWatch macOS Installer"
   - Click "Run workflow" (top right)
   - Leave defaults, click "Run workflow"

2. **Wait for build (10 minutes):**
   - ☕ Get coffee while GitHub builds on macOS
   - Watch progress in real-time

### 4. Download and Test (2 minutes)

1. **Download artifacts:**
   - When build completes, click the run
   - Scroll to "Artifacts" section
   - Download both artifacts

2. **Extract and examine:**
   ```cmd
   # Extract the ZIP files
   # You'll find:
   # - ActivityWatch Team Installer.app (app bundle)
   # - ActivityWatch-Team-Installer-macOS-*.dmg (installer)
   ```

## 🎯 You now have a working macOS installer!

**What you get:**
- ✅ Native macOS app bundle
- ✅ Professional DMG installer  
- ✅ Automatic ActivityWatch installation
- ✅ Team sync configuration
- ✅ Launch Agent for auto-start
- ✅ Privacy controls
- ✅ Comprehensive logging

## 🚀 Next Steps (Optional)

### For Testing Distribution (10 minutes)

1. **Find a Mac user on your team**
2. **Send them the DMG file**  
3. **Have them test the installation:**
   ```bash
   # They just need to:
   open ActivityWatch-Team-Installer-macOS-*.dmg
   # Enter their email
   # Wait 3-5 minutes
   ```

### For Production Release (Setup Apple Developer - 30 minutes)

1. **Get Apple Developer Account** ($99/year)
2. **Add secrets to GitHub repo:**
   - Settings → Secrets and variables → Actions
   - Add the signing certificates (see DEVELOPMENT_GUIDE.md)
3. **Run workflow with signing enabled**
4. **Get notarized, trusted installer**

## 📋 Validation Checklist

After GitHub Actions build completes:

- [ ] Build shows green checkmark
- [ ] App bundle artifact downloaded
- [ ] DMG installer artifact downloaded  
- [ ] Both files extract without errors
- [ ] DMG file is 20-40MB in size
- [ ] App bundle shows proper icon (if available)

## 🐛 If Something Goes Wrong

### Build Fails?
1. Check the Actions log for specific errors
2. Common issues:
   - Python syntax errors → Fix in the code
   - Import errors → Already handled in build script
   - PyInstaller issues → Build script handles this

### Can't Push to GitHub?
```cmd
# Make sure you're authenticated
git config --global user.email "you@example.com"
git config --global user.name "Your Name"

# Or use GitHub Desktop for easier setup
```

### No macOS to Test On?
- That's fine! The build itself validates most functionality
- Ask team members to test
- Use the unsigned installer (users will see security warnings)

## 🔥 Speed Tips

### Fastest Path to Working Installer:
1. **GitHub Actions** (10 minutes) - Automated, no Mac needed
2. **Borrow a Mac** (20 minutes) - If you have access to one
3. **Cloud Mac service** (30 minutes) - Rent by the hour

### Skip for Now (Do Later):
- ❌ Code signing (produces security warnings but still works)
- ❌ Custom app icons (uses default)
- ❌ DMG background images (functional but basic)
- ❌ Comprehensive testing (basic validation is included)

## 🎉 Success Criteria

You'll know it worked when:

1. **GitHub Actions shows green checkmark**
2. **You can download two artifacts**  
3. **DMG file opens on any Mac**
4. **App bundle structure looks correct**
5. **Users can run the installer**

## ⏰ Total Time Investment

- **Minimum**: 20 minutes → Working installer
- **Recommended**: 60 minutes → Tested installer
- **Production**: 2-3 hours → Signed, polished installer

## 💡 Pro Tips

1. **Start with unsigned builds** - they work fine, just show warnings
2. **Use GitHub Actions** - it's free and automatic  
3. **Test early and often** - small iterations are faster
4. **Don't optimize prematurely** - get it working first

## 📞 Need Help?

1. **Check the build logs** in GitHub Actions
2. **Review DEVELOPMENT_GUIDE.md** for detailed troubleshooting  
3. **The installer has comprehensive error logging**
4. **Most issues are covered in the troubleshooting sections**

---

**Ready? Let's build your macOS installer! 🚀**

Copy and paste the commands above and you'll have a working installer in under 30 minutes.