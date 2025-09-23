# Windows Installer Behavior Reference

## Actual Working Implementation

This documents the **exact behavior** of our working Windows installer for the freelancer to replicate on macOS.

### Installation Process

1. **User Prompts**:
   - Email address (validates `@bali.love` domain)
   - Full name (optional)
   - Team/Department (optional)

2. **File Installation**:
   - Downloads ActivityWatch to `%APPDATA%/ActivityWatch-Team/`
   - Creates sync client in same directory
   - Generates `sync_config.json` with user details

3. **Service Setup**:
   - Creates Windows scheduled task: `ActivityWatch-Team-Sync-Periodic`
   - Runs every 10 minutes: `/sc minute /mo 10`
   - Starts ActivityWatch on login
   - Auto-starts sync service

### Configuration Generated

```json
{
  "sync_server_url": "https://activitywatch-sync-server-1051608384208.us-central1.run.app",
  "api_key": "aw-team-2025-secure-key-v1",
  "sync_interval_minutes": 10,
  "user_info": {
    "email": "aldo@bali.love",
    "full_name": "Aldo Bali",
    "team": "Engineering",
    "department": "Development"
  },
  "privacy": {
    "encrypt_window_titles": true,
    "exclude_keywords": ["password", "private", "secret"],
    "work_hours_only": false,
    "excluded_apps": ["1Password", "KeePass"]
  }
}
```

### Runtime Behavior

**Every 10 Minutes**:
1. Sync client queries local ActivityWatch database
2. Collects events from last sync timestamp
3. Formats data according to `successful_sync_example.json`
4. Sends POST request to Cloud Run server
5. Logs sync status to local file

**User Experience**:
- ✅ No visible popups or interruptions
- ✅ Runs silently in background
- ✅ ActivityWatch web interface accessible at `localhost:5600`
- ✅ System tray icon shows ActivityWatch is active

### Data Collection Points

**Applications Tracked**:
- All desktop applications (window titles, durations)
- Web browsers (URLs, page titles, tab counts)
- Development tools (VS Code, terminals, IDEs)

**Metadata Structure** (as sent to server):
```json
{
  "bucket": "aw-watcher-window_HOSTNAME",
  "original_id": "activitywatch_event_id",
  "afk_status": "not-afk",
  "url": "https://example.com",
  "tab_count": 3,
  "audible": false,
  "incognito": false,
  "raw": ""
}
```

### Privacy Implementation

**Automatic Filtering**:
- Window titles containing: "password", "login", "banking", "private"
- URLs with: "login", "auth", "password", "bank"
- Applications: "1Password", "KeePass"
- Browser incognito/private mode sessions

**Data Encryption**:
- Sensitive window titles → `[PRIVATE_CONTENT]`
- Sensitive URLs → `[PRIVATE_URL]`
- `is_sensitive: true` flag set

### Network Communication

**Sync Request**:
```bash
curl -X POST https://activitywatch-sync-server-1051608384208.us-central1.run.app/api/sync \
  -H "Content-Type: application/json" \
  -H "X-API-Key: aw-team-2025-secure-key-v1" \
  -d @event_data.json
```

**Success Response**:
```json
{
  "status": "success",
  "events_processed": 151,
  "events_received": 151,
  "user_email": "aldo@bali.love",
  "timestamp": "2025-09-23T06:42:38.958440"
}
```

### Error Handling

**Common Scenarios**:
- Network timeout → Retry 3 times with backoff
- Authentication error → Log error, continue trying
- Server error → Queue events for next sync
- No new events → Send empty sync (heartbeat)

**Logging Location**:
- Windows: `%APPDATA%/ActivityWatch-Team/logs/sync.log`
- macOS equivalent: `~/Library/Application Support/ActivityWatch-Team/logs/sync.log`

### Startup Integration

**Windows Implementation**:
- Scheduled task runs at login
- ActivityWatch auto-starts via registry entry
- Sync begins 2 minutes after login

**macOS Target**:
- LaunchAgent plist file for auto-start
- ActivityWatch in Applications folder
- Sync daemon starts with system

### Verification Commands

**For User Validation**:
```bash
# Check if sync is working (Windows)
schtasks /query /tn "ActivityWatch-Team-Sync-Periodic"

# macOS equivalent needed
launchctl list | grep activitywatch
```

### Performance Metrics

**Current Windows Results**:
- Installation time: ~2 minutes
- Memory usage: ~50MB total
- CPU usage: <1% during sync
- Network: ~100KB per sync (150 events)
- Battery impact: Negligible

**Target macOS Performance**:
- Similar resource usage
- Battery-efficient background operation
- Native macOS integration