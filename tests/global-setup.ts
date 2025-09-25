import { chromium, FullConfig } from '@playwright/test';
import { execSync } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';

async function globalSetup(config: FullConfig) {
  console.log('🔧 Global setup: Preparing macOS test environment...');
  
  // Check if we're running on macOS
  if (process.platform !== 'darwin') {
    throw new Error('❌ These tests can only run on macOS');
  }
  
  // Create test directories
  const testDirs = [
    'tests/screenshots',
    'tests/videos',
    'tests/traces',
    'tests/logs',
    'tests/temp'
  ];
  
  testDirs.forEach(dir => {
    if (!fs.existsSync(dir)) {
      fs.mkdirSync(dir, { recursive: true });
    }
  });
  
  // System information logging
  const systemInfo = {
    macOSVersion: execSync('sw_vers -productVersion').toString().trim(),
    architecture: execSync('uname -m').toString().trim(),
    availableRAM: execSync('sysctl hw.memsize').toString().split(':')[1].trim(),
    availableDisk: execSync('df -h / | awk \'NR==2 {print $4}\'').toString().trim(),
  };
  
  console.log('📊 System Information:');
  console.log(`   macOS Version: ${systemInfo.macOSVersion}`);
  console.log(`   Architecture: ${systemInfo.architecture}`);
  console.log(`   Available RAM: ${Math.round(parseInt(systemInfo.availableRAM) / 1024 / 1024 / 1024)} GB`);
  console.log(`   Available Disk: ${systemInfo.availableDisk}`);
  
  // Write system info to file
  fs.writeFileSync('tests/logs/system-info.json', JSON.stringify(systemInfo, null, 2));
  
  // Check for DMG file
  const dmgPath = process.env.DMG_PATH;
  if (dmgPath && fs.existsSync(dmgPath)) {
    console.log(`✅ DMG found at: ${dmgPath}`);
    // Verify DMG integrity
    try {
      execSync(`hdiutil verify "${dmgPath}"`, { stdio: 'pipe' });
      console.log('✅ DMG integrity verified');
    } catch (error) {
      console.error('❌ DMG integrity check failed:', error);
      throw error;
    }
  } else {
    console.warn('⚠️ No DMG path specified or file not found');
  }
  
  // Ensure we have necessary permissions for Accessibility and Screen Recording
  console.log('🔐 Checking system permissions...');
  
  // Check if we need to prompt for permissions
  try {
    // This will trigger permissions dialog if needed
    execSync('osascript -e "tell application \\"System Events\\" to get name of first process"', { stdio: 'pipe' });
    console.log('✅ Accessibility permissions available');
  } catch (error) {
    console.warn('⚠️ Accessibility permissions may be required for full testing');
  }
  
  console.log('🎭 Global setup completed successfully');
}

export default globalSetup;
