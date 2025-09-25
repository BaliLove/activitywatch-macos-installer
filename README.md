# ActivityWatch Team macOS Installer 🍎

[![Build Status](https://github.com/BaliLove/activitywatch-macos-installer/actions/workflows/build-macos.yml/badge.svg)](https://github.com/BaliLove/activitywatch-macos-installer/actions)
[![macOS Support](https://img.shields.io/badge/macOS-12.0+-blue.svg)](https://support.apple.com/macos)
[![Python](https://img.shields.io/badge/python-3.11+-green.svg)](https://python.org)

**Status: ✅ READY FOR PRODUCTION**

A professional macOS installer that automatically downloads, installs, and configures ActivityWatch with team sync capabilities for seamless productivity tracking across your organization.

## 🚀 Quick Start for Team Members

### Option 1: Download Pre-built Installer (Recommended)
1. Download the latest `ActivityWatch-Team-Installer-macOS-*.dmg` from [GitHub Releases](../../releases)
2. Double-click the DMG to mount it
3. Drag the "ActivityWatch Team Installer" app to your Applications folder
4. Launch the app from Applications
5. Enter your team email when prompted (e.g., `yourname@bali.love`)
6. The installer will automatically download and configure ActivityWatch

### Option 2: Build from Source
```bash
git clone https://github.com/BaliLove/activitywatch-macos-installer.git
cd activitywatch-macos-installer
./build_macos.sh
```

## 🏗️ For Developers & DevOps

### Current Architecture
- **Main App**: `activitywatch_installer_macos_enhanced.py` - Full-featured installer with GUI/CLI modes
- **Build Script**: `build_macos.sh` - Creates macOS app bundle and DMG
- **CI/CD**: `.github/workflows/build-macos.yml` - Automated testing on macOS 12-14
- **Server**: `https://activitywatch-sync-server-1051608384208.us-central1.run.app`

### Build Process
The GitHub Actions workflow automatically:
1. **Builds** the installer on multiple macOS versions
2. **Tests** app bundle integrity, DMG creation, and installation simulation
3. **Validates** system requirements, network connectivity, and Gatekeeper compatibility
4. **Uploads** artifacts for download and deployment

### System Requirements
- **macOS**: 12.0+ (Monterey through Sonoma)
- **Python**: 3.11+ (bundled in installer)
- **Network**: Required for ActivityWatch download and sync
- **Disk Space**: ~500MB for full installation

## 🔧 Configuration

### API Integration
```json
{
  "api_key": "aw-team-2025-secure-key-v1",
  "server_url": "https://activitywatch-sync-server-1051608384208.us-central1.run.app",
  "sync_interval": 600,
  "endpoint": "/api/sync"
}
```

### Privacy Settings
The installer automatically configures privacy protection:
- Encrypts sensitive window titles (passwords, banking, etc.)
- Filters private browsing sessions
- Excludes password managers and financial apps
- Configurable work hours tracking

## 📁 Repository Structure

```
├── .github/workflows/          # CI/CD automation
│   └── build-macos.yml        # Main build workflow
├── docs/                      # Documentation
├── tests/                     # Playwright UI tests
├── activitywatch_installer_macos_enhanced.py  # Main installer
├── build_macos.sh            # Build script
├── config_template.json      # Configuration template  
├── privacy_settings.json     # Privacy configuration
└── requirements.txt          # Python dependencies
```

## 🧪 Testing & Quality Assurance

### Automated Testing (GitHub Actions)
Every commit is automatically tested on:
- ✅ **macOS 12** (Monterey)
- ✅ **macOS 13** (Ventura) 
- ✅ **macOS 14** (Sonoma)

Tests include:
- App bundle structure validation
- DMG integrity and mounting
- Installation workflow simulation
- System compatibility checks
- Network connectivity validation
- Gatekeeper/quarantine testing

### Manual Testing
For additional validation, artifacts can be downloaded and tested on physical Macs:

```bash
# Download latest build artifacts
gh run download --name activitywatch-macos-dmg-unsigned-latest

# Test on macOS device
open ActivityWatch-Team-Installer-macOS-*.dmg
```

## 🚀 Deployment & Release Process

### For Operations Team
1. **Monitor**: Check [GitHub Actions](../../actions) for build status
2. **Download**: Get artifacts from successful builds
3. **Distribute**: Share DMG files with team members via your preferred method
4. **Verify**: Check server logs for new device connections

### Creating New Releases
```bash
# Tag a release to trigger automatic build
git tag v1.0.0
git push origin v1.0.0

# Or trigger manual build with options
gh workflow run build-macos.yml \
  --field enable_ui_tests=true \
  --field enable_gatekeeper_tests=true \
  --field target_macos_version=14
```

## 📊 Data & Monitoring

### Server Integration
- **Endpoint**: `POST /api/sync`
- **Authentication**: `X-API-Key: aw-team-2025-secure-key-v1`
- **Data Format**: JSON with user email, events, and metadata
- **Sync Frequency**: Every 10 minutes
- **Storage**: BigQuery for analytics

### Monitoring Checklist
- [ ] Server health at endpoint URL
- [ ] BigQuery data ingestion
- [ ] Client sync frequency (10 minutes)
- [ ] Privacy setting compliance
- [ ] macOS compatibility updates

## 🔒 Security & Privacy

### Data Protection
- Window titles encrypted using configurable keyword filtering
- Private browsing sessions excluded automatically
- Password managers and banking apps filtered
- Local data encrypted at rest
- Secure API key transmission

### Compliance Features
- User consent during installation
- Opt-out capabilities built-in
- Data retention policies configurable
- Audit trail for all sync operations

## 🛠️ Maintenance & Support

### Common Issues
1. **"App can't be opened"** → Right-click app, select "Open", confirm security dialog
2. **Sync not working** → Check network connection and server status
3. **High CPU usage** → Verify ActivityWatch isn't conflicting with other apps
4. **Missing data** → Check privacy settings aren't over-filtering

### Server Maintenance
- Monitor endpoint: `https://activitywatch-sync-server-1051608384208.us-central1.run.app/health`
- API key rotation: Update `config_template.json` and rebuild
- BigQuery schema updates: Coordinate with data team

### Updates & Patches
1. Update `activitywatch_installer_macos_enhanced.py` with changes
2. Commit changes to trigger automatic testing
3. Review GitHub Actions results
4. Tag release when ready for distribution
5. Download and distribute new DMG files

## 📝 Development Notes

### Key Dependencies
- **PyInstaller**: Creates standalone executable
- **requests**: HTTP client for server communication
- **certifi**: SSL certificate validation
- **tkinter**: GUI interface (included with Python)

### Build Environment
- Requires macOS for building (GitHub Actions provides this)
- Python 3.11+ with pip package management
- Xcode Command Line Tools for app bundle creation
- DMG creation uses built-in macOS tools

### Troubleshooting Build Issues
```bash
# Local development setup
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt

# Test installer locally
python3 activitywatch_installer_macos_enhanced.py --terminal

# Build locally (requires macOS)
./build_macos.sh
```

## 📞 Support & Contact

- **Repository Issues**: Use GitHub Issues for bugs and feature requests
- **CI/CD Problems**: Check GitHub Actions logs and status
- **Server Issues**: Contact infrastructure team
- **User Support**: Refer to installation guide and FAQ

---

**Last Updated**: January 2025  
**Maintainer**: BaliLove Team  
**License**: Internal Use  
**Build System**: GitHub Actions on macOS runners
