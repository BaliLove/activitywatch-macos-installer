# Production Server Information

## Server Details
- **URL**: `https://activitywatch-sync-server-1051608384208.us-central1.run.app`
- **Status**: ✅ **LIVE and OPERATIONAL**
- **Platform**: Google Cloud Run
- **Region**: us-central1

## Authentication
- **API Key**: `aw-team-2025-secure-key-v1`
- **Method**: HTTP Header `X-API-Key`
- **User Domain**: `@bali.love` (authorized domain)

## API Endpoints

### Health Check
```
GET /
Response: {"status": "healthy", "service": "ActivityWatch Sync Server", "version": "1.0.0"}
```

### Data Sync
```
POST /api/sync
Headers:
  - Content-Type: application/json
  - X-API-Key: aw-team-2025-secure-key-v1
Body: See sync_data_format.json
```

### User Status
```
GET /api/status/{user_email}
Headers: X-API-Key: aw-team-2025-secure-key-v1
Response: User activity statistics
```

## Data Storage
- **Platform**: Google BigQuery
- **Project**: `bali-love-data`
- **Dataset**: `activitywatch_pilot`
- **Table**: `events`

## Server Features
- ✅ Rate limiting (20 requests per 10 minutes)
- ✅ Privacy filtering (sensitive content detection)
- ✅ Data validation and sanitization
- ✅ Automatic categorization
- ✅ Error handling and logging

## Monitoring
Server logs can be monitored with:
```bash
gcloud logging read "resource.type=cloud_run_revision AND resource.labels.service_name=activitywatch-sync-server" --limit=10
```

## Current Usage
- **Active Users**: 3+ team members
- **Data Volume**: 10,000+ events processed
- **Uptime**: 99.9% availability
- **Last Updated**: September 23, 2025