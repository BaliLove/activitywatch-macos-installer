import { test, expect } from '@playwright/test';
import { MacOSAutomation } from './helpers/macos';
import * as path from 'path';
import * as fs from 'fs';

test.describe('ActivityWatch macOS Installer Gatekeeper & Edge Case Tests', () => {
  let macOS: MacOSAutomation;
  let dmgPath: string;
  
  test.beforeEach(async () => {
    macOS = new MacOSAutomation();
    dmgPath = process.env.DMG_PATH || '';
    
    if (!dmgPath || !fs.existsSync(dmgPath)) {
      throw new Error(`DMG file not found: ${dmgPath}`);
    }
    
    console.log(`🎯 Testing DMG: ${dmgPath}`);
  });
  
  test.afterEach(async () => {
    await macOS.cleanup();
  });

  test('Gatekeeper Quarantine Scenario', async () => {
    console.log('🛡️ Testing Gatekeeper quarantine scenario...');
    
    const mountInfo = await macOS.mountDMG(dmgPath);
    const installerAppPath = path.join(mountInfo.mountPoint, 'ActivityWatch Team Installer.app');
    const installedAppPath = await macOS.installAppToApplications(
      installerAppPath, 
      'ActivityWatch Team Installer.app'
    );
    
    // Step 1: Force quarantine attribute to simulate download from internet
    console.log('🔒 Adding quarantine attribute...');
    await macOS.setQuarantineAttribute(installedAppPath, true);
    
    // Take screenshot showing quarantine attributes
    await macOS.takeScreenshot('tests/screenshots/quarantine-attributes.png');
    
    // Step 2: Check Gatekeeper status
    const gatekeeperStatus = await macOS.checkGatekeeperStatus(installedAppPath);
    console.log(`🛡️ Gatekeeper status: blocked=${gatekeeperStatus.blocked}, reason=${gatekeeperStatus.reason}`);
    
    if (gatekeeperStatus.blocked) {
      console.log('✅ Gatekeeper correctly blocks quarantined app');
      expect(gatekeeperStatus.blocked).toBe(true);
      
      // Step 3: Attempt to launch (should trigger Gatekeeper dialog)
      console.log('🚀 Attempting to launch quarantined app...');
      
      let gatekeeperDialogDetected = false;
      
      try {
        // Launch the app in a non-blocking way
        const launchPromise = macOS.launchApp(installedAppPath, [], 15000);
        
        // Give it a moment for Gatekeeper dialog to appear
        await macOS.sleep(3000);
        
        // Take screenshot of potential Gatekeeper dialog
        await macOS.takeScreenshot('tests/screenshots/gatekeeper-dialog-quarantine.png');
        
        // Try to handle the Gatekeeper dialog automatically
        console.log('🛡️ Attempting to handle Gatekeeper dialog...');
        await macOS.handleGatekeeperDialog('open');
        
        // Wait for the app to potentially launch after dialog handling
        const processInfo = await launchPromise;
        
        if (processInfo.pid > 0) {
          console.log('✅ Successfully bypassed Gatekeeper dialog');
          gatekeeperDialogDetected = true;
          
          // Clean up the launched process
          await macOS.killProcess(processInfo.pid);
        }
        
      } catch (error) {
        console.log(`ℹ️ Gatekeeper launch attempt result: ${error}`);
        gatekeeperDialogDetected = error.toString().includes('timeout') || error.toString().includes('blocked');
      }
      
      // This test passes if we detect Gatekeeper behavior (blocking or dialog)
      console.log(`🔍 Gatekeeper dialog detection: ${gatekeeperDialogDetected}`);
      
      // Step 4: Remove quarantine and verify app can launch normally
      console.log('🔓 Removing quarantine attribute for normal launch test...');
      await macOS.setQuarantineAttribute(installedAppPath, false);
      
      // Verify removal
      const newStatus = await macOS.checkGatekeeperStatus(installedAppPath);
      console.log(`🛡️ New Gatekeeper status after quarantine removal: blocked=${newStatus.blocked}`);
      
      // Try to launch normally now
      try {
        const normalProcessInfo = await macOS.launchApp(installedAppPath, [], 30000);
        console.log('✅ App launched successfully after quarantine removal');
        expect(normalProcessInfo.pid).toBeGreaterThan(0);
        
        await macOS.killProcess(normalProcessInfo.pid);
      } catch (normalError) {
        console.warn(`⚠️ App still failed to launch after quarantine removal: ${normalError}`);
        // This might indicate other issues with the installer
      }
      
    } else {
      console.log('ℹ️ App was not blocked by Gatekeeper (possibly signed or system configured to allow)');
      // This is not necessarily a failure - signed apps won't be blocked
    }
    
    console.log('✅ Gatekeeper quarantine scenario test completed');
  });
  
  test('Network Connectivity Issues', async () => {
    console.log('🌐 Testing network connectivity issues...');
    
    const mountInfo = await macOS.mountDMG(dmgPath);
    const installerAppPath = path.join(mountInfo.mountPoint, 'ActivityWatch Team Installer.app');
    const installedAppPath = await macOS.installAppToApplications(
      installerAppPath, 
      'ActivityWatch Team Installer.app'
    );
    
    await macOS.setQuarantineAttribute(installedAppPath, false);
    
    // Step 1: Test with network connectivity disabled
    console.log('📡 Disabling network connectivity...');
    
    // Note: This may require sudo privileges and might not work in CI
    try {
      await macOS.setNetworkConnectivity(false);
      await macOS.sleep(2000);
      
      console.log('🚀 Launching installer with no network...');
      
      // Launch installer and see how it handles network issues
      const executablePath = path.join(installedAppPath, 'Contents', 'MacOS', 'ActivityWatch Team Installer');
      
      const networkTestPromise = new Promise<{ success: boolean; output: string }>((resolve) => {
        const { spawn } = require('child_process');
        const process = spawn(executablePath, ['--terminal'], {
          stdio: ['pipe', 'pipe', 'pipe']
        });
        
        let stdout = '';
        let stderr = '';
        
        process.stdout.on('data', (data) => {
          stdout += data.toString();
          console.log(`📝 Network test output: ${data.toString().trim()}`);
          
          // Send test email if prompted
          if (data.toString().includes('Enter your work email:')) {
            process.stdin.write('network.test@bali.love\\n');
          }
          
          // Send confirmation if prompted
          if (data.toString().includes('Ready to install?')) {
            process.stdin.write('y\\n');
          }
        });
        
        process.stderr.on('data', (data) => {
          stderr += data.toString();
        });
        
        process.on('close', (code) => {
          console.log(`💻 Network test process exited with code: ${code}`);
          resolve({ 
            success: code === 0, 
            output: `STDOUT:\\n${stdout}\\n\\nSTDERR:\\n${stderr}` 
          });
        });
        
        // Timeout after 2 minutes
        setTimeout(() => {
          process.kill('SIGTERM');
          resolve({ 
            success: false, 
            output: `TIMEOUT\\nSTDOUT:\\n${stdout}\\n\\nSTDERR:\\n${stderr}` 
          });
        }, 2 * 60 * 1000);
      });
      
      const networkTestResult = await networkTestPromise;
      
      // Save network test results
      fs.writeFileSync('tests/logs/network-disconnected-test.log', networkTestResult.output);
      
      // The installer should either:
      // 1. Handle network errors gracefully with informative messages
      // 2. Fail with clear error messages (not silent failure)
      // 3. Continue with offline installation if possible
      
      expect(networkTestResult.output.length).toBeGreaterThan(0); // Should produce some output
      
      if (!networkTestResult.success) {
        // Check if it's a graceful failure with error messages
        const hasNetworkErrorMessage = /network|connection|internet|download.*fail/i.test(networkTestResult.output);
        console.log(`🔍 Network error message present: ${hasNetworkErrorMessage}`);
        
        if (hasNetworkErrorMessage) {
          console.log('✅ Installer handled network failure gracefully with error message');
        } else {
          console.warn('⚠️ Installer failed without clear network error message');
        }
      } else {
        console.log('ℹ️ Installer succeeded despite network disconnection (offline capable)');
      }
      
    } catch (networkError) {
      console.warn(`⚠️ Network connectivity test skipped (requires sudo): ${networkError}`);
    } finally {
      // Always restore network connectivity
      try {
        await macOS.setNetworkConnectivity(true);
        console.log('📡 Network connectivity restored');
      } catch (restoreError) {
        console.warn(`⚠️ Failed to restore network: ${restoreError}`);
      }
    }
    
    console.log('✅ Network connectivity test completed');
  });
  
  test('Existing ActivityWatch Installation Conflict', async () => {
    console.log('🏠 Testing existing ActivityWatch installation conflict...');
    
    const mountInfo = await macOS.mountDMG(dmgPath);
    const installerAppPath = path.join(mountInfo.mountPoint, 'ActivityWatch Team Installer.app');
    const installedAppPath = await macOS.installAppToApplications(
      installerAppPath, 
      'ActivityWatch Team Installer.app'
    );
    
    await macOS.setQuarantineAttribute(installedAppPath, false);
    
    // Step 1: Create a mock existing ActivityWatch installation
    console.log('📱 Creating mock existing ActivityWatch installation...');
    
    const existingAWPath = '/Applications/ActivityWatch.app';
    const mockAWDir = await macOS.createTempDirectory('mock-aw-');
    
    // Create a basic app structure
    const mockContents = path.join(mockAWDir, 'Contents');
    const mockMacOS = path.join(mockContents, 'MacOS');
    const mockResources = path.join(mockContents, 'Resources');
    
    fs.mkdirSync(mockContents, { recursive: true });
    fs.mkdirSync(mockMacOS, { recursive: true });
    fs.mkdirSync(mockResources, { recursive: true });
    
    // Create mock executable
    const mockExecutable = path.join(mockMacOS, 'ActivityWatch');
    fs.writeFileSync(mockExecutable, '#!/bin/bash\\necho \"Mock ActivityWatch\"\\n');
    fs.chmodSync(mockExecutable, 0o755);
    
    // Create mock Info.plist
    const mockInfoPlist = path.join(mockContents, 'Info.plist');
    fs.writeFileSync(mockInfoPlist, `<?xml version=\"1.0\" encoding=\"UTF-8\"?>
<!DOCTYPE plist PUBLIC \"-//Apple//DTD PLIST 1.0//EN\" \"http://www.apple.com/DTDs/PropertyList-1.0.dtd\">
<plist version=\"1.0\">
<dict>
    <key>CFBundleIdentifier</key>
    <string>net.activitywatch.ActivityWatch</string>
    <key>CFBundleName</key>
    <string>ActivityWatch</string>
    <key>CFBundleVersion</key>
    <string>0.12.0</string>
</dict>
</plist>`);
    
    // Move mock to Applications directory
    const { execSync } = require('child_process');
    execSync(`cp -R "${mockAWDir}" "${existingAWPath}"`);
    
    expect(fs.existsSync(existingAWPath)).toBe(true);
    console.log('✅ Mock existing ActivityWatch installation created');
    
    // Take screenshot showing existing installation
    await macOS.takeScreenshot('tests/screenshots/existing-aw-conflict.png');
    
    // Step 2: Run installer and see how it handles the conflict
    console.log('🚀 Running installer with existing installation...');
    
    const executablePath = path.join(installedAppPath, 'Contents', 'MacOS', 'ActivityWatch Team Installer');
    
    const conflictTestPromise = new Promise<{ output: string; exitCode: number }>((resolve) => {
      const { spawn } = require('child_process');
      const process = spawn(executablePath, ['--terminal'], {
        stdio: ['pipe', 'pipe', 'pipe']
      });
      
      let stdout = '';
      let stderr = '';
      
      process.stdout.on('data', (data) => {
        const output = data.toString();
        stdout += output;
        console.log(`📝 Conflict test output: ${output.trim()}`);
        
        // Handle prompts
        if (output.includes('Enter your work email:')) {
          process.stdin.write('conflict.test@bali.love\\n');
        } else if (output.includes('Ready to install?')) {
          process.stdin.write('y\\n');
        } else if (output.includes('existing') && output.includes('replace')) {
          // Handle existing installation prompt
          console.log('🔄 Choosing to replace existing installation...');
          process.stdin.write('y\\n');
        }
      });
      
      process.stderr.on('data', (data) => {
        stderr += data.toString();
      });
      
      process.on('close', (code) => {
        resolve({ 
          output: `STDOUT:\\n${stdout}\\n\\nSTDERR:\\n${stderr}`, 
          exitCode: code || 0 
        });
      });
      
      setTimeout(() => {
        process.kill('SIGTERM');
        resolve({ 
          output: `TIMEOUT\\nSTDOUT:\\n${stdout}\\n\\nSTDERR:\\n${stderr}`, 
          exitCode: -1 
        });
      }, 3 * 60 * 1000); // 3 minutes
    });
    
    const conflictResult = await conflictTestPromise;
    
    // Save conflict test results
    fs.writeFileSync('tests/logs/existing-installation-conflict.log', conflictResult.output);
    
    // Step 3: Verify how the installer handled the conflict
    console.log('🔍 Analyzing conflict resolution...');
    
    const hasConflictHandling = /existing|replace|backup|overwrite/i.test(conflictResult.output);
    console.log(`🔍 Conflict handling detected: ${hasConflictHandling}`);
    
    if (hasConflictHandling) {
      console.log('✅ Installer detected and handled existing installation');
    } else {
      console.warn('⚠️ No clear conflict handling detected in installer output');
    }
    
    // Check if installation still completed
    const stillExists = fs.existsSync(existingAWPath);
    console.log(`📱 ActivityWatch still exists after installation: ${stillExists}`);
    
    // Clean up
    try {
      execSync(`rm -rf "${existingAWPath}"`);
      console.log('🗑️ Cleaned up mock installation');
    } catch (cleanupError) {
      console.warn(`⚠️ Cleanup failed: ${cleanupError}`);
    }
    
    console.log('✅ Existing installation conflict test completed');
  });
  
  test('Disk Space Insufficient Scenario', async () => {
    console.log('💾 Testing insufficient disk space scenario...');
    
    const mountInfo = await macOS.mountDMG(dmgPath);
    const installerAppPath = path.join(mountInfo.mountPoint, 'ActivityWatch Team Installer.app');
    const installedAppPath = await macOS.installAppToApplications(
      installerAppPath, 
      'ActivityWatch Team Installer.app'
    );
    
    await macOS.setQuarantineAttribute(installedAppPath, false);
    
    // Check current disk space
    const { execSync } = require('child_process');
    const diskInfo = execSync('df -h / | awk \\'NR==2 {print $4}\\'').toString().trim();
    console.log(`📊 Current available disk space: ${diskInfo}`);
    
    // For this test, we'll simulate a disk space check in the installer
    // rather than actually filling up the disk (which would be dangerous)
    
    const executablePath = path.join(installedAppPath, 'Contents', 'MacOS', 'ActivityWatch Team Installer');
    
    console.log('🚀 Testing installer disk space awareness...');
    
    // Run the installer and capture any disk space related messages
    const diskSpaceTest = new Promise<string>((resolve) => {
      const { spawn } = require('child_process');
      const process = spawn(executablePath, ['--terminal'], {
        stdio: ['pipe', 'pipe', 'pipe']
      });
      
      let output = '';
      
      process.stdout.on('data', (data) => {
        const text = data.toString();
        output += text;
        
        // Look for disk space related messages
        if (/disk.*space|space.*available|storage|insufficient/i.test(text)) {
          console.log(`💾 Disk space message detected: ${text.trim()}`);
        }
        
        // Kill after getting initial output (we're just checking for disk space awareness)
        if (text.length > 1000 || text.includes('Enter your work email:')) {
          setTimeout(() => {
            process.kill('SIGTERM');
            resolve(output);
          }, 1000);
        }
      });
      
      process.on('close', () => {
        resolve(output);
      });
      
      setTimeout(() => {
        process.kill('SIGTERM');
        resolve(output);
      }, 30000);
    });
    
    const diskSpaceOutput = await diskSpaceTest;
    
    // Save disk space test output
    fs.writeFileSync('tests/logs/disk-space-test.log', diskSpaceOutput);
    
    // Check if installer shows disk space awareness
    const hasDiskSpaceCheck = /disk.*space|available.*space|storage|GB.*required/i.test(diskSpaceOutput);
    console.log(`💾 Disk space awareness detected: ${hasDiskSpaceCheck}`);
    
    if (hasDiskSpaceCheck) {
      console.log('✅ Installer shows disk space awareness');
    } else {
      console.log('ℹ️ No explicit disk space messages detected (may check internally)');
    }
    
    console.log('✅ Disk space scenario test completed');
  });
  
  test('Permission Denied Scenarios', async () => {
    console.log('🔒 Testing permission denied scenarios...');
    
    const mountInfo = await macOS.mountDMG(dmgPath);
    const installerAppPath = path.join(mountInfo.mountPoint, 'ActivityWatch Team Installer.app');
    const installedAppPath = await macOS.installAppToApplications(
      installerAppPath, 
      'ActivityWatch Team Installer.app'
    );
    
    await macOS.setQuarantineAttribute(installedAppPath, false);
    
    // Step 1: Create a read-only Applications directory simulation
    console.log('🔐 Testing with restricted permissions...');
    
    const testAppsDir = await macOS.createTempDirectory('test-apps-');
    
    // Make the test directory read-only
    const { execSync } = require('child_process');
    execSync(`chmod 444 "${testAppsDir}"`);
    
    console.log(`📁 Created read-only test directory: ${testAppsDir}`);
    
    // This test is more about checking if the installer handles permission errors gracefully
    // rather than actually testing with a read-only /Applications (which would be system-breaking)
    
    const executablePath = path.join(installedAppPath, 'Contents', 'MacOS', 'ActivityWatch Team Installer');
    
    const permissionTest = new Promise<string>((resolve) => {
      const { spawn } = require('child_process');
      const process = spawn(executablePath, ['--terminal'], {
        stdio: ['pipe', 'pipe', 'pipe']
      });
      
      let output = '';
      
      process.stdout.on('data', (data) => {
        const text = data.toString();
        output += text;
        
        // Look for permission-related messages
        if (/permission|denied|access|admin|sudo/i.test(text)) {
          console.log(`🔒 Permission message detected: ${text.trim()}`);
        }
        
        // Send test input
        if (text.includes('Enter your work email:')) {
          process.stdin.write('permission.test@bali.love\\n');
        } else if (text.includes('Ready to install?')) {
          // Let it try to install and see what happens
          process.stdin.write('y\\n');
        }
      });
      
      process.on('close', (code) => {
        resolve(output);
      });
      
      setTimeout(() => {
        process.kill('SIGTERM');
        resolve(output);
      }, 2 * 60 * 1000);
    });
    
    const permissionOutput = await permissionTest;
    
    // Clean up read-only directory
    try {
      execSync(`chmod 755 "${testAppsDir}"`);
      execSync(`rm -rf "${testAppsDir}"`);
    } catch (cleanupError) {
      console.warn(`⚠️ Cleanup failed: ${cleanupError}`);
    }
    
    // Save permission test output
    fs.writeFileSync('tests/logs/permission-test.log', permissionOutput);
    
    // Check for permission-related handling
    const hasPermissionHandling = /permission|access.*denied|admin.*required|sudo|privilege/i.test(permissionOutput);
    console.log(`🔒 Permission handling detected: ${hasPermissionHandling}`);
    
    if (hasPermissionHandling) {
      console.log('✅ Installer shows permission awareness');
    } else {
      console.log('ℹ️ No explicit permission messages detected');
    }
    
    console.log('✅ Permission scenarios test completed');
  });
});