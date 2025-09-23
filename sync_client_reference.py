"""
ActivityWatch to BigQuery Sync Module
Syncs local ActivityWatch data to BigQuery for team analytics
"""

import json
import time
import uuid
import hashlib
import platform
import getpass
import re
from datetime import datetime, timedelta
from typing import List, Dict, Optional
from pathlib import Path

from google.cloud import bigquery
from google.oauth2 import service_account
from cryptography.fernet import Fernet
import requests


class ActivityWatchBigQuerySync:
    """Handles syncing ActivityWatch data to BigQuery"""

    def __init__(self, config_path: str = "sync_config.json"):
        self.config = self.load_config(config_path)
        self.bq_client = self.init_bigquery()
        self.cipher = self.init_encryption()
        self.user_id = self.get_user_id()
        self.last_sync_time = self.get_last_sync_time()
        self.aw_base_url = self.config.get("activitywatch_url", "http://localhost:5600")

    def load_config(self, path: str) -> Dict:
        """Load configuration from JSON file"""
        config_file = Path(path)
        if not config_file.exists():
            # Create default config
            default_config = {
                "project_id": "bali-love-data",
                "dataset_id": "activitywatch_pilot",
                "service_account_path": "bali-love-data-32918425ecf5.json",
                "activitywatch_url": "http://localhost:5600",
                "sync_interval_minutes": 30,
                "batch_size": 1000,
                "encryption_key": Fernet.generate_key().decode(),
                "privacy": {
                    "encrypt_window_titles": True,
                    "exclude_keywords": ["password", "private", "secret"],
                    "work_hours_only": True,
                    "work_hours": {"start": "09:00", "end": "18:00"},
                    "excluded_apps": ["1Password", "KeePass", "Banking"]
                },
                "user_info": {
                    "email": "",
                    "team": "",
                    "department": ""
                }
            }
            with open(path, 'w') as f:
                json.dump(default_config, f, indent=2)
            print(f"Created default config at {path}")
            print("Please update the config with your information and run again.")
            exit(1)

        with open(path, 'r') as f:
            return json.load(f)

    def init_bigquery(self) -> bigquery.Client:
        """Initialize BigQuery client"""
        credentials = service_account.Credentials.from_service_account_file(
            self.config["service_account_path"]
        )
        return bigquery.Client(
            credentials=credentials,
            project=self.config["project_id"]
        )

    def init_encryption(self) -> Fernet:
        """Initialize encryption handler"""
        key = self.config.get("encryption_key")
        if not key:
            key = Fernet.generate_key().decode()
            self.config["encryption_key"] = key
            self.save_config()
        return Fernet(key.encode())

    def save_config(self):
        """Save configuration back to file"""
        with open("sync_config.json", 'w') as f:
            json.dump(self.config, f, indent=2)

    def get_user_id(self) -> str:
        """Generate or retrieve unique user ID"""
        # Create user ID based on hostname + username
        hostname = platform.node()
        username = getpass.getuser()
        user_string = f"{hostname}_{username}"
        user_id = hashlib.sha256(user_string.encode()).hexdigest()[:16]
        return user_id

    def get_last_sync_time(self) -> Optional[datetime]:
        """Get the last sync time from BigQuery"""
        query = """
        SELECT MAX(sync_timestamp) as last_sync
        FROM `{}.{}.sync_logs`
        WHERE user_id = @user_id
        AND success = TRUE
        """.format(self.config['project_id'], self.config['dataset_id'])

        job_config = bigquery.QueryJobConfig(
            query_parameters=[
                bigquery.ScalarQueryParameter("user_id", "STRING", self.user_id)
            ]
        )

        try:
            result = self.bq_client.query(query, job_config=job_config).result()
            for row in result:
                if row.last_sync:
                    return row.last_sync
        except Exception as e:
            print(f"Could not get last sync time: {e}")
        return None

    def encrypt_sensitive_data(self, data: str) -> str:
        """Encrypt sensitive data"""
        if not data:
            return data
        return self.cipher.encrypt(data.encode()).decode()

    def should_exclude_window(self, window_title: str) -> bool:
        """Check if window should be excluded based on privacy settings"""
        if not window_title:
            return False

        exclude_keywords = self.config["privacy"].get("exclude_keywords", [])
        for keyword in exclude_keywords:
            if keyword.lower() in window_title.lower():
                return True
        return False

    def is_work_hours(self) -> bool:
        """Check if current time is within work hours"""
        if not self.config["privacy"].get("work_hours_only", False):
            return True

        now = datetime.now()
        work_hours = self.config["privacy"]["work_hours"]
        start_hour = datetime.strptime(work_hours["start"], "%H:%M").time()
        end_hour = datetime.strptime(work_hours["end"], "%H:%M").time()

        return start_hour <= now.time() <= end_hour

    def fetch_activitywatch_data(self, bucket_name: str, start_time: datetime, end_time: datetime) -> List[Dict]:
        """Fetch data from ActivityWatch API"""
        try:
            # Get events from ActivityWatch
            url = f"{self.aw_base_url}/api/0/buckets/{bucket_name}/events"
            params = {
                "start": start_time.isoformat(),
                "end": end_time.isoformat(),
                "limit": self.config.get("batch_size", 1000)
            }

            response = requests.get(url, params=params)
            response.raise_for_status()

            return response.json()

        except Exception as e:
            print(f"Error fetching ActivityWatch data: {e}")
            return []

    def get_activitywatch_buckets(self) -> List[str]:
        """Get list of available ActivityWatch buckets"""
        try:
            url = f"{self.aw_base_url}/api/0/buckets/"
            response = requests.get(url)
            response.raise_for_status()
            buckets = response.json()
            return list(buckets.keys())
        except Exception as e:
            print(f"Error getting buckets: {e}")
            return []

    def transform_event(self, event: Dict, bucket_type: str) -> Dict:
        """Transform ActivityWatch event to BigQuery format"""
        # Generate unique event ID
        event_id = f"{self.user_id}_{uuid.uuid4().hex[:8]}_{int(time.time())}"

        # Extract data from event
        data = event.get("data", {})
        app = data.get("app", "Unknown")
        title = data.get("title", "")
        url = data.get("url", "")

        # Handle browser data specifically
        if bucket_type and "web" in bucket_type:
            app = "Browser"
            # Use URL for categorization instead of app name
            category = self.categorize_website(url, title)
            # For browser events, check URL privacy
            if self.should_exclude_url(url, title):
                return None
        else:
            # Regular application event
            if self.should_exclude_window(title):
                return None
            category = self.categorize_application(app)

        # Check if app is excluded
        excluded_apps = self.config["privacy"].get("excluded_apps", [])
        if app in excluded_apps:
            return None

        # Encrypt sensitive data if configured
        if self.config["privacy"].get("encrypt_window_titles", True):
            if title and self.is_sensitive_data(title):
                title = self.encrypt_sensitive_data(title)
            if url and self.is_sensitive_data(url):
                url = self.encrypt_sensitive_data(url)

        # Build BigQuery row
        bq_event = {
            "event_id": event_id,
            "user_id": self.user_id,
            "timestamp": event.get("timestamp"),
            "duration": event.get("duration", 0),
            "application": app,
            "window_title": title,
            "category": category,
            "project_tag": data.get("project", ""),
            "is_productive": self.is_productive_activity(app, category, url),
            "hostname": platform.node(),
            "metadata": {
                "bucket": bucket_type,
                "original_id": event.get("id", ""),
                "afk_status": data.get("status", ""),
                "url": url,
                "tab_count": data.get("tabCount", 0),
                "audible": data.get("audible", False),
                "incognito": data.get("incognito", False)
            }
        }

        return bq_event

    def categorize_application(self, app_name: str) -> str:
        """Categorize application for reporting"""
        categories = {
            "Development": ["code", "visual studio", "vscode", "pycharm", "intellij", "sublime", "atom", "vim"],
            "Communication": ["slack", "teams", "discord", "zoom", "skype", "outlook", "gmail"],
            "Browser": ["chrome", "firefox", "edge", "safari", "brave"],
            "Documentation": ["word", "docs", "notion", "obsidian", "onenote"],
            "Spreadsheet": ["excel", "sheets", "calc"],
            "Design": ["figma", "photoshop", "illustrator", "sketch"],
            "Terminal": ["terminal", "powershell", "cmd", "iterm"],
            "Entertainment": ["youtube", "netflix", "spotify", "steam"],
        }

        app_lower = app_name.lower()
        for category, keywords in categories.items():
            for keyword in keywords:
                if keyword in app_lower:
                    return category

        return "Other"

    def categorize_website(self, url: str, title: str = "") -> str:
        """Categorize website based on URL and title"""
        if not url:
            return "Other"

        # Extract domain from URL
        domain = self.extract_domain(url)

        # Website categories
        website_categories = {
            "Development": [
                "github.com", "gitlab.com", "bitbucket.org", "stackoverflow.com",
                "docs.python.org", "developer.mozilla.org", "w3schools.com",
                "npmjs.com", "pypi.org", "docker.com", "kubernetes.io"
            ],
            "Cloud Services": [
                "console.cloud.google.com", "aws.amazon.com", "azure.microsoft.com",
                "heroku.com", "vercel.com", "netlify.com"
            ],
            "Documentation": [
                "confluence.atlassian.com", "notion.so", "gitbook.io",
                "readthedocs.io", "wiki.", "docs."
            ],
            "Communication": [
                "slack.com", "teams.microsoft.com", "discord.com",
                "zoom.us", "meet.google.com", "webex.com"
            ],
            "Email": [
                "gmail.com", "outlook.com", "mail.google.com", "mail.yahoo.com"
            ],
            "Research": [
                "google.com", "bing.com", "duckduckgo.com", "wikipedia.org",
                "scholar.google.com", "arxiv.org"
            ],
            "Learning": [
                "coursera.org", "udemy.com", "codecademy.com", "khanacademy.org",
                "pluralsight.com", "edx.org", "youtube.com/watch"
            ],
            "Project Management": [
                "jira.atlassian.com", "trello.com", "asana.com", "monday.com",
                "basecamp.com", "linear.app"
            ],
            "Entertainment": [
                "youtube.com", "netflix.com", "twitch.tv", "reddit.com",
                "facebook.com", "instagram.com", "twitter.com", "tiktok.com"
            ],
            "News": [
                "news.ycombinator.com", "techcrunch.com", "arstechnica.com",
                "reuters.com", "bbc.com", "cnn.com"
            ]
        }

        # Check exact domain matches first
        for category, domains in website_categories.items():
            for domain_pattern in domains:
                if domain_pattern in domain:
                    return category

        # Check URL path for additional context
        url_lower = url.lower()
        if any(keyword in url_lower for keyword in ["docs", "documentation", "wiki"]):
            return "Documentation"
        elif any(keyword in url_lower for keyword in ["learn", "tutorial", "course"]):
            return "Learning"
        elif any(keyword in url_lower for keyword in ["admin", "dashboard", "console"]):
            return "Administration"

        return "Web Browsing"

    def extract_domain(self, url: str) -> str:
        """Extract domain from URL"""
        if not url:
            return ""

        # Remove protocol
        if "://" in url:
            url = url.split("://")[1]

        # Remove path and parameters
        if "/" in url:
            url = url.split("/")[0]

        # Remove port
        if ":" in url:
            url = url.split(":")[0]

        return url.lower()

    def should_exclude_url(self, url: str, title: str = "") -> bool:
        """Check if URL should be excluded based on privacy settings"""
        if not url:
            return False

        # Check sensitive URL patterns
        sensitive_patterns = [
            r"bank", r"paypal", r"secure", r"login", r"auth",
            r"password", r"account", r"billing", r"payment"
        ]

        for pattern in sensitive_patterns:
            if re.search(pattern, url, re.IGNORECASE):
                return True
            if title and re.search(pattern, title, re.IGNORECASE):
                return True

        return False

    def is_sensitive_data(self, data: str) -> bool:
        """Check if data contains sensitive information"""
        if not data:
            return False

        sensitive_keywords = self.config["privacy"].get("exclude_keywords", [])
        for keyword in sensitive_keywords:
            if keyword.lower() in data.lower():
                return True

        return False

    def is_productive_activity(self, app: str, category: str, url: str = "") -> bool:
        """Enhanced productivity determination including web activity"""
        productive_categories = [
            "Development", "Documentation", "Spreadsheet", "Design",
            "Terminal", "Cloud Services", "Learning", "Project Management"
        ]
        unproductive_categories = ["Entertainment", "Social Media"]

        if category in productive_categories:
            return True
        elif category in unproductive_categories:
            return False
        elif category == "Web Browsing" and url:
            # Additional URL-based productivity check
            productive_domains = [
                "github.com", "stackoverflow.com", "docs.", "developer.",
                "learn.", "tutorial", "course"
            ]
            for domain in productive_domains:
                if domain in url.lower():
                    return True
            return False
        else:
            # Default based on work hours
            return self.is_work_hours()

    def is_productive(self, app: str, category: str) -> bool:
        """Legacy method - redirect to enhanced version"""
        return self.is_productive_activity(app, category)

    def sync_to_bigquery(self, events: List[Dict]) -> bool:
        """Sync events to BigQuery"""
        if not events:
            print("No events to sync")
            return True

        table_id = f"{self.config['project_id']}.{self.config['dataset_id']}.events"

        try:
            table = self.bq_client.get_table(table_id)
            errors = self.bq_client.insert_rows_json(table, events)

            if errors:
                print(f"Failed to insert some rows: {errors}")
                return False

            print(f"Successfully synced {len(events)} events to BigQuery")
            return True

        except Exception as e:
            print(f"Error syncing to BigQuery: {e}")
            return False

    def log_sync(self, success: bool, events_count: int, error_message: str = None):
        """Log sync operation to BigQuery"""
        log_id = f"sync_{self.user_id}_{int(time.time())}"
        log_entry = {
            "log_id": log_id,
            "user_id": self.user_id,
            "sync_timestamp": datetime.now().isoformat(),
            "events_count": events_count,
            "success": success,
            "error_message": error_message,
            "duration_seconds": 0,  # Will be calculated
            "data_size_bytes": 0  # Will be calculated
        }

        table_id = f"{self.config['project_id']}.{self.config['dataset_id']}.sync_logs"

        try:
            table = self.bq_client.get_table(table_id)
            errors = self.bq_client.insert_rows_json(table, [log_entry])
            if errors:
                print(f"Failed to log sync: {errors}")
        except Exception as e:
            print(f"Error logging sync: {e}")

    def update_user_info(self):
        """Update user information in BigQuery"""
        user_data = {
            "user_id": self.user_id,
            "email": self.encrypt_sensitive_data(self.config["user_info"].get("email", "")),
            "full_name": self.encrypt_sensitive_data(self.config["user_info"].get("full_name", "")),
            "team": self.config["user_info"].get("team", ""),
            "department": self.config["user_info"].get("department", ""),
            "role": self.config["user_info"].get("role", ""),
            "hostname": platform.node(),
            "os_type": platform.system(),
            "activitywatch_version": "0.12.0",  # You can fetch this dynamically
            "onboarded_at": datetime.now().isoformat(),
            "last_sync": datetime.now().isoformat(),
            "is_active": True,
            "settings": self.config["privacy"]
        }

        table_id = f"{self.config['project_id']}.{self.config['dataset_id']}.users"

        try:
            # Try to update existing user first
            query = """
            UPDATE `{}`
            SET last_sync = CURRENT_TIMESTAMP()
            WHERE user_id = @user_id
            """.format(table_id)

            job_config = bigquery.QueryJobConfig(
                query_parameters=[
                    bigquery.ScalarQueryParameter("user_id", "STRING", self.user_id)
                ]
            )

            self.bq_client.query(query, job_config=job_config).result()
        except:
            # If update fails, insert new user
            try:
                table = self.bq_client.get_table(table_id)
                errors = self.bq_client.insert_rows_json(table, [user_data])
                if errors:
                    print(f"Failed to update user info: {errors}")
                else:
                    print("User info updated in BigQuery")
            except Exception as e:
                print(f"Error updating user info: {e}")

    def run_sync(self):
        """Main sync function"""
        print(f"Starting sync for user {self.user_id}")
        sync_start_time = time.time()

        # Check if within work hours
        if not self.is_work_hours() and self.config["privacy"].get("work_hours_only", False):
            print("Outside work hours, skipping sync")
            return

        # Get sync time range
        end_time = datetime.now()
        if self.last_sync_time:
            start_time = self.last_sync_time
        else:
            # First sync - get last 24 hours
            start_time = end_time - timedelta(hours=24)

        print(f"Syncing data from {start_time} to {end_time}")

        # Get available buckets
        buckets = self.get_activitywatch_buckets()
        print(f"Found {len(buckets)} ActivityWatch buckets")

        all_events = []

        # Fetch and transform events from each bucket
        for bucket in buckets:
            print(f"Processing bucket: {bucket}")
            events = self.fetch_activitywatch_data(bucket, start_time, end_time)

            for event in events:
                transformed = self.transform_event(event, bucket)
                if transformed:
                    all_events.append(transformed)

        print(f"Collected {len(all_events)} events for sync")

        # Sync to BigQuery
        success = False
        error_message = None

        if all_events:
            success = self.sync_to_bigquery(all_events)
        else:
            success = True  # No events is still a successful sync

        # Log sync operation
        self.log_sync(success, len(all_events), error_message)

        # Update user info
        self.update_user_info()

        duration = time.time() - sync_start_time
        print(f"Sync completed in {duration:.2f} seconds")

    def run_continuous_sync(self):
        """Run continuous sync at specified intervals"""
        interval_minutes = self.config.get("sync_interval_minutes", 30)
        print(f"Starting continuous sync every {interval_minutes} minutes")

        while True:
            try:
                self.run_sync()
            except Exception as e:
                print(f"Sync error: {e}")

            # Wait for next sync
            print(f"Next sync in {interval_minutes} minutes...")
            time.sleep(interval_minutes * 60)


def main():
    """Main entry point"""
    print("=" * 50)
    print("ActivityWatch BigQuery Sync")
    print("=" * 50)

    sync = ActivityWatchBigQuerySync()

    # Check if ActivityWatch is running
    try:
        buckets = sync.get_activitywatch_buckets()
        if not buckets:
            print("No ActivityWatch buckets found. Is ActivityWatch running?")
            print("Please start ActivityWatch and try again.")
            return
    except:
        print("Cannot connect to ActivityWatch at http://localhost:5600")
        print("Please ensure ActivityWatch is running and try again.")
        return

    print(f"User ID: {sync.user_id}")
    print(f"Project: {sync.config['project_id']}")
    print(f"Dataset: {sync.config['dataset_id']}")
    print("")

    # Run once or continuous
    import sys
    if len(sys.argv) > 1 and sys.argv[1] == "--continuous":
        sync.run_continuous_sync()
    else:
        sync.run_sync()
        print("\nTo run continuous sync, use: python activitywatch_bigquery_sync.py --continuous")


if __name__ == "__main__":
    main()