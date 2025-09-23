#!/usr/bin/env python3
"""
macOS Build Script Template
Based on working Windows build process from ActivityWatch-Standalone-EXE

This is a template for building the macOS installer using the same structure
as the successful Windows installer.
"""

import os
import subprocess
import shutil
from pathlib import Path

def clean_build():
    """Clean previous build artifacts"""
    print("🧹 Cleaning previous builds...")

    dirs_to_clean = ['build', 'dist', '__pycache__']
    for dir_name in dirs_to_clean:
        if os.path.exists(dir_name):
            shutil.rmtree(dir_name)
            print(f"   Removed {dir_name}/")

    files_to_clean = ['*.spec']
    for pattern in files_to_clean:
        for file_path in Path('.').glob(pattern):
            if 'template' not in str(file_path):  # Keep template files
                file_path.unlink()
                print(f"   Removed {file_path}")

def build_installer():
    """Build the macOS installer using PyInstaller"""
    print("🔨 Building macOS installer...")

    # PyInstaller command (equivalent to Windows version)
    cmd = [
        'python', '-m', 'PyInstaller',
        '--onedir',                    # Create directory bundle
        '--windowed',                  # No console window
        '--name=ActivityWatch-Team-Installer',
        'activitywatch_installer_mac.py'  # Main installer script
    ]

    try:
        result = subprocess.run(cmd, check=True, capture_output=True, text=True)
        print("✅ PyInstaller build successful")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ PyInstaller build failed: {e}")
        print(f"   stdout: {e.stdout}")
        print(f"   stderr: {e.stderr}")
        return False

def create_dmg():
    """Create DMG installer for distribution"""
    print("📦 Creating DMG installer...")

    app_path = "dist/ActivityWatch-Team-Installer.app"
    dmg_path = "ActivityWatch-Team-Installer.dmg"

    if not os.path.exists(app_path):
        print(f"❌ App bundle not found: {app_path}")
        return False

    # Remove existing DMG
    if os.path.exists(dmg_path):
        os.remove(dmg_path)

    # Create DMG
    cmd = [
        'hdiutil', 'create',
        '-volname', 'ActivityWatch Team Installer',
        '-srcfolder', app_path,
        '-ov', '-format', 'UDZO',
        dmg_path
    ]

    try:
        subprocess.run(cmd, check=True)
        print(f"✅ DMG created: {dmg_path}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ DMG creation failed: {e}")
        return False

def verify_build():
    """Verify the build was successful"""
    print("🔍 Verifying build...")

    app_path = "dist/ActivityWatch-Team-Installer.app"
    dmg_path = "ActivityWatch-Team-Installer.dmg"

    checks = []

    # Check app bundle exists
    if os.path.exists(app_path):
        size_mb = get_folder_size(app_path) / (1024 * 1024)
        checks.append(f"✅ App bundle exists ({size_mb:.1f}MB)")
    else:
        checks.append("❌ App bundle missing")

    # Check DMG exists
    if os.path.exists(dmg_path):
        size_mb = os.path.getsize(dmg_path) / (1024 * 1024)
        checks.append(f"✅ DMG exists ({size_mb:.1f}MB)")
    else:
        checks.append("❌ DMG missing")

    # Check executable exists
    exe_path = f"{app_path}/Contents/MacOS/ActivityWatch-Team-Installer"
    if os.path.exists(exe_path):
        checks.append("✅ Executable exists")
    else:
        checks.append("❌ Executable missing")

    print("\n".join(checks))
    return all("✅" in check for check in checks)

def get_folder_size(folder_path):
    """Get total size of folder in bytes"""
    total_size = 0
    for dirpath, dirnames, filenames in os.walk(folder_path):
        for filename in filenames:
            file_path = os.path.join(dirpath, filename)
            if os.path.exists(file_path):
                total_size += os.path.getsize(file_path)
    return total_size

def main():
    """Main build process"""
    print("🚀 ActivityWatch macOS Installer Build")
    print("=" * 50)

    # Step 1: Clean
    clean_build()

    # Step 2: Build
    if not build_installer():
        print("❌ Build failed - stopping")
        return False

    # Step 3: Create DMG
    if not create_dmg():
        print("⚠️  DMG creation failed - app bundle still available")

    # Step 4: Verify
    success = verify_build()

    print("\n" + "=" * 50)
    if success:
        print("🎉 Build completed successfully!")
        print("\nDistribution files:")
        print("   📱 App Bundle: dist/ActivityWatch-Team-Installer.app")
        print("   💿 DMG Installer: ActivityWatch-Team-Installer.dmg")
        print("\nNext steps:")
        print("   1. Test the app bundle on a clean macOS system")
        print("   2. Verify sync functionality with production server")
        print("   3. Test DMG installation process")
    else:
        print("❌ Build completed with errors")
        print("   Check the error messages above")

    return success

if __name__ == "__main__":
    main()