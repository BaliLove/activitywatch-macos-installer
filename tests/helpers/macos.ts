import { execSync, spawn, ChildProcess } from 'child_process';
import { promises as fs } from 'fs';
import * as path from 'path';

export interface DMGMountInfo {
  mountPoint: string;
  devicePath: string;
  volumeName: string;
}

export interface ProcessInfo {
  pid: number;
  name: string;
  command: string;
}

export class MacOSAutomation {
  private mountedDMGs: string[] = [];
  private spawnedProcesses: ChildProcess[] = [];
  private tempDirectories: string[] = [];

  /**
   * Mount a DMG file and return mount information
   */
  async mountDMG(dmgPath: string): Promise<DMGMountInfo> {
    console.log(`📦 Mounting DMG: ${dmgPath}`);
    
    // Verify DMG exists
    try {
      await fs.access(dmgPath);
    } catch (error) {
      throw new Error(`DMG file not found: ${dmgPath}`);
    }
    
    // Mount the DMG
    const mountCommand = `hdiutil attach "${dmgPath}" -nobrowse -quiet -plist`;
    const result = execSync(mountCommand, { encoding: 'utf8' });
    
    // Parse the plist output to get mount information
    const plistData = result.trim();
    const mountInfo = this.parseDMGMountOutput(plistData);
    
    // Keep track of mounted DMGs for cleanup
    this.mountedDMGs.push(mountInfo.mountPoint);
    
    console.log(`✅ DMG mounted at: ${mountInfo.mountPoint}`);
    return mountInfo;
  }

  /**
   * Unmount a DMG
   */
  async unmountDMG(mountPoint: string): Promise<void> {
    console.log(`📦 Unmounting DMG: ${mountPoint}`);
    
    try {
      execSync(`hdiutil detach "${mountPoint}" -quiet`, { stdio: 'pipe' });
      
      // Remove from tracked mounts
      const index = this.mountedDMGs.indexOf(mountPoint);
      if (index > -1) {
        this.mountedDMGs.splice(index, 1);
      }
      
      console.log(`✅ DMG unmounted: ${mountPoint}`);
    } catch (error) {
      console.warn(`⚠️ Failed to unmount DMG: ${error}`);
      // Try force unmount
      try {
        execSync(`hdiutil detach "${mountPoint}" -force -quiet`, { stdio: 'pipe' });
      } catch (forceError) {
        console.error(`❌ Force unmount also failed: ${forceError}`);
        throw forceError;
      }
    }
  }

  /**
   * Copy app to Applications folder using Finder (simulates drag & drop)
   */
  async installAppToApplications(sourcePath: string, appName: string): Promise<string> {
    console.log(`📱 Installing app to Applications: ${appName}`);
    
    const destinationPath = `/Applications/${appName}`;
    
    // Remove existing installation if present
    try {
      execSync(`rm -rf "${destinationPath}"`, { stdio: 'pipe' });
    } catch (error) {
      // Ignore if app doesn't exist
    }
    
    // Copy the app using AppleScript to simulate Finder drag & drop
    const appleScript = `
      tell application "Finder"
        set sourceApp to POSIX file "${sourcePath}" as alias
        set destinationFolder to folder "Applications" of startup disk
        duplicate sourceApp to destinationFolder with replacing
      end tell
    `;
    
    try {
      execSync(`osascript -e '${appleScript}'`, { stdio: 'pipe' });
      console.log(`✅ App installed to Applications: ${destinationPath}`);
      return destinationPath;
    } catch (error) {
      // Fallback to command line copy
      console.warn(`⚠️ AppleScript copy failed, using cp: ${error}`);
      execSync(`cp -R "${sourcePath}" "${destinationPath}"`);
      return destinationPath;
    }
  }

  /**
   * Launch an app and wait for it to start
   */
  async launchApp(appPath: string, args: string[] = [], timeout: number = 30000): Promise<ProcessInfo> {
    console.log(`🚀 Launching app: ${appPath}`);
    
    const launchCommand = ['open', '-W', appPath];
    if (args.length > 0) {
      launchCommand.push('--args', ...args);
    }
    
    const startTime = Date.now();
    const process = spawn(launchCommand[0], launchCommand.slice(1));
    
    this.spawnedProcesses.push(process);
    
    // Wait for the process to start
    return new Promise((resolve, reject) => {
      const checkInterval = setInterval(async () => {
        if (Date.now() - startTime > timeout) {
          clearInterval(checkInterval);
          reject(new Error(`App launch timeout after ${timeout}ms`));
          return;
        }
        
        try {
          const processes = await this.findProcessesByName(path.basename(appPath, '.app'));
          if (processes.length > 0) {
            clearInterval(checkInterval);
            console.log(`✅ App launched: PID ${processes[0].pid}`);
            resolve(processes[0]);
          }
        } catch (error) {
          // Continue checking
        }
      }, 1000);
      
      process.on('error', (error) => {
        clearInterval(checkInterval);
        reject(error);
      });
    });
  }

  /**
   * Find processes by name
   */
  async findProcessesByName(processName: string): Promise<ProcessInfo[]> {
    try {
      const result = execSync(`ps aux | grep -i "${processName}" | grep -v grep`, { encoding: 'utf8' });
      const lines = result.trim().split('\n').filter(line => line.length > 0);
      
      return lines.map(line => {
        const parts = line.trim().split(/\\s+/);
        return {
          pid: parseInt(parts[1]),
          name: processName,
          command: parts.slice(10).join(' ')
        };
      });
    } catch (error) {
      return [];
    }
  }

  /**
   * Kill a process by PID
   */
  async killProcess(pid: number, signal: string = 'TERM'): Promise<void> {
    console.log(`🔪 Killing process: PID ${pid}`);
    
    try {
      execSync(`kill -${signal} ${pid}`, { stdio: 'pipe' });
      
      // Wait a moment then check if it's really dead
      await this.sleep(2000);
      
      try {
        execSync(`kill -0 ${pid}`, { stdio: 'pipe' });
        // Still alive, force kill
        console.warn(`⚠️ Process ${pid} still alive, force killing...`);
        execSync(`kill -KILL ${pid}`, { stdio: 'pipe' });
      } catch (error) {
        // Process is dead, good
      }
      
      console.log(`✅ Process killed: PID ${pid}`);
    } catch (error) {
      console.warn(`⚠️ Failed to kill process ${pid}: ${error}`);
    }
  }

  /**
   * Set or remove quarantine attribute on a file/app
   */
  async setQuarantineAttribute(filePath: string, enable: boolean = true): Promise<void> {
    console.log(`🔒 ${enable ? 'Adding' : 'Removing'} quarantine attribute: ${filePath}`);
    
    try {
      if (enable) {
        execSync(`xattr -w com.apple.quarantine "0083;$(date +%s);Chrome;$(uuidgen)" "${filePath}"`, { stdio: 'pipe' });
      } else {
        execSync(`xattr -r -d com.apple.quarantine "${filePath}"`, { stdio: 'pipe' });
      }
      console.log(`✅ Quarantine attribute ${enable ? 'added' : 'removed'}: ${filePath}`);
    } catch (error) {
      console.warn(`⚠️ Failed to ${enable ? 'add' : 'remove'} quarantine: ${error}`);
    }
  }

  /**
   * Check if Gatekeeper will block an app
   */
  async checkGatekeeperStatus(appPath: string): Promise<{ blocked: boolean; reason?: string }> {
    console.log(`🛡️ Checking Gatekeeper status: ${appPath}`);
    
    try {
      execSync(`spctl --assess --type execute "${appPath}"`, { stdio: 'pipe' });
      return { blocked: false };
    } catch (error) {
      const errorMessage = error.toString();
      return { 
        blocked: true, 
        reason: errorMessage.includes('rejected') ? 'unsigned' : 'unknown'
      };
    }
  }

  /**
   * Click through Gatekeeper dialog using AppleScript
   */
  async handleGatekeeperDialog(action: 'open' | 'cancel' = 'open'): Promise<void> {
    console.log(`🛡️ Handling Gatekeeper dialog: ${action}`);
    
    const appleScript = action === 'open' 
      ? `
        tell application "System Events"
          repeat while exists (processes where name is "SecurityAgent")
            if exists button "Open" of window 1 of application process "SecurityAgent" then
              click button "Open" of window 1 of application process "SecurityAgent"
              exit repeat
            end if
            delay 0.5
          end repeat
        end tell
      `
      : `
        tell application "System Events"
          repeat while exists (processes where name is "SecurityAgent")
            if exists button "Cancel" of window 1 of application process "SecurityAgent" then
              click button "Cancel" of window 1 of application process "SecurityAgent"
              exit repeat
            end if
            delay 0.5
          end repeat
        end tell
      `;
    
    try {
      execSync(`osascript -e '${appleScript}'`, { timeout: 10000 });
      console.log(`✅ Gatekeeper dialog handled: ${action}`);
    } catch (error) {
      console.warn(`⚠️ Failed to handle Gatekeeper dialog: ${error}`);
    }
  }

  /**
   * Simulate network connectivity changes
   */
  async setNetworkConnectivity(connected: boolean): Promise<void> {
    console.log(`🌐 ${connected ? 'Enabling' : 'Disabling'} network connectivity`);
    
    try {
      // Get the primary network interface
      const interface = execSync(`route get default | grep interface | awk '{print $2}'`, { encoding: 'utf8' }).trim();
      
      if (interface) {
        if (connected) {
          execSync(`sudo ifconfig ${interface} up`, { stdio: 'pipe' });
        } else {
          execSync(`sudo ifconfig ${interface} down`, { stdio: 'pipe' });
        }
        console.log(`✅ Network connectivity ${connected ? 'enabled' : 'disabled'}`);
      }
    } catch (error) {
      console.warn(`⚠️ Failed to change network connectivity: ${error}`);
      console.warn(`ℹ️ This may require sudo privileges`);
    }
  }

  /**
   * Wait for HTTP endpoint to become available
   */
  async waitForHTTPEndpoint(url: string, timeout: number = 60000): Promise<boolean> {
    console.log(`🌐 Waiting for HTTP endpoint: ${url}`);
    
    const startTime = Date.now();
    
    while (Date.now() - startTime < timeout) {
      try {
        execSync(`curl -f -s "${url}" > /dev/null`, { stdio: 'pipe' });
        console.log(`✅ HTTP endpoint available: ${url}`);
        return true;
      } catch (error) {
        await this.sleep(2000);
      }
    }
    
    console.warn(`⚠️ HTTP endpoint timeout: ${url}`);
    return false;
  }

  /**
   * Take a screenshot
   */
  async takeScreenshot(outputPath: string): Promise<void> {
    console.log(`📸 Taking screenshot: ${outputPath}`);
    
    try {
      execSync(`screencapture -x "${outputPath}"`, { stdio: 'pipe' });
      console.log(`✅ Screenshot saved: ${outputPath}`);
    } catch (error) {
      console.warn(`⚠️ Failed to take screenshot: ${error}`);
    }
  }

  /**
   * Create a temporary directory
   */
  async createTempDirectory(prefix: string = 'aw-test-'): Promise<string> {
    const tempDir = `/tmp/${prefix}${Date.now()}-${Math.random().toString(36).substring(7)}`;
    await fs.mkdir(tempDir, { recursive: true });
    this.tempDirectories.push(tempDir);
    console.log(`📁 Created temp directory: ${tempDir}`);
    return tempDir;
  }

  /**
   * Sleep for specified milliseconds
   */
  async sleep(ms: number): Promise<void> {
    return new Promise(resolve => setTimeout(resolve, ms));
  }

  /**
   * Cleanup all resources
   */
  async cleanup(): Promise<void> {
    console.log('🧹 Cleaning up macOS automation resources...');
    
    // Kill spawned processes
    for (const process of this.spawnedProcesses) {
      if (!process.killed) {
        process.kill('SIGTERM');
      }
    }
    this.spawnedProcesses = [];
    
    // Unmount DMGs
    for (const mountPoint of this.mountedDMGs) {
      try {
        await this.unmountDMG(mountPoint);
      } catch (error) {
        console.warn(`⚠️ Failed to unmount ${mountPoint}: ${error}`);
      }
    }
    this.mountedDMGs = [];
    
    // Clean up temp directories
    for (const tempDir of this.tempDirectories) {
      try {
        execSync(`rm -rf "${tempDir}"`, { stdio: 'pipe' });
        console.log(`🗑️ Cleaned up temp directory: ${tempDir}`);
      } catch (error) {
        console.warn(`⚠️ Failed to clean up ${tempDir}: ${error}`);
      }
    }
    this.tempDirectories = [];
    
    console.log('✅ macOS automation cleanup completed');
  }

  /**
   * Parse DMG mount output to extract mount information
   */
  private parseDMGMountOutput(plistData: string): DMGMountInfo {
    // Parse plist data to extract mount point
    // This is a simplified parser - in production you might want to use a proper plist parser
    const lines = plistData.split('\n');
    let mountPoint = '';
    let devicePath = '';
    let volumeName = '';
    
    // Look for mount-point in the plist output
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].includes('<key>mount-point</key>')) {
        const nextLine = lines[i + 1];
        const match = nextLine.match(/<string>(.*)<\\/string>/);
        if (match) {
          mountPoint = match[1];
        }
      }
      if (lines[i].includes('<key>dev-entry</key>')) {
        const nextLine = lines[i + 1];
        const match = nextLine.match(/<string>(.*)<\\/string>/);
        if (match) {
          devicePath = match[1];
        }
      }
    }
    
    // Extract volume name from mount point
    volumeName = path.basename(mountPoint);
    
    if (!mountPoint) {
      throw new Error('Failed to parse DMG mount output');
    }
    
    return { mountPoint, devicePath, volumeName };
  }
}