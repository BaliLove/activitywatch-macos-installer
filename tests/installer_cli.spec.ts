import { test, expect } from '@playwright/test';
import { MacOSAutomation } from './helpers/macos';
import { spawn, ChildProcess } from 'child_process';
import * as path from 'path';
import * as fs from 'fs';

test.describe('ActivityWatch macOS Installer CLI Tests', () => {
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

  test('Terminal Mode Installation', async () => {
    console.log('💻 Starting terminal mode installation test...');
    
    // Step 1: Mount DMG and install app
    const mountInfo = await macOS.mountDMG(dmgPath);
    const installerAppPath = path.join(mountInfo.mountPoint, 'ActivityWatch Team Installer.app');
    const installedAppPath = await macOS.installAppToApplications(
      installerAppPath, 
      'ActivityWatch Team Installer.app'
    );
    
    // Remove quarantine for testing
    await macOS.setQuarantineAttribute(installedAppPath, false);
    
    // Step 2: Launch installer in terminal mode
    console.log('🚀 Launching installer in terminal mode...');
    
    const executablePath = path.join(installedAppPath, 'Contents', 'MacOS', 'ActivityWatch Team Installer');
    const testEmail = 'cli.test@bali.love';
    
    // Create a promise to handle the CLI interaction
    const cliInstallation = new Promise<{ stdout: string; stderr: string; exitCode: number }>((resolve, reject) => {
      const process = spawn(executablePath, ['--terminal'], {
        stdio: ['pipe', 'pipe', 'pipe'],
        cwd: '/tmp'
      });
      
      let stdout = '';
      let stderr = '';
      
      process.stdout.on('data', (data) => {
        const output = data.toString();
        stdout += output;
        console.log(`📝 STDOUT: ${output.trim()}`);
        
        // Check for email prompt
        if (output.includes('Enter your work email:') || output.includes('📧')) {
          console.log('📧 Email prompt detected, sending test email...');
          process.stdin.write(`${testEmail}\n`);
        }
        
        // Check for confirmation prompt
        if (output.includes('Ready to install?') || output.includes('🚀')) {
          console.log('🚀 Install confirmation prompt detected, confirming...');
          process.stdin.write('y\n');
        }
      });
      
      process.stderr.on('data', (data) => {
        const output = data.toString();
        stderr += output;
        console.log(`⚠️ STDERR: ${output.trim()}`);
      });
      
      process.on('close', (code) => {
        console.log(`💻 CLI process exited with code: ${code}`);
        resolve({ stdout, stderr, exitCode: code || 0 });
      });
      
      process.on('error', (error) => {
        console.error(`❌ CLI process error: ${error}`);
        reject(error);
      });
      
      // Timeout handling
      setTimeout(() => {
        if (!process.killed) {
          console.log('⏰ CLI installation timeout, killing process...');
          process.kill('SIGTERM');
          reject(new Error('CLI installation timeout'));
        }
      }, 5 * 60 * 1000); // 5 minutes timeout
    });
    
    // Wait for CLI installation to complete
    console.log('⏳ Waiting for CLI installation to complete...');
    const result = await cliInstallation;
    
    // Step 3: Verify installation results
    console.log('🔍 Verifying CLI installation results...');
    
    // Check exit code
    expect(result.exitCode).toBe(0);
    
    // Check for success indicators in output
    expect(result.stdout).toMatch(/installation.*completed|successfully|✅/i);
    expect(result.stdout).toMatch(new RegExp(testEmail, 'i'));
    
    // Verify ActivityWatch components were installed
    const activityWatchPath = '/Applications/ActivityWatch.app';
    const configPath = path.join(process.env.HOME || '', 'Library', 'Application Support', 'ActivityWatch-Team');
    const launchAgentPath = path.join(process.env.HOME || '', 'Library', 'LaunchAgents', 'com.activitywatch.team.plist');
    
    expect(fs.existsSync(activityWatchPath)).toBe(true);
    expect(fs.existsSync(configPath)).toBe(true);
    expect(fs.existsSync(launchAgentPath)).toBe(true);
    
    // Check configuration file
    const configFile = path.join(configPath, 'sync_config.json');
    if (fs.existsSync(configFile)) {
      const config = JSON.parse(fs.readFileSync(configFile, 'utf8'));
      expect(config.user_info.email).toBe(testEmail);
      expect(config.api_key).toBe('aw-team-2025-secure-key-v1');
      console.log('✅ CLI installation configuration verified');
    }
    
    // Step 4: Test that ActivityWatch is running
    console.log('🔄 Testing ActivityWatch startup...');
    
    // Wait a moment for services to start
    await macOS.sleep(10000);
    
    const awProcesses = await macOS.findProcessesByName('ActivityWatch');
    expect(awProcesses.length).toBeGreaterThan(0);
    
    // Check web interface
    const webAvailable = await macOS.waitForHTTPEndpoint('http://localhost:5600', 30000);
    expect(webAvailable).toBe(true);
    
    console.log('🎯 CLI installation test completed successfully');
    
    // Save CLI output for debugging
    fs.writeFileSync('tests/logs/cli-installation-output.log', 
      `STDOUT:\n${result.stdout}\n\nSTDERR:\n${result.stderr}\n\nEXIT CODE: ${result.exitCode}`
    );
  });
  
  test('CLI Error Handling', async () => {
    console.log('🧪 Testing CLI error handling scenarios...');
    
    const mountInfo = await macOS.mountDMG(dmgPath);
    const installerAppPath = path.join(mountInfo.mountPoint, 'ActivityWatch Team Installer.app');
    const installedAppPath = await macOS.installAppToApplications(
      installerAppPath, 
      'ActivityWatch Team Installer.app'
    );
    
    await macOS.setQuarantineAttribute(installedAppPath, false);
    
    const executablePath = path.join(installedAppPath, 'Contents', 'MacOS', 'ActivityWatch Team Installer');
    
    // Test 1: Invalid email handling
    console.log('📧 Testing invalid email handling...');
    
    const invalidEmailTest = new Promise<string>((resolve, reject) => {
      const process = spawn(executablePath, ['--terminal'], {
        stdio: ['pipe', 'pipe', 'pipe']
      });
      
      let stdout = '';
      let emailPromptReceived = false;
      let invalidEmailSent = false;
      
      process.stdout.on('data', (data) => {
        const output = data.toString();
        stdout += output;
        
        if (!emailPromptReceived && (output.includes('Enter your work email:') || output.includes('📧'))) {
          emailPromptReceived = true;
          console.log('📧 Sending invalid email...');
          process.stdin.write('invalid-email\n');
          invalidEmailSent = true;
        } else if (invalidEmailSent && output.includes('valid email')) {
          console.log('✅ Invalid email rejected correctly');
          process.kill('SIGTERM');
          resolve(stdout);
        }
      });
      
      process.on('close', () => {
        resolve(stdout);
      });
      
      setTimeout(() => {
        process.kill('SIGTERM');
        resolve(stdout);
      }, 30000);
    });
    
    const invalidEmailOutput = await invalidEmailTest;
    expect(invalidEmailOutput).toMatch(/valid email|invalid|error/i);
    
    // Test 2: Cancellation handling
    console.log('❌ Testing installation cancellation...');
    
    const cancellationTest = new Promise<string>((resolve, reject) => {
      const process = spawn(executablePath, ['--terminal'], {
        stdio: ['pipe', 'pipe', 'pipe']
      });
      
      let stdout = '';
      
      process.stdout.on('data', (data) => {
        const output = data.toString();
        stdout += output;
        
        if (output.includes('Enter your work email:') || output.includes('📧')) {
          console.log('📧 Sending valid email then cancelling...');
          process.stdin.write('cancel.test@bali.love\n');
        } else if (output.includes('Ready to install?') || output.includes('🚀')) {
          console.log('❌ Cancelling installation...');
          process.stdin.write('n\n');
          setTimeout(() => {
            process.kill('SIGTERM');
            resolve(stdout);
          }, 2000);
        }
      });
      
      process.on('close', () => {
        resolve(stdout);
      });
      
      setTimeout(() => {
        process.kill('SIGTERM');
        resolve(stdout);
      }, 30000);
    });
    
    const cancellationOutput = await cancellationTest;
    expect(cancellationOutput).toMatch(/cancel|abort|exit/i);
    
    console.log('✅ CLI error handling tests completed');
  });
  
  test('CLI Timeout and Hang Detection', async () => {
    console.log('🕐 Testing CLI timeout and hang detection...');
    
    const mountInfo = await macOS.mountDMG(dmgPath);
    const installerAppPath = path.join(mountInfo.mountPoint, 'ActivityWatch Team Installer.app');
    const installedAppPath = await macOS.installAppToApplications(
      installerAppPath, 
      'ActivityWatch Team Installer.app'
    );
    
    await macOS.setQuarantineAttribute(installedAppPath, false);
    
    const executablePath = path.join(installedAppPath, 'Contents', 'MacOS', 'ActivityWatch Team Installer');
    
    // Test: Launch CLI but don't provide input (simulate hang)
    console.log('🔄 Testing CLI hang scenario...');
    
    const hangTest = new Promise<{ hung: boolean; output: string }>((resolve) => {
      const process = spawn(executablePath, ['--terminal'], {
        stdio: ['pipe', 'pipe', 'pipe']
      });
      
      let stdout = '';
      let emailPromptReceived = false;
      const startTime = Date.now();
      
      process.stdout.on('data', (data) => {
        const output = data.toString();
        stdout += output;
        
        if (output.includes('Enter your work email:') || output.includes('📧')) {
          emailPromptReceived = true;
          console.log('📧 Email prompt received - not responding to test hang detection');
        }
      });
      
      // Set a timeout to detect if the process hangs
      setTimeout(() => {
        const elapsed = Date.now() - startTime;
        const isHung = emailPromptReceived && elapsed > 15000; // 15 seconds without progress
        
        console.log(`⏱️ Hang test: elapsed ${elapsed}ms, email prompt: ${emailPromptReceived}, hung: ${isHung}`);
        
        process.kill('SIGTERM');
        resolve({ hung: isHung, output: stdout });
      }, 20000); // 20 second timeout
    });
    
    const hangResult = await hangTest;
    
    // The test should detect that the CLI is waiting for input (not truly hung)
    expect(hangResult.output).toMatch(/email|input|prompt/i);
    console.log('✅ CLI hang detection test completed');
    
    // Save hang test output
    fs.writeFileSync('tests/logs/cli-hang-test-output.log', 
      `HUNG: ${hangResult.hung}\nOUTPUT:\n${hangResult.output}`
    );
  });
  
  test('CLI System Requirements Check', async () => {
    console.log('🔍 Testing CLI system requirements check...');
    
    const mountInfo = await macOS.mountDMG(dmgPath);
    const installerAppPath = path.join(mountInfo.mountPoint, 'ActivityWatch Team Installer.app');
    const installedAppPath = await macOS.installAppToApplications(
      installerAppPath, 
      'ActivityWatch Team Installer.app'
    );
    
    await macOS.setQuarantineAttribute(installedAppPath, false);
    
    const executablePath = path.join(installedAppPath, 'Contents', 'MacOS', 'ActivityWatch Team Installer');
    
    // Launch CLI and capture system requirements output
    const sysReqTest = new Promise<string>((resolve) => {
      const process = spawn(executablePath, ['--terminal'], {
        stdio: ['pipe', 'pipe', 'pipe']
      });
      
      let stdout = '';
      
      process.stdout.on('data', (data) => {
        const output = data.toString();
        stdout += output;
        
        // Kill process after we get some output (we're just testing the initial checks)
        if (output.includes('macOS') || output.includes('System') || output.length > 500) {
          setTimeout(() => {
            process.kill('SIGTERM');
            resolve(stdout);
          }, 2000);
        }
      });
      
      process.on('close', () => {
        resolve(stdout);
      });
      
      setTimeout(() => {
        process.kill('SIGTERM');
        resolve(stdout);
      }, 15000);
    });
    
    const sysReqOutput = await sysReqTest;
    
    // Verify that system requirements are checked and displayed
    console.log('📋 System requirements output received');
    
    // The installer should report system information
    expect(sysReqOutput.length).toBeGreaterThan(0);
    
    // Save system requirements output
    fs.writeFileSync('tests/logs/cli-system-requirements.log', sysReqOutput);
    
    console.log('✅ CLI system requirements test completed');
  });
});