# ActivityWatch macOS Installer Testing Framework

## Overview

This document describes the comprehensive automated testing framework for the ActivityWatch macOS installer, designed to catch the "nothing happens" scenarios and other deployment issues that occur in real-world usage.

## Framework Components

### 1. GitHub Actions Workflow

The main workflow (`build-macos.yml`) provides:

- **Multi-macOS Version Testing**: Tests across macOS 12, 13, and 14
- **Signed/Unsigned Variants**: Tests both signed and unsigned installers
- **Playwright UI Automation**: Real macOS GUI automation for installation testing
- **Timeout & Hang Detection**: Advanced monitoring to catch silent failures
- **Rich Diagnostics**: Comprehensive logging and error reporting

### 2. Test Types

#### GUI Installation Tests (`installer_gui.spec.ts`)
- **DMG Mounting**: Verifies DMG can be mounted and contains expected files
- **Drag-and-Drop Install**: Simulates user dragging app to Applications
- **App Launch**: Tests actual app launch from Applications folder  
- **GUI Interaction**: Automated email input and installation progression
- **Installation Verification**: Confirms ActivityWatch is properly installed
- **Cleanup**: Removes test installations

#### CLI Installation Tests (`installer_cli.spec.ts`)
- **Terminal Mode**: Tests the `--terminal` flag functionality
- **Input Handling**: Automated email input via stdin
- **Output Validation**: Verifies expected console output
- **Error Scenarios**: Tests invalid emails and user cancellation
- **Hang Detection**: Monitors for CLI hangs and timeouts

#### Gatekeeper & Edge Case Tests (`gatekeeper_scenarios.spec.ts`)
- **Quarantine Testing**: Tests Gatekeeper quarantine attribute handling
- **Security Dialogs**: Automates macOS security dialog responses
- **Network Issues**: Tests offline installation scenarios
- **Existing Installations**: Tests upgrade/replacement scenarios  
- **Disk Space**: Tests insufficient disk space handling
- **Permission Errors**: Tests read-only directory scenarios

### 3. Automation Helpers

#### MacOSAutomation Helper (`macos-automation.ts`)
- **DMG Operations**: Mount, unmount, verify DMG files
- **App Installation**: Simulate drag-and-drop installation
- **System Control**: Launch apps, kill processes, handle dialogs
- **Security Management**: Set/remove quarantine attributes
- **Network Control**: Disable/enable network connectivity
- **Diagnostics**: Capture system state and logs

### 4. Workflow Parameters

#### Manual Trigger Options
```yaml
workflow_dispatch:
  inputs:
    create_release: boolean        # Create GitHub release
    sign_and_notarize: boolean    # Code sign and notarize  
    run_ui_tests: boolean         # Run Playwright tests
    dmg_url: string              # Test external DMG URL
    test_gatekeeper: boolean      # Run Gatekeeper tests
    macos_version: choice         # Target specific macOS version
    timeout_minutes: number       # Test timeout (default: 30)
    detailed_diagnostics: boolean # Capture system diagnostics
```

#### Scheduled Runs
- **Nightly**: Runs at 3 AM UTC with full test matrix
- **Comprehensive**: Tests all macOS versions and scenarios

### 5. Diagnostic Features

#### Timeout Detection
- **Per-Test Timeouts**: Each test type has individual timeouts
- **Global Timeout**: Overall job timeout with cleanup buffer
- **Progress Monitoring**: Regular progress updates during long tests

#### Hang Detection  
- **Log Activity Monitoring**: Detects when logs stop updating
- **System State Capture**: Captures process lists, resources, network
- **Automatic Termination**: Kills hung processes gracefully
- **Diagnostic Reports**: Detailed hang analysis reports

#### Rich Reporting
- **Test Summaries**: Comprehensive results in GitHub UI
- **Artifact Collection**: Screenshots, videos, traces, logs
- **Error Analysis**: Automatic detection of common failure patterns
- **Visual Evidence**: Screenshots at key interaction points

## Usage Guide

### Running Tests Manually

#### Full Test Suite (All macOS Versions)
1. Go to Actions tab in GitHub repository
2. Select "Build ActivityWatch macOS Installer" workflow
3. Click "Run workflow"
4. Configure options:
   - `macos_version`: "all"
   - `run_ui_tests`: true
   - `test_gatekeeper`: true
   - `timeout_minutes`: 30
5. Click "Run workflow"

#### Testing Specific macOS Version
1. Follow steps 1-3 above
2. Configure options:
   - `macos_version`: "macos-14" (or desired version)
   - Other options as needed
3. Run workflow

#### Testing External DMG
1. Follow steps 1-3 above  
2. Configure options:
   - `dmg_url`: "https://example.com/path/to/installer.dmg"
   - `run_ui_tests`: true
3. Run workflow

### Interpreting Results

#### Test Summary
Located in the GitHub Actions job summary, provides:
- **Environment Details**: macOS version, architecture, resources
- **Test Results**: Pass/fail counts for each test type
- **Artifacts Available**: Links to logs, screenshots, videos
- **Critical Issues**: Automatically detected problems

#### Artifacts
Automatically uploaded for analysis:
- **📸 Screenshots**: Key interaction moments
- **🎬 Videos**: Full test execution recordings  
- **🔍 Traces**: Detailed Playwright execution traces
- **📋 Logs**: System logs, installer logs, test logs
- **📊 Reports**: Interactive HTML test reports

#### Common Failure Patterns

##### "Nothing Happens" Scenarios
- **Symptoms**: App appears to launch but no GUI appears
- **Diagnostics**: Check for Gatekeeper blocking in logs
- **Artifacts**: Look for security-related console messages

##### Installation Hangs
- **Symptoms**: Process stops responding during install
- **Diagnostics**: Hang detection captures system state
- **Artifacts**: Process dumps and resource usage logs

##### Network-Related Failures
- **Symptoms**: Installer fails to sync with team server
- **Diagnostics**: Network connectivity tests run automatically
- **Artifacts**: Network connection logs and endpoint tests

## Test Environment Specifications

### GitHub Actions Runners
- **macOS 12**: GitHub-hosted runner (Intel x86_64)
- **macOS 13**: GitHub-hosted runner (Intel x86_64)  
- **macOS 14**: GitHub-hosted runner (Apple Silicon M1)

### Test Isolation
- **Clean Environment**: Each test starts with fresh runner
- **Cleanup**: Tests clean up after themselves
- **Independence**: Tests don't affect each other

### Resource Limits
- **Timeout**: 30 minutes default (configurable)
- **Disk Space**: ~14GB available on runners
- **Memory**: 7GB available on runners
- **Network**: Full internet access for downloads

## Development Guidelines

### Adding New Tests

#### 1. Create Test File
```typescript
// tests/new-feature.spec.ts
import { test, expect } from '@playwright/test';
import { MacOSAutomation } from '../helpers/macos-automation';

test.describe('New Feature Tests', () => {
  let automation: MacOSAutomation;
  
  test.beforeEach(async () => {
    automation = new MacOSAutomation();
  });
  
  test.afterEach(async () => {
    await automation.cleanup();
  });
  
  test('should test new feature', async () => {
    // Test implementation
  });
});
```

#### 2. Update Workflow
Add test execution to the workflow:
```yaml
# Run new feature tests
echo "4. Running new feature tests..."
run_test_with_timeout "New-Feature-Tests" "tests/new-feature.spec.ts" || true
```

#### 3. Update Documentation
- Add test description to this document
- Update usage examples if needed
- Document any new parameters or outputs

### Best Practices

#### Test Design
- **Isolation**: Tests should not depend on each other
- **Cleanup**: Always clean up test artifacts
- **Timeouts**: Use reasonable timeouts for operations
- **Error Handling**: Handle expected failures gracefully

#### Debugging
- **Screenshots**: Take screenshots at key moments
- **Logging**: Log important actions and state changes
- **Diagnostics**: Capture system state on failures
- **Reproduction**: Make failures reproducible locally

#### Performance
- **Efficient Waits**: Use Playwright's smart waiting
- **Resource Management**: Clean up processes and files
- **Parallel Safe**: Design tests to run in parallel safely

## Troubleshooting

### Common Issues

#### Test Timeouts
- **Cause**: macOS runners can be slow during peak hours
- **Solution**: Increase `timeout_minutes` parameter
- **Prevention**: Use efficient waits, avoid sleep() calls

#### Gatekeeper Blocking
- **Cause**: Unsigned apps trigger Gatekeeper by default
- **Solution**: Tests handle this automatically with AppleScript
- **Prevention**: Use signed builds for production testing

#### Network Connectivity
- **Cause**: Tests need internet access for downloads
- **Solution**: Built-in network connectivity tests
- **Prevention**: Implement offline fallback modes

#### Resource Exhaustion
- **Cause**: Tests don't clean up properly
- **Solution**: Review cleanup procedures in failing tests
- **Prevention**: Use try/finally blocks for cleanup

### Getting Help

#### Debug Information
When reporting issues, include:
- **Workflow Run URL**: Link to the failing GitHub Actions run
- **Test Artifacts**: Download and examine logs/screenshots
- **Environment**: macOS version and runner type
- **Configuration**: Workflow input parameters used

#### Log Analysis
Key log files to examine:
- `tests/logs/*-execution.log`: Individual test execution logs
- `tests/logs/hang-diagnostic-*.log`: Hang detection reports  
- `tests/logs/system-logs-*.log`: System console logs
- `tests/playwright-report/`: Interactive test report

## Future Enhancements

### Planned Features
- **Real Device Testing**: Integration with physical Mac hardware
- **Performance Benchmarking**: Installation speed measurements
- **User Simulation**: More complex user interaction patterns
- **A/B Testing**: Compare different installer variants
- **Accessibility Testing**: VoiceOver and accessibility validation

### Integration Opportunities
- **Slack Notifications**: Alert team on test failures
- **Metrics Collection**: Performance and reliability metrics
- **Automated Rollback**: Revert on critical test failures
- **Release Gates**: Require passing tests for releases

---

## Quick Reference

### Commands
```bash
# Run all tests locally (if you have macOS)
npm test

# Run specific test file  
npx playwright test tests/installer_gui.spec.ts

# Run tests with debug mode
npx playwright test --debug

# Generate test report
npx playwright show-report
```

### Key Files
- `.github/workflows/build-macos.yml` - Main workflow
- `tests/installer_gui.spec.ts` - GUI installation tests
- `tests/installer_cli.spec.ts` - CLI installation tests  
- `tests/gatekeeper_scenarios.spec.ts` - Security tests
- `helpers/macos-automation.ts` - macOS automation helpers
- `playwright.config.ts` - Playwright configuration

### Workflow Triggers
- **Push**: Main/develop branches and tags
- **Pull Request**: To main branch
- **Manual**: Via workflow_dispatch
- **Schedule**: Nightly at 3 AM UTC

This testing framework provides comprehensive coverage for the macOS installer, specifically designed to catch the "nothing happens" scenarios that plague real-world deployments.