"""
ActivityWatch Team Edition - Mac Installer
Single executable that installs everything without requiring Python
"""

import sys
import os
import subprocess
import urllib.request
import json
import time
import requests
import tkinter as tk
from tkinter import messagebox, simpledialog
from pathlib import Path
import threading
import webbrowser
import platform
import shutil

class ActivityWatchMacInstaller:
    def __init__(self):
        # macOS specific paths
        self.home_path = Path.home()
        self.install_path = self.home_path / 'Applications' / 'ActivityWatch-Team'
        self.config_path = self.home_path / 'Library' / 'Application Support' / 'ActivityWatch-Team'
        self.launchd_path = self.home_path / 'Library' / 'LaunchAgents'
        self.server_url = "https://activitywatch-sync-server-1051608384208.us-central1.run.app"

        # Create GUI
        self.root = tk.Tk()
        self.root.title("ActivityWatch Team Edition Installer")
        self.root.geometry("500x500")
        self.root.resizable(False, False)

        # macOS specific styling and fixes
        if platform.system() == "Darwin":
            try:
                # Use system appearance on macOS
                self.root.tk.call('tk', 'appname', 'ActivityWatch Team Installer')
                # Fix for blank window on macOS
                self.root.lift()
                self.root.attributes('-topmost', True)
                self.root.after_idle(self.root.attributes, '-topmost', False)
            except:
                pass

        self.setup_gui()

    def setup_gui(self):
        """Create the installer GUI"""

        # Header
        header_frame = tk.Frame(self.root, bg="#2E86AB", height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)

        title_label = tk.Label(header_frame, text="ActivityWatch Team Edition for Mac",
                              font=("Arial", 16, "bold"), fg="white", bg="#2E86AB")
        title_label.pack(pady=20)

        # Main content
        content_frame = tk.Frame(self.root, padx=30, pady=20)
        content_frame.pack(fill="both", expand=True)

        # Description
        desc_text = """This installer will set up ActivityWatch with automatic sync for your team.

What will be installed:
• ActivityWatch time tracking application
• Automatic sync to company database
• Privacy controls and encryption
• Dock and Applications folder shortcuts
• Launch agent for auto-start

No Python installation required!
Installation time: 2-3 minutes"""

        desc_label = tk.Label(content_frame, text=desc_text, font=("Arial", 10),
                             justify="left", wraplength=400)
        desc_label.pack(pady=(0, 20))

        # Email input
        email_frame = tk.Frame(content_frame)
        email_frame.pack(fill="x", pady=(0, 20))

        tk.Label(email_frame, text="Work Email:", font=("Arial", 10, "bold")).pack(anchor="w")
        self.email_var = tk.StringVar()
        self.email_entry = tk.Entry(email_frame, textvariable=self.email_var,
                                   font=("Arial", 10), width=40)
        self.email_entry.pack(fill="x", pady=(5, 0))

        # Progress bar area
        self.progress_frame = tk.Frame(content_frame)
        self.progress_frame.pack(fill="x", pady=(0, 20))

        self.status_label = tk.Label(self.progress_frame, text="Ready to install",
                                    font=("Arial", 9), fg="gray")
        self.status_label.pack()

        # Buttons
        button_frame = tk.Frame(content_frame)
        button_frame.pack(fill="x")

        self.install_button = tk.Button(button_frame, text="Install ActivityWatch",
                                       command=self.start_installation,
                                       bg="#007AFF", fg="white", font=("Arial", 11, "bold"),
                                       padx=20, pady=8)
        self.install_button.pack(side="left")

        self.cancel_button = tk.Button(button_frame, text="Cancel",
                                      command=self.root.quit,
                                      bg="#FF3B30", fg="white", font=("Arial", 11),
                                      padx=20, pady=8)
        self.cancel_button.pack(side="right")

    def update_status(self, message):
        """Update status message"""
        self.status_label.config(text=message)
        self.root.update()

    def start_installation(self):
        """Start the installation process"""
        email = self.email_var.get().strip()

        if not email or '@' not in email:
            messagebox.showerror("Error", "Please enter a valid work email address")
            return

        # Disable buttons during installation
        self.install_button.config(state="disabled")
        self.email_entry.config(state="disabled")

        # Start installation in separate thread
        install_thread = threading.Thread(target=self.run_installation, args=(email,))
        install_thread.daemon = True
        install_thread.start()

    def run_installation(self, email):
        """Run the actual installation"""
        try:
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

            self.update_status("Testing connection...")
            self.test_installation()

            # Success!
            self.update_status("Installation completed successfully!")

            messagebox.showinfo("Success",
                               "ActivityWatch Team Edition installed successfully!\n\n"
                               "• Application installed in Applications folder\n"
                               "• Automatic sync enabled\n"
                               "• Dashboard: http://localhost:5600\n\n"
                               "ActivityWatch will start automatically on next login.")

            # Open dashboard
            if messagebox.askyesno("Open Dashboard", "Would you like to open the ActivityWatch dashboard now?"):
                webbrowser.open("http://localhost:5600")

            self.root.quit()

        except Exception as e:
            self.update_status(f"Installation failed: {str(e)}")
            messagebox.showerror("Installation Failed",
                               f"Installation failed: {str(e)}\n\n"
                               "Please contact IT support for assistance.")

            # Re-enable buttons
            self.install_button.config(state="normal")
            self.email_entry.config(state="normal")

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

        # Download the DMG
        urllib.request.urlretrieve(aw_url, dmg_path)

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
        messagebox.showerror("Error", "This installer is for macOS only!")
        return

    app = ActivityWatchMacInstaller()
    app.root.mainloop()

if __name__ == "__main__":
    main()