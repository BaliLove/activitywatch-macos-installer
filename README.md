# macOS ActivityWatch Installer - Freelancer Handover

## Project Overview
Create a macOS installer for ActivityWatch team deployment system that syncs activity data to BigQuery.

## What You Need to Build
A **macOS app installer** equivalent to the Windows `.exe` file that:
1. Installs ActivityWatch on macOS
2. Sets up automatic sync to our Cloud Run server
3. Configures privacy settings and team authentication

## Working Windows Reference
- **Windows Installer**: `ActivityWatch-Standalone-EXE/ActivityWatch-Team-Installer.exe` (3.9MB)
- **Status**: ✅ Fully operational and tested
- **Server**: `https://activitywatch-sync-server-1051608384208.us-central1.run.app`

## Key Requirements

### 1. Core Installation
- Install ActivityWatch application for macOS
- Set up sync client that runs every 10 minutes
- Configure automatic startup on login

### 2. Authentication & Configuration
- **API Key**: `aw-team-2025-secure-key-v1` (hardcoded)
- **Server URL**: `https://activitywatch-sync-server-1051608384208.us-central1.run.app`
- **User Email**: Prompt during installation
- **Sync Interval**: 10 minutes

### 3. Privacy Settings
- Encrypt window titles containing sensitive keywords
- Filter out private browsing sessions
- Exclude password managers and banking apps
- Work hours tracking optional

## Technical Details

### Server API
- **Endpoint**: `POST /api/sync`
- **Headers**: `X-API-Key: aw-team-2025-secure-key-v1`
- **Content-Type**: `application/json`
- **Payload**: See `sync_data_format.json` for structure

### Data Structure
Events sent to server must include:
```json
{
  "user_email": "user@bali.love",
  "events": [
    {
      "event_id": "unique_id",
      "timestamp": "2025-09-23T06:00:00Z",
      "duration": 300.0,
      "application": "Safari",
      "window_title": "Document Title",
      "hostname": "MacBook-Pro",
      "metadata": {
        "bucket": "aw-watcher-window_MacBook-Pro",
        "original_id": "event_123",
        "afk_status": "not-afk",
        "url": "https://example.com",
        "tab_count": 3,
        "audible": false,
        "incognito": false
      }
    }
  ]
}
```

## Deliverables
1. **macOS App Bundle** (`.app` file)
2. **DMG Installer** for easy distribution
3. **Installation Instructions** for team members
4. **Source Code** for future maintenance

## Testing Requirements
- Test on macOS Monterey, Ventura, and Sonoma
- Verify sync functionality with our production server
- Confirm data appears in BigQuery after installation
- Test privacy filtering works correctly

## Budget & Timeline
- **Budget**: [To be discussed]
- **Timeline**: [To be agreed]
- **Milestones**: Alpha version → Beta testing → Final release

## Support During Development
- Server access and credentials provided
- Technical support for API integration
- BigQuery schema documentation available
- Testing environment access

## Files Included in This Handover
- `activitywatch_installer_reference.py` - Windows installer logic
- `sync_client_reference.py` - Sync functionality
- `config_template.json` - Configuration structure
- `sync_data_format.json` - API payload format
- `privacy_settings.json` - Privacy configuration
- `TESTING_GUIDE.md` - How to test the installer

---
**Contact**: For questions during development, please reach out with specific technical details.