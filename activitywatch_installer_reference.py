"""
ActivityWatch Team Edition - Standalone Installer
Single EXE file that installs everything without requiring Python
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
import logging
import hashlib
import uuid
from datetime import datetime, timezone

# Import security alerting
try:
    from security_alerts import SecurityAlerter
except ImportError:
    # Fallback if security_alerts module not available
    class SecurityAlerter:
        def alert_auth_failure(self, *args, **kwargs): pass
        def alert_sync_failure(self, *args, **kwargs): pass
        def alert_suspicious_activity(self, *args, **kwargs): pass
        def alert_connection_failure(self, *args, **kwargs): pass

class ActivityWatchInstaller:
    def __init__(self):
        self.install_path = Path(os.environ['LOCALAPPDATA']) / 'ActivityWatch-Team'
        self.config_path = Path(os.environ['APPDATA']) / 'ActivityWatch-Team'
        self.server_url = "https://activitywatch-sync-server-1051608384208.us-central1.run.app"

        # API key management - multiple options for security
        self.api_key = self.get_api_key()

        # Initialize audit logging and alerting
        self.setup_audit_logging()
        self.security_alerter = SecurityAlerter()
        self.log_security_event("installer_started", {"install_path": str(self.install_path)})

        # Create GUI
        self.root = tk.Tk()
        self.root.title("ActivityWatch Team Edition Installer")
        self.root.geometry("500x500")
        self.root.resizable(False, False)

        self.setup_gui()

    def get_api_key(self):
        """Get API key from multiple sources (in order of preference)"""
        # 1. Environment variable (most secure for enterprise deployment)
        api_key = os.environ.get('ACTIVITYWATCH_API_KEY')
        if api_key:
            return api_key

        # 2. Config file (for updates/rotation)
        config_file = self.config_path / 'api_key.txt'
        if config_file.exists():
            try:
                with open(config_file, 'r') as f:
                    api_key = f.read().strip()
                    if api_key:
                        return api_key
            except:
                pass

        # 3. Default key (fallback - should be rotated regularly)
        return "aw-team-2025-secure-key-v1"

    def rotate_api_key(self, new_key):
        """Rotate API key by saving to config file"""
        try:
            config_file = self.config_path / 'api_key.txt'
            # Ensure config directory exists
            self.config_path.mkdir(parents=True, exist_ok=True)

            # Save new key securely
            with open(config_file, 'w') as f:
                f.write(new_key)

            # Set restrictive file permissions (Windows)
            import stat
            os.chmod(config_file, stat.S_IREAD | stat.S_IWRITE)

            # Update current instance
            self.api_key = new_key

            # Update sync config if it exists
            sync_config_file = self.config_path / 'sync_config.json'
            if sync_config_file.exists():
                import json
                with open(sync_config_file, 'r') as f:
                    config = json.load(f)
                config['api_key'] = new_key
                with open(sync_config_file, 'w') as f:
                    json.dump(config, f, indent=2)

            return True
        except Exception as e:
            print(f"API key rotation failed: {e}")
            return False

    def validate_api_key_format(self, key):
        """Validate API key format for security"""
        if not key or len(key) < 16:
            return False
        # Key should be alphanumeric with dashes
        import re
        if not re.match(r'^[a-zA-Z0-9\-_]{16,}$', key):
            return False
        return True

    def setup_audit_logging(self):
        """Initialize secure audit logging system"""
        # Create audit log directory
        self.audit_path = self.config_path / 'audit'
        self.audit_path.mkdir(parents=True, exist_ok=True)

        # Setup audit logger
        self.audit_logger = logging.getLogger('activitywatch_security_audit')
        self.audit_logger.setLevel(logging.INFO)

        # Create audit log file with date
        log_file = self.audit_path / f'security_audit_{datetime.now().strftime("%Y%m%d")}.log'

        # File handler for audit logs
        handler = logging.FileHandler(log_file, encoding='utf-8')
        formatter = logging.Formatter(
            '%(asctime)s|%(levelname)s|%(message)s',
            datefmt='%Y-%m-%d %H:%M:%S UTC'
        )
        handler.setFormatter(formatter)
        self.audit_logger.addHandler(handler)

        # Generate session ID for tracking
        self.session_id = str(uuid.uuid4())

    def log_security_event(self, event_type, details=None, level="INFO"):
        """Log security-related events with structured data"""
        if details is None:
            details = {}

        # Add standard security context
        event_data = {
            "session_id": self.session_id,
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": os.environ.get('USERNAME', 'unknown'),
            "hostname": os.environ.get('COMPUTERNAME', 'unknown'),
            "api_key_source": self.get_api_key_source(),
            **details
        }

        # Create structured log entry
        log_message = "|".join([
            f"EVENT:{event_type}",
            f"SESSION:{self.session_id}",
            f"USER:{event_data['user_id']}",
            f"HOST:{event_data['hostname']}",
            f"DATA:{str(details)}"
        ])

        # Log based on severity
        if level == "ERROR":
            self.audit_logger.error(log_message)
        elif level == "WARN":
            self.audit_logger.warning(log_message)
        else:
            self.audit_logger.info(log_message)

        return event_data

    def get_api_key_source(self):
        """Determine and log API key source for security tracking"""
        if os.environ.get('ACTIVITYWATCH_API_KEY'):
            return "environment"
        elif (self.config_path / 'api_key.txt').exists():
            return "config_file"
        else:
            return "default"

    def log_api_operation(self, operation, endpoint, status_code, details=None):
        """Log API operations for security monitoring"""
        api_details = {
            "operation": operation,
            "endpoint": endpoint,
            "status_code": status_code,
            "api_key_hash": hashlib.sha256(self.api_key.encode()).hexdigest()[:8],
            **(details or {})
        }

        level = "ERROR" if status_code >= 400 else "INFO"
        self.log_security_event("api_operation", api_details, level)

    def monitor_failed_auth(self, response):
        """Monitor and alert on authentication failures"""
        if response.status_code == 401:
            api_key_hash = hashlib.sha256(self.api_key.encode()).hexdigest()[:8]
            self.log_security_event("auth_failure", {
                "status_code": response.status_code,
                "response_text": response.text[:200],
                "api_key_hash": api_key_hash
            }, "ERROR")

            # Send security alert
            self.security_alerter.alert_auth_failure(
                user_id=os.environ.get('USERNAME', 'unknown'),
                hostname=os.environ.get('COMPUTERNAME', 'unknown'),
                api_key_hash=api_key_hash,
                response_text=response.text
            )
            return True
        elif response.status_code == 403:
            self.log_security_event("auth_forbidden", {
                "status_code": response.status_code,
                "response_text": response.text[:200]
            }, "WARN")
            return True
        return False

    def setup_gui(self):
        """Create the installer GUI"""

        # Header
        header_frame = tk.Frame(self.root, bg="#2E86AB", height=80)
        header_frame.pack(fill="x")
        header_frame.pack_propagate(False)

        title_label = tk.Label(header_frame, text="ActivityWatch Team Edition",
                              font=("Arial", 16, "bold"), fg="white", bg="#2E86AB")
        title_label.pack(pady=20)

        # Main content
        content_frame = tk.Frame(self.root, padx=30, pady=20)
        content_frame.pack(fill="both", expand=True)

        # Description
        desc_text = """This installer will set up ActivityWatch with automatic BigQuery sync for your team.

What will be installed:
• ActivityWatch time tracking application
• Automatic sync to company database
• Privacy controls and encryption
• Desktop shortcuts

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
                                       bg="#28A745", fg="white", font=("Arial", 11, "bold"),
                                       padx=20, pady=8)
        self.install_button.pack(side="left")

        self.cancel_button = tk.Button(button_frame, text="Cancel",
                                      command=self.root.quit,
                                      bg="#DC3545", fg="white", font=("Arial", 11),
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
            self.log_security_event("installation_failed", {"reason": "invalid_email", "email_provided": bool(email)}, "ERROR")
            messagebox.showerror("Error", "Please enter a valid work email address")
            return

        # Log installation start
        self.log_security_event("installation_started", {"user_email": email})

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

            self.update_status("Setting up categories...")
            self.setup_bali_love_categories(email)

            self.update_status("Creating shortcuts...")
            self.create_shortcuts()

            self.update_status("Testing connection...")
            self.test_installation()

            # Success!
            self.update_status("Installation completed successfully!")

            messagebox.showinfo("Success",
                               "ActivityWatch Team Edition installed successfully!\n\n"
                               "• Desktop shortcuts created\n"
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

    def install_activitywatch(self):
        """Download and install ActivityWatch"""
        aw_url = "https://github.com/ActivityWatch/activitywatch/releases/download/v0.13.2/activitywatch-v0.13.2-windows-x86_64-setup.exe"
        installer_path = self.install_path / "aw_installer.exe"

        # Download
        urllib.request.urlretrieve(aw_url, installer_path)

        # Install silently
        subprocess.run([str(installer_path), "/S"], check=True)

        # Clean up
        installer_path.unlink()

    def create_config(self, email):
        """Create configuration file"""
        config = {
            "sync_server_url": self.server_url,
            "api_key": self.api_key,  # Use the securely obtained API key
            "activitywatch_url": "http://localhost:5600",
            "sync_interval_minutes": 10,
            "user_info": {
                "email": email,
                "team": "Bali Love Creative Team",
                "department": "Creative Marketing"
            },
            "privacy": {
                "encrypt_window_titles": True,
                "exclude_keywords": ["password", "private", "secret", "banking"],
                "excluded_apps": ["1Password", "KeePass", "Banking"]
            }
        }

        config_file = self.config_path / "sync_config.json"
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)

    def setup_sync_service(self):
        """Set up automatic sync service"""
        # Copy this executable to install directory for sync
        import shutil
        sync_exe = self.install_path / "activitywatch_sync.exe"
        shutil.copy2(sys.executable, sync_exe)

        # Create scheduled task for ActivityWatch startup
        aw_path = Path(os.environ['LOCALAPPDATA']) / "Programs" / "ActivityWatch" / "aw-qt.exe"
        if aw_path.exists():
            task_cmd = f'schtasks /create /tn "ActivityWatch-Team" /tr "{aw_path}" /sc onlogon /rl highest /f'
            subprocess.run(task_cmd, shell=True, capture_output=True)

        # Create TWO scheduled tasks for sync:
        # 1. Run at system startup (so it works after reboot)
        sync_startup_cmd = f'schtasks /create /tn "ActivityWatch-Team-Sync-Startup" /tr "{sync_exe} --sync" /sc onstart /delay 0002:00 /rl highest /f'
        subprocess.run(sync_startup_cmd, shell=True, capture_output=True)

        # 2. Run every 10 minutes while the system is running
        sync_periodic_cmd = f'schtasks /create /tn "ActivityWatch-Team-Sync-Periodic" /tr "{sync_exe} --sync" /sc minute /mo 10 /rl highest /f'
        subprocess.run(sync_periodic_cmd, shell=True, capture_output=True)

        # Also create a task that runs when user logs in (in case system wasn't rebooted)
        sync_logon_cmd = f'schtasks /create /tn "ActivityWatch-Team-Sync-Logon" /tr "{sync_exe} --sync" /sc onlogon /delay 0001:00 /rl highest /f'
        subprocess.run(sync_logon_cmd, shell=True, capture_output=True)

    def create_shortcuts(self):
        """Create desktop shortcuts"""
        import winshell
        from win32com.client import Dispatch

        desktop = winshell.desktop()

        # ActivityWatch Dashboard shortcut
        shell = Dispatch('WScript.Shell')
        shortcut = shell.CreateShortCut(os.path.join(desktop, "ActivityWatch Dashboard.lnk"))
        shortcut.Targetpath = "http://localhost:5600"
        shortcut.IconLocation = str(Path(os.environ['LOCALAPPDATA']) / "Programs" / "ActivityWatch" / "aw-qt.exe")
        shortcut.save()

    def setup_bali_love_categories(self, user_email):
        """Fetch and set up team categories from server"""
        try:
            self.log_security_event("categories_fetch_started", {"server_url": self.server_url})

            # Fetch categories from server
            headers = {
                'Content-Type': 'application/json',
                'X-API-Key': self.api_key
            }

            params = {'email': user_email}
            response = requests.get(f"{self.server_url}/api/categories",
                                  headers=headers, params=params, timeout=10)

            if response.status_code == 200:
                categories_response = response.json()
                categories = categories_response.get('categories', [])
                team_id = categories_response.get('team_id', 'unknown')

                if categories:
                    # Save categories for local use
                    categories_file = self.config_path / "team_categories.json"
                    with open(categories_file, 'w') as f:
                        json.dump(categories_response, f, indent=2)

                    # Apply categories to ActivityWatch (wait for AW to be ready)
                    self.apply_categories_to_activitywatch(categories)

                    self.log_security_event("categories_setup_completed", {
                        "team_id": team_id,
                        "categories_count": len(categories),
                        "config_file": str(categories_file)
                    })
                else:
                    self.log_security_event("categories_setup_warning",
                                          {"message": "No categories received from server"}, "WARNING")
            else:
                self.log_security_event("categories_fetch_failed", {
                    "status_code": response.status_code,
                    "response": response.text[:200]
                }, "ERROR")

                # Fallback: create minimal local categories
                self.create_fallback_categories()

        except Exception as e:
            self.log_security_event("categories_setup_error", {"error": str(e)}, "ERROR")
            # Create fallback categories so users still get some categorization
            self.create_fallback_categories()

    def apply_categories_to_activitywatch(self, categories):
        """Apply categories to ActivityWatch via API"""
        try:
            # Convert to ActivityWatch format
            aw_categories = {}
            for category in categories:
                category_name = category.get('category_name', category.get('name', ''))
                rules = category.get('rules', [])

                if rules and category_name:
                    # Combine all regex patterns with OR
                    regex_patterns = []
                    for rule in rules:
                        regex = rule.get('rule_regex', rule.get('regex', ''))
                        if regex:
                            regex_patterns.append(f"({regex})")

                    if regex_patterns:
                        combined_regex = '|'.join(regex_patterns)
                        aw_categories[category_name] = {
                            'name': category_name,
                            'rule': {
                                'type': 'regex',
                                'regex': combined_regex
                            }
                        }

            if not aw_categories:
                self.log_security_event("categories_apply_warning",
                                      {"message": "No valid categories to apply"}, "WARNING")
                return

            # Save in ActivityWatch import format for backup
            import_file = self.config_path / "bali_love_categories_import.json"
            with open(import_file, 'w') as f:
                json.dump(aw_categories, f, indent=2)

            # Wait for ActivityWatch to be ready and inject categories
            max_attempts = 30  # 30 seconds total wait
            for attempt in range(max_attempts):
                try:
                    # Check if ActivityWatch is running
                    response = requests.get("http://localhost:5600/api/0/buckets", timeout=2)
                    if response.ok:
                        # ActivityWatch is ready, inject categories
                        self.inject_categories_to_activitywatch(aw_categories)
                        break
                except requests.exceptions.RequestException:
                    if attempt < max_attempts - 1:
                        time.sleep(1)  # Wait 1 second before retry
                        continue
                    else:
                        self.log_security_event("categories_apply_timeout",
                                              {"message": "ActivityWatch not ready for category injection"}, "WARNING")

            self.log_security_event("categories_applied", {
                "categories_count": len(aw_categories),
                "import_file": str(import_file)
            })

        except Exception as e:
            self.log_security_event("categories_apply_failed", {"error": str(e)}, "ERROR")

    def inject_categories_to_activitywatch(self, categories):
        """Directly inject categories into ActivityWatch via API"""
        try:
            # Use the correct categories endpoint
            categories_url = "http://localhost:5600/api/0/settings/categories"

            # Post categories directly to the endpoint
            response = requests.post(categories_url, json=categories, timeout=5)

            if response.ok:
                self.log_security_event("categories_injected", {
                    "categories_injected": len(categories),
                    "endpoint": categories_url
                })

                print(f"✅ Injected {len(categories)} categories into ActivityWatch")

                # Verify injection worked
                verify_response = requests.get(categories_url, timeout=5)
                if verify_response.ok:
                    verified_count = len(verify_response.json()) if verify_response.json() else 0
                    print(f"✅ Verified: {verified_count} categories now active")

                return True
            else:
                self.log_security_event("categories_injection_failed", {
                    "status_code": response.status_code,
                    "response": response.text[:200]
                }, "WARNING")
                print(f"⚠️ Category injection failed: {response.status_code}")
                return False

        except Exception as e:
            self.log_security_event("categories_injection_failed", {"error": str(e)}, "WARNING")
            print(f"⚠️ Could not inject categories directly: {e}")
            return False

    def create_fallback_categories(self):
        """Create minimal fallback categories if server fetch fails"""
        try:
            fallback_categories = {
                "Development": {"regex": "(Visual Studio Code|Terminal|Cursor|github\\.com|bali\\.love)"},
                "Social Media": {"regex": "(instagram\\.com|facebook\\.com|tiktok\\.com)"},
                "Communication": {"regex": "(gmail\\.com|WhatsApp|missiveapp\\.com)"},
                "Content Creation": {"regex": "(Adobe Illustrator|canva\\.com|capcut\\.com)"}
            }

            fallback_file = self.config_path / "fallback_categories.json"
            with open(fallback_file, 'w') as f:
                json.dump(fallback_categories, f, indent=2)

            self.log_security_event("fallback_categories_created", {
                "categories_count": len(fallback_categories)
            })

        except Exception as e:
            self.log_security_event("fallback_categories_failed", {"error": str(e)}, "ERROR")

    def test_installation(self):
        """Test the installation"""
        # Test server connection
        try:
            self.log_security_event("connection_test_started", {"server_url": self.server_url})
            response = requests.get(f"{self.server_url}/", timeout=5)

            # Log API operation
            self.log_api_operation("health_check", f"{self.server_url}/", response.status_code)

            # Check for authentication issues
            if self.monitor_failed_auth(response):
                raise Exception("Authentication failed - check API key")

            if not response.ok:
                self.log_security_event("connection_test_failed", {
                    "status_code": response.status_code,
                    "response_text": response.text[:200]
                }, "ERROR")
                raise Exception("Server connection failed")

            self.log_security_event("connection_test_success", {"status_code": response.status_code})

        except Exception as e:
            self.log_security_event("connection_test_error", {"error": str(e)}, "ERROR")
            raise Exception("Cannot connect to sync server")


class ActivityWatchSync:
    """Handles syncing data to the server"""

    def __init__(self):
        config_path = Path(os.environ['APPDATA']) / 'ActivityWatch-Team' / 'sync_config.json'

        if not config_path.exists():
            print(f"[ERROR] Configuration file not found at {config_path}")
            raise FileNotFoundError(f"sync_config.json not found at {config_path}")

        with open(config_path) as f:
            self.config = json.load(f)

        print(f"[INFO] Loaded config for user: {self.config.get('user_info', {}).get('email', 'unknown')}")

        # Initialize audit logging for sync operations
        self.setup_sync_audit_logging()
        self.session_id = str(uuid.uuid4())
        self.security_alerter = SecurityAlerter()
        self.log_sync_event("sync_service_started")

    def setup_sync_audit_logging(self):
        """Initialize audit logging for sync operations"""
        config_path = Path(os.environ['APPDATA']) / 'ActivityWatch-Team'
        self.audit_path = config_path / 'audit'
        self.audit_path.mkdir(parents=True, exist_ok=True)

        # Setup sync audit logger
        self.sync_logger = logging.getLogger('activitywatch_sync_audit')
        self.sync_logger.setLevel(logging.INFO)

        # Create sync log file
        log_file = self.audit_path / f'sync_audit_{datetime.now().strftime("%Y%m%d")}.log'

        # File handler for sync logs
        handler = logging.FileHandler(log_file, encoding='utf-8')
        formatter = logging.Formatter(
            '%(asctime)s|%(levelname)s|%(message)s',
            datefmt='%Y-%m-%d %H:%M:%S UTC'
        )
        handler.setFormatter(formatter)
        self.sync_logger.addHandler(handler)

    def log_sync_event(self, event_type, details=None, level="INFO"):
        """Log sync-related security events"""
        if details is None:
            details = {}

        # Add sync context
        event_data = {
            "session_id": self.session_id,
            "event_type": event_type,
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "user_id": os.environ.get('USERNAME', 'unknown'),
            "hostname": os.environ.get('COMPUTERNAME', 'unknown'),
            **details
        }

        # Create structured log entry
        log_message = "|".join([
            f"SYNC_EVENT:{event_type}",
            f"SESSION:{self.session_id}",
            f"USER:{event_data['user_id']}",
            f"HOST:{event_data['hostname']}",
            f"DATA:{str(details)}"
        ])

        # Log based on severity
        if level == "ERROR":
            self.sync_logger.error(log_message)
        elif level == "WARN":
            self.sync_logger.warning(log_message)
        else:
            self.sync_logger.info(log_message)

    def sync_data(self):
        """Sync ActivityWatch data to server"""
        sync_start_time = datetime.now(timezone.utc)
        self.log_sync_event("sync_started", {"start_time": sync_start_time.isoformat()})

        try:
            # Get ActivityWatch data
            self.log_sync_event("fetching_local_data")
            response = requests.get("http://localhost:5600/api/0/buckets", timeout=10)

            if not response.ok:
                self.log_sync_event("local_aw_unavailable", {
                    "status_code": response.status_code,
                    "response_text": response.text[:200]
                }, "WARN")
                print("ActivityWatch not running")
                return

            buckets = response.json()
            all_events = []
            bucket_count = len(buckets)

            self.log_sync_event("processing_buckets", {"bucket_count": bucket_count})

            for bucket_id in buckets:
                try:
                    events_response = requests.get(
                        f"http://localhost:5600/api/0/buckets/{bucket_id}/events?limit=50",
                        timeout=10
                    )
                    if events_response.ok:
                        events = events_response.json()

                        for event in events:
                            event_data = {
                                'event_id': event.get('id', f"{bucket_id}_{len(all_events)}"),
                                'timestamp': event.get('timestamp'),
                                'duration': event.get('duration', 0),
                                'application': event.get('data', {}).get('app', 'Unknown'),
                                'window_title': event.get('data', {}).get('title', ''),
                                'hostname': event.get('data', {}).get('hostname', 'unknown'),
                                'metadata': event.get('data', {})
                            }
                            all_events.append(event_data)
                    else:
                        self.log_sync_event("bucket_fetch_failed", {
                            "bucket_id": bucket_id,
                            "status_code": events_response.status_code
                        }, "WARN")
                except Exception as e:
                    self.log_sync_event("bucket_processing_error", {
                        "bucket_id": bucket_id,
                        "error": str(e)
                    }, "ERROR")
                    continue

            event_count = len(all_events)
            self.log_sync_event("data_collection_complete", {
                "total_events": event_count,
                "bucket_count": bucket_count
            })

            if all_events:
                # Write last sync attempt timestamp
                status_file = Path(os.environ['APPDATA']) / 'ActivityWatch-Team' / 'last_sync_status.json'
                status_file.parent.mkdir(parents=True, exist_ok=True)

                # Send to server with API key authentication
                api_key = self.config.get('api_key', 'aw-team-2025-secure-key-v1')
                headers = {
                    'Content-Type': 'application/json',
                    'X-API-Key': api_key
                }

                sync_payload = {
                    'user_email': self.config['user_info']['email'],
                    'events': all_events
                }

                self.log_sync_event("sync_upload_started", {
                    "server_url": self.config['sync_server_url'],
                    "user_email": self.config['user_info']['email'],
                    "event_count": event_count,
                    "api_key_hash": hashlib.sha256(api_key.encode()).hexdigest()[:8]
                })

                print(f"[INFO] Sending {event_count} events to server for {self.config['user_info']['email']}")
                sync_response = requests.post(
                    f"{self.config['sync_server_url']}/api/sync",
                    json=sync_payload,
                    headers=headers,
                    timeout=30
                )

                # Monitor authentication and log response
                if sync_response.status_code == 401:
                    api_key_hash = hashlib.sha256(api_key.encode()).hexdigest()[:8]
                    self.log_sync_event("sync_auth_failed", {
                        "status_code": sync_response.status_code,
                        "response_text": sync_response.text[:200],
                        "api_key_hash": api_key_hash
                    }, "ERROR")

                    # Send authentication failure alert
                    self.security_alerter.alert_auth_failure(
                        user_id=os.environ.get('USERNAME', 'unknown'),
                        hostname=os.environ.get('COMPUTERNAME', 'unknown'),
                        api_key_hash=api_key_hash,
                        response_text=sync_response.text
                    )
                elif sync_response.status_code == 403:
                    self.log_sync_event("sync_forbidden", {
                        "status_code": sync_response.status_code,
                        "response_text": sync_response.text[:200],
                        "user_email": self.config['user_info']['email']
                    }, "ERROR")
                    print(f"[ERROR] Access forbidden for {self.config['user_info']['email']} - check domain authorization")
                elif sync_response.ok:
                    sync_duration = (datetime.now(timezone.utc) - sync_start_time).total_seconds()
                    self.log_sync_event("sync_success", {
                        "status_code": sync_response.status_code,
                        "events_synced": event_count,
                        "duration_seconds": sync_duration,
                        "response_size": len(sync_response.text)
                    })
                    print(f"[SUCCESS] Synced {len(all_events)} events successfully to BigQuery")

                    # Write successful sync status
                    sync_status = {
                        "last_sync_time": datetime.now().isoformat(),
                        "status": "success",
                        "events_synced": len(all_events),
                        "user_email": self.config['user_info']['email'],
                        "next_sync": (datetime.now() + timedelta(minutes=30)).isoformat()
                    }
                    with open(status_file, 'w') as f:
                        json.dump(sync_status, f, indent=2)

                    # Sync categories (check for updates)
                    self.sync_categories()
                else:
                    self.log_sync_event("sync_failed", {
                        "status_code": sync_response.status_code,
                        "response_text": sync_response.text[:200],
                        "events_attempted": event_count
                    }, "ERROR")

                    # Write failed sync status
                    sync_status = {
                        "last_sync_time": datetime.now().isoformat(),
                        "status": "failed",
                        "error": f"HTTP {sync_response.status_code}: {sync_response.text[:200]}",
                        "events_attempted": len(all_events),
                        "user_email": self.config['user_info']['email'],
                        "next_sync": (datetime.now() + timedelta(minutes=30)).isoformat()
                    }
                    with open(status_file, 'w') as f:
                        json.dump(sync_status, f, indent=2)

                    # Send sync failure alert
                    self.security_alerter.alert_sync_failure(
                        user_id=os.environ.get('USERNAME', 'unknown'),
                        hostname=os.environ.get('COMPUTERNAME', 'unknown'),
                        error_message=sync_response.text[:200],
                        event_count=event_count
                    )
                    print(f"Sync failed: {sync_response.text}")
            else:
                self.log_sync_event("no_events_to_sync")
                print("No events to sync")

        except Exception as e:
            sync_duration = (datetime.now(timezone.utc) - sync_start_time).total_seconds()
            self.log_sync_event("sync_exception", {
                "error": str(e),
                "error_type": type(e).__name__,
                "duration_seconds": sync_duration
            }, "ERROR")
            print(f"Sync error: {e}")

    def sync_categories(self):
        """Sync team categories from server"""
        try:
            self.log_sync_event("category_sync_started")

            # Get user email from config
            user_email = self.config.get('user_email')
            api_key = self.config.get('api_key')
            server_url = self.config.get('server_url', 'https://activitywatch-sync-server-1051608384208.us-central1.run.app')

            if not user_email or not api_key:
                self.log_sync_event("category_sync_failed", {
                    "error": "Missing user_email or api_key in config"
                }, "WARN")
                return

            # Fetch categories from server
            headers = {'Content-Type': 'application/json', 'X-API-Key': api_key}
            params = {'email': user_email}

            self.log_sync_event("fetching_categories", {"user_email": user_email})

            response = requests.get(
                f"{server_url}/api/categories",
                headers=headers,
                params=params,
                timeout=10
            )

            if response.status_code == 200:
                categories_response = response.json()
                categories = categories_response.get('categories', [])
                team_id = categories_response.get('team_id', 'unknown')

                self.log_sync_event("categories_received", {
                    "team_id": team_id,
                    "category_count": len(categories)
                })

                # Check if categories have changed by comparing with cached version
                categories_cache_path = Path(os.environ['APPDATA']) / 'ActivityWatch-Team' / 'categories_cache.json'

                # Load cached categories if they exist
                cached_categories = {}
                if categories_cache_path.exists():
                    try:
                        with open(categories_cache_path, 'r') as f:
                            cached_categories = json.load(f)
                    except Exception as e:
                        self.log_sync_event("cache_read_failed", {"error": str(e)}, "WARN")

                # Compare current categories with cached ones
                current_categories = {cat['category_id']: cat for cat in categories}

                if current_categories != cached_categories:
                    self.log_sync_event("categories_changed", {
                        "cached_count": len(cached_categories),
                        "current_count": len(current_categories)
                    })

                    # Apply updated categories to ActivityWatch
                    self.apply_categories_to_activitywatch_sync(categories)

                    # Update cache
                    try:
                        categories_cache_path.parent.mkdir(parents=True, exist_ok=True)
                        with open(categories_cache_path, 'w') as f:
                            json.dump(current_categories, f, indent=2)

                        self.log_sync_event("categories_cached")
                    except Exception as e:
                        self.log_sync_event("cache_write_failed", {"error": str(e)}, "WARN")
                else:
                    self.log_sync_event("categories_unchanged")

            elif response.status_code == 403:
                self.log_sync_event("category_sync_unauthorized", {
                    "status_code": response.status_code,
                    "user_email": user_email
                }, "ERROR")
            else:
                self.log_sync_event("category_sync_failed", {
                    "status_code": response.status_code,
                    "response_text": response.text[:200]
                }, "ERROR")

        except Exception as e:
            self.log_sync_event("category_sync_exception", {
                "error": str(e),
                "error_type": type(e).__name__
            }, "ERROR")
            print(f"Category sync error: {e}")

    def apply_categories_to_activitywatch(self, categories):
        """Apply categories to ActivityWatch configuration"""
        try:
            self.log_sync_event("applying_categories", {"category_count": len(categories)})

            # Get ActivityWatch config directory
            aw_config_dir = Path.home() / '.config' / 'activitywatch'

            # Check Windows path if Linux path doesn't exist
            if not aw_config_dir.exists():
                aw_config_dir = Path(os.environ.get('APPDATA', '')) / 'activitywatch'

            if not aw_config_dir.exists():
                self.log_sync_event("aw_config_not_found", {"searched_path": str(aw_config_dir)}, "WARN")
                return

            # Prepare categories in ActivityWatch format
            aw_categories = {}

            for category in categories:
                category_name = category['category_name']

                # Build regex pattern from rules
                regex_patterns = []
                for rule in category.get('rules', []):
                    regex_patterns.append(rule['rule_regex'])

                if regex_patterns:
                    # Combine all patterns with OR operator
                    combined_regex = '|'.join(f"({pattern})" for pattern in regex_patterns)

                    aw_categories[category_name] = {
                        "name": category_name,
                        "rule": {
                            "type": "regex",
                            "regex": combined_regex
                        }
                    }

            # Write categories to ActivityWatch-Team config
            team_config_dir = Path(os.environ['APPDATA']) / 'ActivityWatch-Team'
            team_config_dir.mkdir(parents=True, exist_ok=True)

            categories_file = team_config_dir / 'bali_love_categories_import.json'

            with open(categories_file, 'w') as f:
                json.dump(aw_categories, f, indent=2)

            self.log_sync_event("categories_applied", {
                "categories_file": str(categories_file),
                "applied_count": len(aw_categories)
            })

            print(f"Updated {len(aw_categories)} categories from server")

        except Exception as e:
            self.log_sync_event("apply_categories_failed", {
                "error": str(e),
                "error_type": type(e).__name__
            }, "ERROR")
            print(f"Failed to apply categories: {e}")

    def apply_categories_to_activitywatch_sync(self, categories):
        """Apply categories to ActivityWatch during sync"""
        try:
            self.log_sync_event("applying_categories", {"category_count": len(categories)})

            # Convert to ActivityWatch format
            aw_categories = {}
            for category in categories:
                category_name = category.get('category_name', '')
                rules = category.get('rules', [])

                if rules and category_name:
                    # Combine all regex patterns with OR
                    regex_patterns = []
                    for rule in rules:
                        regex = rule.get('rule_regex', '')
                        if regex:
                            regex_patterns.append(f"({regex})")

                    if regex_patterns:
                        combined_regex = '|'.join(regex_patterns)
                        aw_categories[category_name] = {
                            'name': category_name,
                            'rule': {
                                'type': 'regex',
                                'regex': combined_regex
                            }
                        }

            if aw_categories:
                # Try to inject directly into ActivityWatch
                try:
                    # Check if ActivityWatch is running
                    response = requests.get("http://localhost:5600/api/0/buckets", timeout=2)
                    if response.ok:
                        # Try to inject categories via settings API
                        self.inject_categories_via_api(aw_categories)
                    else:
                        self.log_sync_event("aw_not_running", {}, "WARN")
                except requests.exceptions.RequestException:
                    self.log_sync_event("aw_connection_failed", {}, "WARN")

                # Always save to file as backup
                team_config_dir = Path(os.environ['APPDATA']) / 'ActivityWatch-Team'
                team_config_dir.mkdir(parents=True, exist_ok=True)
                categories_file = team_config_dir / 'bali_love_categories_import.json'

                with open(categories_file, 'w') as f:
                    json.dump(aw_categories, f, indent=2)

                self.log_sync_event("categories_applied", {
                    "categories_file": str(categories_file),
                    "applied_count": len(aw_categories)
                })

        except Exception as e:
            self.log_sync_event("apply_categories_failed", {
                "error": str(e),
                "error_type": type(e).__name__
            }, "ERROR")

    def inject_categories_via_api(self, categories):
        """Inject categories directly into ActivityWatch via API"""
        try:
            categories_url = "http://localhost:5600/api/0/settings/categories"

            # Post categories directly to the correct endpoint
            response = requests.post(categories_url, json=categories, timeout=3)

            if response.ok:
                self.log_sync_event("categories_injected_via_api", {
                    "categories_injected": len(categories),
                    "endpoint": categories_url
                })

                # Verify injection worked
                verify_response = requests.get(categories_url, timeout=3)
                if verify_response.ok:
                    verified_count = len(verify_response.json()) if verify_response.json() else 0
                    self.log_sync_event("categories_verified", {"verified_count": verified_count})

            else:
                self.log_sync_event("api_injection_failed", {
                    "status_code": response.status_code,
                    "response": response.text[:200]
                }, "WARN")

        except Exception as e:
            self.log_sync_event("api_injection_failed", {"error": str(e)}, "WARN")


def main():
    """Main entry point"""
    if len(sys.argv) > 1 and sys.argv[1] == '--sync':
        # Running as sync service - no GUI needed
        print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Starting sync service...")
        try:
            # Check if config exists
            config_path = Path(os.environ['APPDATA']) / 'ActivityWatch-Team' / 'sync_config.json'
            if not config_path.exists():
                print(f"[ERROR] Configuration file not found at {config_path}")
                sys.exit(1)

            # Run sync
            syncer = ActivityWatchSync()
            syncer.sync_data()
            print(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Sync completed")
        except Exception as e:
            print(f"[ERROR] Sync failed: {e}")
            # Log to file for debugging
            error_log = Path(os.environ['APPDATA']) / 'ActivityWatch-Team' / 'sync_errors.log'
            error_log.parent.mkdir(parents=True, exist_ok=True)
            with open(error_log, 'a') as f:
                f.write(f"{datetime.now().isoformat()} - Sync error: {e}\n")
            sys.exit(1)
    else:
        # Running as installer
        app = ActivityWatchInstaller()
        app.root.mainloop()


if __name__ == "__main__":
    main()