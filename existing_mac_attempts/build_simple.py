#!/usr/bin/env python3
"""
Simple Python-based builder for macOS
Avoids shell script permission issues
"""

import subprocess
import sys
import os
import platform
from pathlib import Path

def run_command(cmd, description=""):
    """Run a command and handle errors"""
    print(f"🔧 {description}...")
    try:
        result = subprocess.run(cmd, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} - Success")
        return result.stdout
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} - Failed")
        print(f"Error: {e.stderr}")
        return None

def main():
    """Main build process"""
    print("🍎 ActivityWatch Mac Installer Builder")
    print("=" * 50)

    # Check if on macOS
    if platform.system() != "Darwin":
        print("❌ This must be run on macOS")
        sys.exit(1)

    # Check Python version
    print(f"✅ Python version: {sys.version}")

    # Install requirements
    if not run_command("pip3 install requests pyinstaller", "Installing requirements"):
        print("❌ Failed to install requirements")
        sys.exit(1)

    # Clean any previous builds
    run_command("rm -rf dist build *.spec", "Cleaning previous builds")

    # Build the application (use --onedir for macOS .app bundles)
    build_cmd = """pyinstaller --onedir --windowed --name="ActivityWatch-Team-Installer" activitywatch_installer_mac.py"""

    if not run_command(build_cmd, "Building Mac application"):
        print("❌ Failed to build application")
        sys.exit(1)

    # Check what was actually created
    print("\n🔍 Checking build output...")

    # First, let's see if dist directory exists
    if not Path("dist").exists():
        print("❌ No dist directory found")
        run_command("ls -la", "Listing current directory")
        return

    # List everything in dist
    dist_contents = run_command("ls -la dist/", "Listing dist directory")
    if dist_contents:
        print("Contents of dist/:")
        print(dist_contents)

    # Find all files recursively in dist
    all_files = run_command("find dist/ -type f", "Finding all files in dist")
    if all_files:
        print("\nAll files created:")
        print(all_files)

    # Look for the .app bundle specifically
    app_path = Path("dist/ActivityWatch-Team-Installer.app")

    if app_path.exists():
        print(f"✅ Application bundle found: {app_path}")

        # Check if it's a proper app bundle
        info_plist = app_path / "Contents" / "Info.plist"
        if info_plist.exists():
            print("✅ Valid Mac app bundle structure")
        else:
            print("⚠️  App bundle may be incomplete")

        # Copy to current directory
        run_command("cp -r dist/ActivityWatch-Team-Installer.app ./", "Copying app to current directory")

        # Get file size
        size_output = run_command("du -sh ActivityWatch-Team-Installer.app", "Getting app size")
        if size_output:
            print(f"📦 App size: {size_output.strip()}")

        # Test if it's executable
        executable = app_path / "Contents" / "MacOS" / "ActivityWatch-Team-Installer"
        if executable.exists():
            print("✅ Executable found inside app bundle")
        else:
            print("⚠️  No executable found in app bundle")

    else:
        print("❌ No .app bundle found")
        print("🔍 Looking for any executable files...")
        run_command("find dist/ -type f -perm +111", "Finding executable files")

        # Look for the executable without .app extension
        exe_path = Path("dist/ActivityWatch-Team-Installer")
        if exe_path.exists():
            print(f"✅ Standalone executable found: {exe_path}")
            run_command("cp dist/ActivityWatch-Team-Installer ./ActivityWatch-Team-Installer-mac", "Copying executable")
            run_command("chmod +x ActivityWatch-Team-Installer-mac", "Making executable")
        else:
            print("❌ No recognizable output found")
            return

    # Try to create DMG (optional)
    print("\n🔧 Creating DMG installer...")
    dmg_commands = [
        "mkdir -p dmg-temp",
        "cp -r dist/ActivityWatch-Team-Installer.app dmg-temp/",
        "hdiutil create -volname 'ActivityWatch Team Installer' -srcfolder dmg-temp -ov -format UDZO ActivityWatch-Team-Installer.dmg",
        "rm -rf dmg-temp"
    ]

    dmg_success = True
    for cmd in dmg_commands:
        if not run_command(cmd, f"DMG step: {cmd.split()[0]}"):
            dmg_success = False
            break

    if dmg_success:
        dmg_size = run_command("du -sh ActivityWatch-Team-Installer.dmg", "Getting DMG size")
        if dmg_size:
            print(f"📦 DMG size: {dmg_size.strip()}")

    print("\n🎉 Build Complete!")
    print("=" * 50)
    print("Files created:")

    if Path("ActivityWatch-Team-Installer.app").exists():
        print("✅ ActivityWatch-Team-Installer.app")

    if Path("ActivityWatch-Team-Installer.dmg").exists():
        print("✅ ActivityWatch-Team-Installer.dmg")

    print("\nDistribution options:")
    print("• Send .app file directly (easier)")
    print("• Send .dmg file (more professional)")
    print("\nBoth work without Python installation on target Macs!")

if __name__ == "__main__":
    main()