# Development Guide

## Overview

This repository contains the source code and build system for the ActivityWatch Team macOS installer. The installer is built using Python and PyInstaller, with automated testing via GitHub Actions.

## Architecture

### Core Components

1. **Main Installer** (`activitywatch_installer_macos_enhanced.py`)
   - GUI and CLI modes
   - ActivityWatch download and installation
   - Team sync configuration
   - Privacy settings setup

2. **Build Script** (`build_macos.sh`)
   - PyInstaller app bundle creation
   - DMG package generation
   - Entitlements configuration

3. **CI/CD Pipeline** (`.github/workflows/build-macos.yml`)
   - Multi-version macOS testing
   - Automated build and artifact generation
   - Quality assurance testing

## Local Development

### Prerequisites
- macOS 12.0+ (for building)
- Python 3.11+
- Xcode Command Line Tools
- Git

### Setup
```bash
# Clone the repository
git clone https://github.com/BaliLove/activitywatch-macos-installer.git
cd activitywatch-macos-installer

# Create virtual environment
python3 -m venv venv
source venv/bin/activate

# Install dependencies
pip install -r requirements.txt
```

### Testing the Installer
```bash
# Test CLI mode
python3 activitywatch_installer_macos_enhanced.py --terminal

# Test GUI mode  
python3 activitywatch_installer_macos_enhanced.py

# Test with dry run
python3 activitywatch_installer_macos_enhanced.py --dry-run
```

### Building Locally
```bash
# Build app bundle and DMG
./build_macos.sh

# Output will be in dist/ directory
ls -la dist/
```

## Configuration

### API Configuration
The installer uses these hardcoded settings:
- **Server URL**: `https://activitywatch-sync-server-1051608384208.us-central1.run.app`
- **API Key**: `aw-team-2025-secure-key-v1`
- **Sync Interval**: 600 seconds (10 minutes)

To modify these, update `config_template.json` and rebuild.

### Privacy Settings
Privacy configuration is in `privacy_settings.json`:
- Sensitive keyword filtering
- App exclusion lists
- Work hours settings

## Testing

### Automated Testing
GitHub Actions automatically tests:
- App bundle structure
- DMG integrity
- Installation simulation
- System compatibility
- Network connectivity

### Manual Testing
```bash
# Download artifacts from GitHub Actions
gh run download <run-id> --name activitywatch-macos-dmg-unsigned-*

# Test on clean macOS system
open ActivityWatch-Team-Installer-macOS-*.dmg
```

## Release Process

### Creating Releases
1. **Prepare Release**:
   ```bash
   # Update version in installer
   # Test all functionality
   # Update documentation
   ```

2. **Tag and Push**:
   ```bash
   git tag v1.0.0
   git push origin v1.0.0
   ```

3. **Monitor Build**:
   - Check GitHub Actions for build status
   - Download artifacts when complete
   - Test final DMG

4. **Distribute**:
   - Upload DMG to release
   - Notify team members
   - Update documentation

### Hotfixes
For urgent fixes:
1. Create fix in new branch
2. Test via pull request
3. Merge and tag immediately
4. Fast-track through CI/CD

## CI/CD Details

### Workflow Triggers
- **Push**: Automatic build on main branch
- **Pull Request**: Test builds for validation
- **Manual**: Workflow dispatch with options

### Build Matrix
Tests on multiple macOS versions:
- macOS 12 (Monterey)
- macOS 13 (Ventura)
- macOS 14 (Sonoma)

### Artifact Outputs
- Unsigned app bundle (for testing)
- Unsigned DMG (for distribution)
- Build info and checksums

## Troubleshooting

### Build Issues
```bash
# Check Python version
python3 --version

# Verify PyInstaller
pip show PyInstaller

# Clean build
rm -rf dist/ build/
./build_macos.sh
```

### Signing Issues
Current build uses unsigned artifacts. For production:
1. Configure Apple Developer certificates
2. Update workflow with signing steps
3. Enable notarization process

### Testing Issues
```bash
# Check app bundle structure
find "dist/ActivityWatch Team Installer.app" -type f

# Verify DMG mounting
hdiutil verify "dist/ActivityWatch-Team-Installer-macOS-*.dmg"

# Test installation workflow
python3 -c "from activitywatch_installer_macos_enhanced import *"
```

## Code Structure

### Main Classes
- `ActivityWatchMacOSInstaller`: Core installer logic
- GUI methods: `create_gui()`, `show_*_screen()`
- CLI methods: `run_terminal_mode()`
- Installation: `download_*()`, `install_*()`, `configure_*()`

### Key Methods
- `verify_system()`: System requirements check
- `download_activitywatch()`: ActivityWatch download
- `setup_sync_client()`: Team sync configuration
- `configure_privacy_settings()`: Privacy setup

### Configuration Files
- `config_template.json`: API and server settings
- `privacy_settings.json`: Privacy filtering rules
- `requirements.txt`: Python dependencies

## Security Considerations

### Data Handling
- No sensitive data stored in repository
- API keys are hardcoded (internal use)
- User emails collected during installation only

### Build Security
- GitHub Actions provides secure build environment
- Artifacts are unsigned (requires manual trust)
- No secrets or credentials in source code

### Distribution Security
- DMG files should be distributed via secure channels
- End users must explicitly trust unsigned apps
- Consider code signing for production deployment

## Performance

### Build Times
- Local build: ~2-3 minutes
- GitHub Actions: ~5-7 minutes
- Full test suite: ~10-15 minutes

### App Size
- App bundle: ~35MB
- DMG file: ~11MB
- ActivityWatch download: ~100MB

### Runtime Performance
- Installation time: 2-5 minutes
- Memory usage: ~50MB during install
- Disk usage: ~500MB total after install

---

For additional support, check GitHub Issues or contact the development team.