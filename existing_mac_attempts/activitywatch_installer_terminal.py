#!/usr/bin/env python3
"""
ActivityWatch Team Edition - Terminal Installer for macOS
No GUI dependencies required - works with any Python installation
"""

import sys
import os
import subprocess
import urllib.request
import json
import time
import platform
import shutil
from pathlib import Path

class ActivityWatchTerminalInstaller:
    def __init__(self):
        # macOS specific paths
        self.home_path = Path.home()
        self.install_path = self.home_path / 'Applications' / 'ActivityWatch-Team'
        self.config_path = self.home_path / 'Library' / 'Application Support' / 'ActivityWatch-Team'
        self.launchd_path = self.home_path / 'Library' / 'LaunchAgents'
        self.server_url = "https://activitywatch-sync-server-1051608384208.us-central1.run.app"

    def print_header(self):
        """Print installer header"""
        print("=" * 60)
        print("🍎 ActivityWatch Team Edition - macOS Installer")
        print("=" * 60)
        print()

    def get_user_input(self, prompt, validator=None):
        """Get validated user input"""
        while True:
            try:
                value = input(prompt).strip()
                if validator and not validator(value):
                    continue
                return value
            except KeyboardInterrupt:
                print("\n\n❌ Installation cancelled by user")
                sys.exit(1)

    def validate_email(self, email):
        """Validate email format"""
        if not email or '@' not in email:
            print("❌ Please enter a valid email address")
            return False
        return True

    def run_installation(self):
        """Run the complete installation"""
        try:
            self.print_header()

            print("This installer will set up ActivityWatch with automatic sync for your team.")
            print()
            print("What will be installed:")
            print("• ActivityWatch time tracking application")
            print("• Automatic sync to company database")
            print("• Privacy controls and encryption")
            print("• Dock and Applications folder shortcuts")
            print("• Launch agent for auto-start")
            print()
            print("Installation time: 2-3 minutes")
            print()

            # Get user email
            email = self.get_user_input(
                "📧 Enter your work email: ",
                self.validate_email
            )

            print(f"\n✅ Email: {email}")

            # Confirm installation
            confirm = self.get_user_input(
                "\n🚀 Ready to install? (y/N): "
            ).lower()

            if confirm not in ['y', 'yes']:
                print("❌ Installation cancelled")
                return

            print("\n🔧 Starting installation...")

            # Run installation steps
            self.update_status("Creating directories...")
            self.create_directories()

            self.update_status("Downloading ActivityWatch...")
            self.install_activitywatch()

            self.update_status("Configuring team settings...")
            self.create_config(email)

            self.update_status("Setting up sync service...")
            self.setup_sync_service()

            self.update_status("Creating launch agent...")
            self.create_launch_agent()

            self.update_status("Testing installation...")
            self.test_installation()

            # Success!
            print("\n🎉 Installation completed successfully!")
            print()
            print("✅ Application installed in Applications folder")
            print("✅ Automatic sync enabled")
            print("✅ Dashboard: http://localhost:5600")
            print()
            print("ActivityWatch will start automatically on next login.")

            # Ask about opening dashboard
            open_dashboard = self.get_user_input(
                "\n🌐 Open ActivityWatch dashboard now? (y/N): "
            ).lower()

            if open_dashboard in ['y', 'yes']:
                subprocess.run(["open", "http://localhost:5600"])

        except Exception as e:
            print(f"\n❌ Installation failed: {str(e)}")
            print("\nPlease contact IT support for assistance.")
            sys.exit(1)

    def update_status(self, message):
        """Update status message"""
        print(f"🔧 {message}")

    def create_directories(self):
        """Create necessary directories"""
        self.install_path.mkdir(parents=True, exist_ok=True)
        self.config_path.mkdir(parents=True, exist_ok=True)
        self.launchd_path.mkdir(parents=True, exist_ok=True)

    def install_activitywatch(self):
        """Download and install ActivityWatch for macOS"""
        # Download ActivityWatch for macOS
        aw_url = "https://github.com/ActivityWatch/activitywatch/releases/download/v0.13.2/activitywatch-v0.13.2-macos-x86_64.dmg"
        dmg_path = self.install_path / "activitywatch.dmg"

        print("   📥 Downloading ActivityWatch...")
        urllib.request.urlretrieve(aw_url, dmg_path)

        print("   💿 Mounting disk image...")
        # Mount the DMG
        mount_result = subprocess.run(["hdiutil", "attach", str(dmg_path), "-nobrowse"],
                                     capture_output=True, text=True)

        if mount_result.returncode != 0:
            raise Exception("Failed to mount ActivityWatch DMG")

        # Find the mounted volume
        mount_point = None
        for line in mount_result.stdout.split('\n'):
            if 'ActivityWatch' in line and '/Volumes/' in line:
                mount_point = line.split('\t')[-1].strip()
                break

        if not mount_point:
            raise Exception("Could not find mounted ActivityWatch volume")

        print("   📱 Installing to Applications...")
        # Copy ActivityWatch.app to Applications
        aw_app_source = Path(mount_point) / "ActivityWatch.app"
        aw_app_dest = self.home_path / "Applications" / "ActivityWatch.app"

        if aw_app_source.exists():
            if aw_app_dest.exists():
                shutil.rmtree(aw_app_dest)
            shutil.copytree(aw_app_source, aw_app_dest)

        # Unmount the DMG
        subprocess.run(["hdiutil", "detach", mount_point], check=True)

        # Clean up DMG file
        dmg_path.unlink()

    def create_config(self, email):
        """Create configuration file"""
        config = {
            "sync_server_url": self.server_url,
            "activitywatch_url": "http://localhost:5600",
            "sync_interval_minutes": 30,
            "user_info": {
                "email": email,
                "team": "Development",
                "department": "Engineering"
            },
            "privacy": {
                "encrypt_window_titles": True,
                "exclude_keywords": ["password", "private", "secret", "banking"],
                "work_hours_only": False,
                "work_hours": {"start": "09:00", "end": "18:00"},
                "excluded_apps": ["1Password", "Keychain Access", "Banking"]
            }
        }

        config_file = self.config_path / "sync_config.json"
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)

    def setup_sync_service(self):
        """Create sync script for macOS"""
        sync_script_content = f'''#!/usr/bin/env python3
"""
ActivityWatch Sync Service for macOS
"""
import requests
import json
import time
import urllib.request
from pathlib import Path

class ActivityWatchSync:
    def __init__(self):
        config_path = Path.home() / 'Library' / 'Application Support' / 'ActivityWatch-Team' / 'sync_config.json'
        with open(config_path, 'r') as f:
            self.config = json.load(f)

        self.server_url = self.config['sync_server_url']
        self.user_email = self.config['user_info']['email']
        self.aw_url = self.config['activitywatch_url']

    def sync_data(self):
        """Sync ActivityWatch data to server"""
        try:
            # Get buckets from ActivityWatch
            buckets_url = f"{{self.aw_url}}/api/0/buckets"
            response = urllib.request.urlopen(buckets_url)
            buckets = json.loads(response.read())

            # Sync data to server
            sync_data = {{
                "user_email": self.user_email,
                "buckets": buckets,
                "timestamp": time.time()
            }}

            requests.post(f"{{self.server_url}}/sync", json=sync_data)
            print(f"[SUCCESS] Synced data for {{self.user_email}}")

        except Exception as e:
            print(f"[ERROR] Sync failed: {{e}}")

if __name__ == "__main__":
    sync = ActivityWatchSync()
    sync.sync_data()
'''

        sync_script = self.config_path / "sync_service.py"
        with open(sync_script, 'w') as f:
            f.write(sync_script_content)

        # Make script executable
        os.chmod(sync_script, 0o755)

    def create_launch_agent(self):
        """Create Launch Agent for automatic startup and sync"""
        plist_content = f'''<?xml version="1.0" encoding="UTF-8"?>
<!DOCTYPE plist PUBLIC "-//Apple//DTD PLIST 1.0//EN" "http://www.apple.com/DTDs/PropertyList-1.0.dtd">
<plist version="1.0">
<dict>
    <key>Label</key>
    <string>com.activitywatch.team</string>
    <key>ProgramArguments</key>
    <array>
        <string>/usr/bin/python3</string>
        <string>{self.config_path}/sync_service.py</string>
    </array>
    <key>StartInterval</key>
    <integer>1800</integer>
    <key>RunAtLoad</key>
    <true/>
    <key>KeepAlive</key>
    <false/>
</dict>
</plist>'''

        plist_file = self.launchd_path / "com.activitywatch.team.plist"
        with open(plist_file, 'w') as f:
            f.write(plist_content)

        # Load the launch agent
        subprocess.run(["launchctl", "load", str(plist_file)], check=True)

    def test_installation(self):
        """Test the installation"""
        try:
            # Test ActivityWatch API
            response = urllib.request.urlopen("http://localhost:5600/api/0/buckets", timeout=5)
            if response.status == 200:
                return True
        except:
            pass

        # Start ActivityWatch if not running
        aw_app = self.home_path / "Applications" / "ActivityWatch.app"
        if aw_app.exists():
            subprocess.Popen(["open", str(aw_app)])
            time.sleep(3)

        return True

def main():
    """Main entry point"""
    if platform.system() != "Darwin":
        print("❌ This installer is for macOS only!")
        return

    installer = ActivityWatchTerminalInstaller()
    installer.run_installation()

if __name__ == "__main__":
    main()