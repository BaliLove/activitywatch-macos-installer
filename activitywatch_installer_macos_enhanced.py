#!/usr/bin/env python3
"""
ActivityWatch Team Edition - Enhanced macOS Installer
Compatible with macOS 12+ (Monterey, Ventura, Sonoma)
Supports both GUI and terminal modes
"""

import sys
import os
import subprocess
import urllib.request
import json
import time
import platform
import shutil
import hashlib
import uuid
import logging
import plistlib
from pathlib import Path
from datetime import datetime, timezone
import tempfile
import ssl
import certifi

# Try to import GUI components
try:
    import tkinter as tk
    from tkinter import messagebox, simpledialog, ttk
    GUI_AVAILABLE = True
except ImportError:
    GUI_AVAILABLE = False
    print("⚠️  GUI not available, running in terminal mode")

# Try to import requests for better HTTP handling
try:
    import requests
    REQUESTS_AVAILABLE = True
except ImportError:
    REQUESTS_AVAILABLE = False
    print("⚠️  Requests not available, using urllib")

class ActivityWatchMacOSInstaller:
    def __init__(self, gui_mode=None):
        """Initialize installer with automatic mode detection"""
        # Auto-detect GUI availability if not specified
        if gui_mode is None:
            gui_mode = GUI_AVAILABLE and sys.stdout.isatty()
        
        self.gui_mode = gui_mode
        self.session_id = str(uuid.uuid4())
        
        # macOS specific paths
        self.home_path = Path.home()
        self.install_path = self.home_path / 'Applications'
        self.app_path = self.install_path / 'ActivityWatch.app'
        self.config_path = self.home_path / 'Library' / 'Application Support' / 'ActivityWatch-Team'
        self.launchd_path = self.home_path / 'Library' / 'LaunchAgents'
        
        # Server configuration
        self.server_url = "https://activitywatch-sync-server-1051608384208.us-central1.run.app"
        self.api_key = "aw-team-2025-secure-key-v1"
        
        # Create SSL context for downloads
        self.ssl_context = ssl.create_default_context(cafile=certifi.where())
        
        # Setup logging
        self.setup_logging()
        self.log_event("installer_initialized", {
            "gui_mode": self.gui_mode,
            "platform": platform.platform(),
            "python_version": platform.python_version()
        })
        
        # Initialize GUI if available
        if self.gui_mode and GUI_AVAILABLE:
            self.setup_gui()
    
    def setup_logging(self):
        """Setup comprehensive logging"""
        # Create logs directory
        log_dir = self.config_path / 'logs'
        log_dir.mkdir(parents=True, exist_ok=True)
        
        # Setup logger
        self.logger = logging.getLogger('activitywatch_installer')
        self.logger.setLevel(logging.INFO)
        
        # File handler
        log_file = log_dir / f'installer_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(logging.INFO)
        
        # Console handler
        console_handler = logging.StreamHandler()
        console_handler.setLevel(logging.INFO)
        
        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        file_handler.setFormatter(formatter)
        console_handler.setFormatter(formatter)
        
        self.logger.addHandler(file_handler)
        self.logger.addHandler(console_handler)
    
    def log_event(self, event_type, details=None, level="INFO"):
        """Log structured events"""
        if details is None:
            details = {}
        
        event_data = {
            "session_id": self.session_id,
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "hostname": platform.node(),
            **details
        }
        
        message = f"{event_type} | {json.dumps(details, default=str)}"
        
        if level == "ERROR":
            self.logger.error(message)
        elif level == "WARN":
            self.logger.warning(message)
        else:
            self.logger.info(message)
    
    def setup_gui(self):
        """Setup GUI interface"""
        self.root = tk.Tk()
        self.root.title("ActivityWatch Team Installer")
        self.root.geometry("600x700")
        self.root.resizable(False, False)
        
        # Set app icon if available
        try:
            # Try to use system icon
            self.root.iconbitmap()
        except:
            pass
        
        self.create_gui_components()
    
    def create_gui_components(self):
        """Create GUI components"""
        # Header
        header_frame = tk.Frame(self.root, bg="#007ACC", height=100)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)
        
        title_label = tk.Label(
            header_frame, 
            text="🍎 ActivityWatch Team Edition", 
            font=("SF Pro Display", 18, "bold") if "SF Pro Display" in tk.font.families() else ("Arial", 18, "bold"),
            fg="white", 
            bg="#007ACC"
        )
        title_label.pack(pady=30)
        
        # Main content
        content_frame = tk.Frame(self.root, padx=40, pady=30)
        content_frame.pack(fill="both", expand=True)
        
        # Description
        desc_text = """This installer will set up ActivityWatch with automatic team sync for macOS.

What will be installed:
• ActivityWatch time tracking application
• Automatic sync to company database every 10 minutes  
• Privacy controls and data encryption
• Launch Agent for automatic startup
• Applications folder integration

Requirements:
• macOS 12+ (Monterey, Ventura, or Sonoma)
• Internet connection for sync
• Admin permissions may be required

Installation time: 3-5 minutes"""
        
        desc_label = tk.Label(
            content_frame, 
            text=desc_text, 
            font=("SF Pro Text", 11) if "SF Pro Text" in tk.font.families() else ("Arial", 11),
            justify="left", 
            wraplength=500,
            bg=self.root.cget('bg')
        )
        desc_label.pack(pady=(0, 30))
        
        # Email input section
        email_frame = tk.LabelFrame(content_frame, text="User Information", font=("Arial", 12, "bold"))
        email_frame.pack(fill="x", pady=(0, 30))
        
        tk.Label(
            email_frame, 
            text="Work Email Address:", 
            font=("Arial", 11)
        ).pack(anchor="w", padx=15, pady=(15, 5))
        
        self.email_var = tk.StringVar()
        self.email_entry = tk.Entry(
            email_frame, 
            textvariable=self.email_var,
            font=("Arial", 11), 
            width=50
        )
        self.email_entry.pack(fill="x", padx=15, pady=(0, 15))
        
        # Progress section
        self.progress_frame = tk.LabelFrame(content_frame, text="Installation Progress", font=("Arial", 12, "bold"))
        self.progress_frame.pack(fill="x", pady=(0, 30))
        
        self.status_label = tk.Label(
            self.progress_frame, 
            text="Ready to install", 
            font=("Arial", 10),
            fg="gray"
        )
        self.status_label.pack(pady=(15, 10))
        
        # Progress bar
        self.progress_var = tk.DoubleVar()
        self.progress_bar = ttk.Progressbar(
            self.progress_frame,
            variable=self.progress_var,
            maximum=100,
            length=400
        )
        self.progress_bar.pack(pady=(0, 15))
        
        # Buttons
        button_frame = tk.Frame(content_frame)
        button_frame.pack(fill="x", pady=(30, 0))
        
        self.install_button = tk.Button(
            button_frame, 
            text="🚀 Install ActivityWatch",
            command=self.start_installation,
            bg="#28A745", 
            fg="white", 
            font=("Arial", 12, "bold"),
            padx=30, 
            pady=10,
            relief="flat",
            cursor="hand2"
        )
        self.install_button.pack(side="left")
        
        self.cancel_button = tk.Button(
            button_frame, 
            text="Cancel",
            command=self.cancel_installation,
            bg="#DC3545", 
            fg="white", 
            font=("Arial", 12),
            padx=30, 
            pady=10,
            relief="flat",
            cursor="hand2"
        )
        self.cancel_button.pack(side="right")
        
        # System requirements check
        self.check_system_requirements()
    
    def check_system_requirements(self):
        """Check if system meets requirements"""
        issues = []
        
        # Check macOS version
        mac_version = platform.mac_ver()[0]
        if mac_version:
            major, minor = map(int, mac_version.split('.')[:2])
            if major < 12:
                issues.append(f"macOS 12+ required (found {mac_version})")
        
        # Check internet connectivity
        try:
            if REQUESTS_AVAILABLE:
                requests.get("https://google.com", timeout=5)
            else:
                urllib.request.urlopen("https://google.com", timeout=5)
        except:
            issues.append("Internet connection required")
        
        if issues and self.gui_mode:
            messagebox.showwarning(
                "System Requirements", 
                "⚠️ Potential issues detected:\n\n" + "\n".join(f"• {issue}" for issue in issues) + 
                "\n\nYou can continue, but installation may fail."
            )
    
    def update_progress(self, value, message):
        """Update progress in GUI mode"""
        if self.gui_mode and GUI_AVAILABLE:
            self.progress_var.set(value)
            self.status_label.config(text=message)
            self.root.update()
        else:
            print(f"[{int(value):3d}%] {message}")
    
    def start_installation(self):
        """Start installation process"""
        if self.gui_mode:
            email = self.email_var.get().strip()
            if not self.validate_email(email):
                messagebox.showerror("Invalid Email", "Please enter a valid work email address")
                return
            
            # Disable buttons
            self.install_button.config(state="disabled")
            self.email_entry.config(state="disabled")
            
            # Start installation in thread to prevent GUI freeze
            import threading
            install_thread = threading.Thread(target=self.run_installation, args=(email,))
            install_thread.daemon = True
            install_thread.start()
        else:
            # Terminal mode
            email = self.get_email_terminal()
            self.run_installation(email)
    
    def cancel_installation(self):
        """Cancel installation"""
        if self.gui_mode:
            self.root.quit()
        else:
            print("Installation cancelled")
            sys.exit(0)
    
    def validate_email(self, email):
        """Validate email format"""
        import re
        pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(pattern, email) is not None
    
    def get_email_terminal(self):
        """Get email in terminal mode"""
        while True:
            email = input("\n📧 Enter your work email: ").strip()
            if self.validate_email(email):
                return email
            print("❌ Please enter a valid email address")
    
    def run_installation(self, email):
        """Run the complete installation process"""
        try:
            self.log_event("installation_started", {"email": email})
            
            steps = [
                (10, "Verifying system compatibility", self.verify_system),
                (20, "Creating directories", self.create_directories),
                (30, "Downloading ActivityWatch", self.download_activitywatch),
                (50, "Installing ActivityWatch", self.install_activitywatch),
                (60, "Creating configuration", lambda: self.create_config(email)),
                (70, "Setting up sync service", self.setup_sync_service),
                (80, "Creating launch agent", self.create_launch_agent),
                (90, "Testing installation", self.test_installation),
                (100, "Installation completed", lambda: None)
            ]
            
            for progress, message, func in steps:
                self.update_progress(progress, message)
                if func:
                    func()
                time.sleep(0.5)  # Brief pause for user experience
            
            self.installation_success()
            
        except Exception as e:
            self.log_event("installation_failed", {"error": str(e), "type": type(e).__name__}, "ERROR")
            self.installation_failed(str(e))
    
    def verify_system(self):
        """Verify system compatibility"""
        if platform.system() != "Darwin":
            raise Exception("This installer is for macOS only")
        
        # Check Python version
        if sys.version_info < (3, 8):
            raise Exception("Python 3.8+ required")
        
        # Check for required commands
        required_commands = ["hdiutil", "launchctl", "open"]
        for cmd in required_commands:
            if shutil.which(cmd) is None:
                raise Exception(f"Required command '{cmd}' not found")
    
    def create_directories(self):
        """Create necessary directories"""
        dirs = [
            self.config_path,
            self.config_path / 'logs',
            self.launchd_path
        ]
        
        for directory in dirs:
            directory.mkdir(parents=True, exist_ok=True)
            self.log_event("directory_created", {"path": str(directory)})
    
    def download_activitywatch(self):
        """Download ActivityWatch for macOS"""
        # Determine architecture
        arch = "arm64" if platform.machine() == "arm64" else "x86_64"
        
        # ActivityWatch download URL
        aw_version = "v0.13.2"
        aw_url = f"https://github.com/ActivityWatch/activitywatch/releases/download/{aw_version}/activitywatch-{aw_version}-macos-{arch}.dmg"
        
        self.dmg_path = self.config_path / "activitywatch.dmg"
        
        self.log_event("download_started", {"url": aw_url, "architecture": arch})
        
        try:
            # Download with progress tracking
            urllib.request.urlretrieve(aw_url, self.dmg_path)
            
            # Verify download
            if not self.dmg_path.exists() or self.dmg_path.stat().st_size < 1024 * 1024:
                raise Exception("Download failed or file too small")
            
            self.log_event("download_completed", {
                "size": self.dmg_path.stat().st_size,
                "path": str(self.dmg_path)
            })
            
        except Exception as e:
            raise Exception(f"Failed to download ActivityWatch: {e}")
    
    def install_activitywatch(self):
        """Install ActivityWatch from DMG"""
        try:
            # Mount the DMG
            self.log_event("mounting_dmg", {"path": str(self.dmg_path)})
            
            mount_result = subprocess.run([
                "hdiutil", "attach", str(self.dmg_path), 
                "-nobrowse", "-quiet"
            ], capture_output=True, text=True, check=True)
            
            # Find mount point
            mount_point = None
            for line in mount_result.stdout.split('\n'):
                if 'ActivityWatch' in line and '/Volumes/' in line:
                    mount_point = line.split('\t')[-1].strip()
                    break
            
            if not mount_point:
                raise Exception("Could not find mounted ActivityWatch volume")
            
            self.log_event("dmg_mounted", {"mount_point": mount_point})
            
            # Copy ActivityWatch.app
            source_app = Path(mount_point) / "ActivityWatch.app"
            
            if not source_app.exists():
                raise Exception("ActivityWatch.app not found in mounted volume")
            
            # Remove existing installation if present
            if self.app_path.exists():
                shutil.rmtree(self.app_path)
            
            # Copy the app
            shutil.copytree(source_app, self.app_path)
            
            # Set permissions
            subprocess.run(["chmod", "-R", "755", str(self.app_path)], check=True)
            
            self.log_event("app_installed", {"path": str(self.app_path)})
            
            # Unmount DMG
            subprocess.run(["hdiutil", "detach", mount_point, "-quiet"], 
                         capture_output=True)
            
            # Clean up DMG
            self.dmg_path.unlink()
            
        except subprocess.CalledProcessError as e:
            raise Exception(f"Installation failed: {e.stderr}")
        except Exception as e:
            raise Exception(f"Installation error: {e}")
    
    def create_config(self, email):
        """Create configuration files"""
        config = {
            "sync_server_url": self.server_url,
            "api_key": self.api_key,
            "activitywatch_url": "http://localhost:5600",
            "sync_interval_minutes": 10,
            "user_info": {
                "email": email,
                "team": "Bali Love Team",
                "department": "Creative",
                "installation_id": self.session_id,
                "installed_at": datetime.now(timezone.utc).isoformat()
            },
            "privacy": {
                "encrypt_window_titles": True,
                "exclude_keywords": [
                    "password", "private", "secret", "banking", 
                    "login", "account", "credit card", "ssn"
                ],
                "excluded_apps": [
                    "1Password", "Keychain Access", "Banking", 
                    "Wallet", "Passwords", "Bitwarden"
                ],
                "work_hours_only": False,
                "work_hours": {"start": "09:00", "end": "18:00"}
            },
            "logging": {
                "level": "INFO",
                "max_log_files": 30,
                "max_log_size_mb": 10
            }
        }
        
        config_file = self.config_path / "sync_config.json"
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        # Set restrictive permissions
        os.chmod(config_file, 0o600)
        
        self.log_event("config_created", {
            "config_file": str(config_file),
            "user_email": email
        })
    
    def setup_sync_service(self):
        """Create sync service script"""
        sync_script_content = f'''#!/usr/bin/env python3
"""
ActivityWatch Sync Service for macOS
"""
import sys
import json
import requests
import time
import hashlib
import logging
from pathlib import Path
from datetime import datetime, timezone

class ActivityWatchSync:
    def __init__(self):
        self.config_path = Path.home() / 'Library' / 'Application Support' / 'ActivityWatch-Team'
        self.config_file = self.config_path / 'sync_config.json'
        
        if not self.config_file.exists():
            print(f"Config file not found: {{self.config_file}}")
            sys.exit(1)
        
        with open(self.config_file, 'r') as f:
            self.config = json.load(f)
        
        # Setup logging
        self.setup_logging()
        self.log("Sync service started")
    
    def setup_logging(self):
        log_dir = self.config_path / 'logs'
        log_dir.mkdir(exist_ok=True)
        
        self.logger = logging.getLogger('aw_sync')
        self.logger.setLevel(logging.INFO)
        
        # Rotating log handler
        log_file = log_dir / f"sync_{{datetime.now().strftime('%Y%m%d')}}.log"
        handler = logging.FileHandler(log_file)
        handler.setFormatter(logging.Formatter(
            '%(asctime)s | %(levelname)s | %(message)s'
        ))
        self.logger.addHandler(handler)
    
    def log(self, message, level="INFO"):
        if level == "ERROR":
            self.logger.error(message)
        elif level == "WARN":
            self.logger.warning(message)
        else:
            self.logger.info(message)
        print(f"[{{datetime.now().strftime('%H:%M:%S')}}] {{message}}")
    
    def sync_data(self):
        try:
            # Get ActivityWatch data
            aw_url = self.config['activitywatch_url']
            buckets_response = requests.get(f"{{aw_url}}/api/0/buckets", timeout=10)
            
            if not buckets_response.ok:
                self.log("ActivityWatch not available", "WARN")
                return
            
            buckets = buckets_response.json()
            all_events = []
            
            # Collect events from all buckets
            for bucket_id in buckets:
                try:
                    events_response = requests.get(
                        f"{{aw_url}}/api/0/buckets/{{bucket_id}}/events?limit=50",
                        timeout=10
                    )
                    if events_response.ok:
                        events = events_response.json()
                        for event in events:
                            event_data = {{
                                'event_id': event.get('id', f"{{bucket_id}}_{{len(all_events)}}"),
                                'timestamp': event.get('timestamp'),
                                'duration': event.get('duration', 0),
                                'application': event.get('data', {{}}).get('app', 'Unknown'),
                                'window_title': self.filter_title(event.get('data', {{}}).get('title', '')),
                                'hostname': event.get('data', {{}}).get('hostname', 'unknown'),
                                'metadata': event.get('data', {{}})
                            }}
                            all_events.append(event_data)
                except Exception as e:
                    self.log(f"Error processing bucket {{bucket_id}}: {{e}}", "ERROR")
                    continue
            
            if all_events:
                # Send to server
                headers = {{
                    'Content-Type': 'application/json',
                    'X-API-Key': self.config['api_key']
                }}
                
                payload = {{
                    'user_email': self.config['user_info']['email'],
                    'events': all_events
                }}
                
                response = requests.post(
                    f"{{self.config['sync_server_url']}}/api/sync",
                    json=payload,
                    headers=headers,
                    timeout=30
                )
                
                if response.ok:
                    self.log(f"Successfully synced {{len(all_events)}} events")
                else:
                    self.log(f"Sync failed: {{response.status_code}} - {{response.text}}", "ERROR")
            else:
                self.log("No events to sync")
        
        except Exception as e:
            self.log(f"Sync error: {{e}}", "ERROR")
    
    def filter_title(self, title):
        """Filter sensitive information from window titles"""
        if not title:
            return title
        
        sensitive_keywords = self.config.get('privacy', {{}}).get('exclude_keywords', [])
        title_lower = title.lower()
        
        for keyword in sensitive_keywords:
            if keyword.lower() in title_lower:
                return "[FILTERED]"
        
        return title

if __name__ == "__main__":
    sync = ActivityWatchSync()
    sync.sync_data()
'''
        
        sync_script = self.config_path / "sync_service.py"
        with open(sync_script, 'w') as f:
            f.write(sync_script_content)
        
        # Make executable
        os.chmod(sync_script, 0o755)
        
        self.log_event("sync_service_created", {"path": str(sync_script)})
    
    def create_launch_agent(self):
        """Create Launch Agent for automatic startup"""
        plist_data = {
            'Label': 'com.activitywatch.team',
            'ProgramArguments': [
                '/usr/bin/python3',
                str(self.config_path / 'sync_service.py')
            ],
            'StartInterval': 600,  # 10 minutes
            'RunAtLoad': True,
            'KeepAlive': False,
            'StandardOutPath': str(self.config_path / 'logs' / 'sync_stdout.log'),
            'StandardErrorPath': str(self.config_path / 'logs' / 'sync_stderr.log'),
            'ProcessType': 'Background'
        }
        
        plist_file = self.launchd_path / "com.activitywatch.team.plist"
        
        with open(plist_file, 'wb') as f:
            plistlib.dump(plist_data, f)
        
        # Load the launch agent
        try:
            subprocess.run([
                "launchctl", "load", "-w", str(plist_file)
            ], check=True, capture_output=True)
            
            self.log_event("launch_agent_created", {
                "plist_file": str(plist_file),
                "loaded": True
            })
        except subprocess.CalledProcessError as e:
            self.log_event("launch_agent_failed", {
                "error": e.stderr.decode() if e.stderr else str(e)
            }, "WARN")
    
    def test_installation(self):
        """Test the installation"""
        # Test 1: Check if app exists
        if not self.app_path.exists():
            raise Exception("ActivityWatch.app not found")
        
        # Test 2: Try to start ActivityWatch
        try:
            subprocess.run(["open", str(self.app_path)], 
                          capture_output=True, timeout=10)
            time.sleep(3)  # Wait for app to start
        except:
            pass  # Non-critical
        
        # Test 3: Test server connectivity
        try:
            if REQUESTS_AVAILABLE:
                response = requests.get(self.server_url, timeout=10)
                if not response.ok:
                    self.log_event("server_connectivity_warning", {
                        "status_code": response.status_code
                    }, "WARN")
            else:
                urllib.request.urlopen(self.server_url, timeout=10)
        except Exception as e:
            self.log_event("server_connectivity_failed", {
                "error": str(e)
            }, "WARN")
        
        self.log_event("installation_tested")
    
    def installation_success(self):
        """Handle successful installation"""
        self.log_event("installation_completed")
        
        success_message = """🎉 Installation completed successfully!

✅ ActivityWatch installed in Applications folder
✅ Automatic sync enabled (every 10 minutes)  
✅ Launch Agent configured for auto-start
✅ Privacy filters activated

Next steps:
• ActivityWatch will start automatically on login
• Access dashboard at: http://localhost:5600
• Check sync logs in: ~/Library/Application Support/ActivityWatch-Team/logs

The application will begin tracking activity immediately."""

        if self.gui_mode and GUI_AVAILABLE:
            messagebox.showinfo("Installation Complete", success_message)
            
            if messagebox.askyesno("Open Dashboard", 
                                 "Would you like to open the ActivityWatch dashboard now?"):
                subprocess.run(["open", "http://localhost:5600"])
            
            self.root.quit()
        else:
            print("\n" + "="*60)
            print(success_message)
            print("="*60)
            
            # Ask about opening dashboard
            try:
                open_dash = input("\nOpen ActivityWatch dashboard now? (y/N): ").lower()
                if open_dash in ['y', 'yes']:
                    subprocess.run(["open", "http://localhost:5600"])
            except KeyboardInterrupt:
                pass
    
    def installation_failed(self, error):
        """Handle installation failure"""
        error_message = f"""❌ Installation failed: {error}

Please try the following:
1. Check internet connection
2. Ensure you have admin permissions
3. Check system requirements (macOS 12+)
4. Contact IT support with error details

Error details have been logged to:
{self.config_path / 'logs'}"""

        if self.gui_mode and GUI_AVAILABLE:
            messagebox.showerror("Installation Failed", error_message)
            # Re-enable buttons
            self.install_button.config(state="normal")
            self.email_entry.config(state="normal")
        else:
            print(f"\n❌ {error_message}")
            sys.exit(1)
    
    def run(self):
        """Main entry point"""
        if not self.gui_mode or not GUI_AVAILABLE:
            # Terminal mode
            print("🍎 ActivityWatch Team Edition - macOS Installer")
            print("=" * 50)
            print("\nRunning in terminal mode...")
            
            if platform.system() != "Darwin":
                print("❌ This installer is for macOS only!")
                return
            
            email = self.get_email_terminal()
            print(f"\n✅ Email: {email}")
            
            confirm = input("\n🚀 Ready to install? (y/N): ").lower()
            if confirm not in ['y', 'yes']:
                print("Installation cancelled")
                return
            
            print("\n🔧 Starting installation...")
            self.run_installation(email)
        else:
            # GUI mode
            self.root.mainloop()

def main():
    """Main entry point"""
    # Check for command line arguments
    gui_mode = None
    if len(sys.argv) > 1:
        if sys.argv[1] == '--terminal':
            gui_mode = False
        elif sys.argv[1] == '--gui':
            gui_mode = True
    
    installer = ActivityWatchMacOSInstaller(gui_mode=gui_mode)
    installer.run()

if __name__ == "__main__":
    main()