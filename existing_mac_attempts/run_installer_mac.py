#!/usr/bin/env python3
"""
Direct Python runner for Mac - No building required!
Just run: python3 run_installer_mac.py
"""

import sys
import platform

def main():
    """Check system and run installer"""

    if platform.system() != "Darwin":
        print("❌ This installer is for macOS only!")
        print("Please run this on a Mac computer.")
        sys.exit(1)

    print("🍎 ActivityWatch Team Edition - Mac Installer")
    print("=" * 50)

    try:
        # Import and run the installer
        from activitywatch_installer_mac import ActivityWatchMacInstaller

        print("✅ Starting installer...")
        app = ActivityWatchMacInstaller()
        app.root.mainloop()

    except ImportError as e:
        print(f"❌ Missing dependency: {e}")
        print("\nTo fix this, run:")
        print("pip3 install requests")
        sys.exit(1)
    except Exception as e:
        print(f"❌ Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main()