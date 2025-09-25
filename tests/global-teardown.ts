import { FullConfig } from '@playwright/test';
import { execSync } from 'child_process';
import * as fs from 'fs';

async function globalTeardown(config: FullConfig) {
  console.log('🧹 Global teardown: Cleaning up test environment...');
  
  try {
    // Kill any remaining ActivityWatch processes
    try {
      execSync('pkill -f "ActivityWatch" || true', { stdio: 'pipe' });
      console.log('🔄 Cleaned up ActivityWatch processes');
    } catch (error) {
      // Ignore errors - processes might not be running
    }
    
    // Unmount any remaining DMG volumes
    try {
      const volumes = execSync('ls /Volumes/ | grep -i activitywatch || true').toString().trim();
      if (volumes) {
        volumes.split('\n').forEach(volume => {
          if (volume.trim()) {
            try {
              execSync(`hdiutil detach "/Volumes/${volume.trim()}" 2>/dev/null || true`);
              console.log(`📦 Unmounted DMG: ${volume.trim()}`);
            } catch (error) {
              // Ignore unmount errors
            }
          }
        });
      }
    } catch (error) {
      // Ignore errors
    }
    
    // Clean up temporary Applications installations
    try {
      execSync('rm -rf /tmp/mock_applications_* 2>/dev/null || true');
      execSync('rm -rf /tmp/aw_installer_test_* 2>/dev/null || true');
      console.log('🗑️ Cleaned up temporary directories');
    } catch (error) {
      // Ignore cleanup errors
    }
    
    // Clean up any test Launch Agents
    try {
      execSync('launchctl unload ~/Library/LaunchAgents/com.activitywatch.team.test.plist 2>/dev/null || true');
      execSync('rm -f ~/Library/LaunchAgents/com.activitywatch.team.test.plist 2>/dev/null || true');
    } catch (error) {
      // Ignore cleanup errors
    }
    
    // Remove quarantine attributes from test applications (cleanup)
    try {
      execSync('xattr -r -d com.apple.quarantine /tmp/test_* 2>/dev/null || true');
    } catch (error) {
      // Ignore cleanup errors
    }
    
    // Generate test summary
    const testSummary = {
      timestamp: new Date().toISOString(),
      cleanup: 'completed',
      platform: process.platform,
      nodeVersion: process.version
    };
    
    if (!fs.existsSync('tests/logs')) {
      fs.mkdirSync('tests/logs', { recursive: true });
    }
    
    fs.writeFileSync('tests/logs/teardown-summary.json', JSON.stringify(testSummary, null, 2));
    
    console.log('✅ Global teardown completed successfully');
    
  } catch (error) {
    console.error('⚠️ Global teardown encountered errors:', error);
    // Don't throw - we don't want teardown failures to fail the entire test run
  }
}

export default globalTeardown;