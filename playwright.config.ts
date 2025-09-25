import { defineConfig, devices } from '@playwright/test';

/**
 * See https://playwright.dev/docs/test-configuration.
 */
export default defineConfig({
  testDir: './tests',
  /* Run tests in files in parallel */
  fullyParallel: true,
  /* Fail the build on CI if you accidentally left test.only in the source code. */
  forbidOnly: !!process.env.CI,
  /* Retry on CI only */
  retries: process.env.CI ? 2 : 0,
  /* Opt out of parallel tests on CI. */
  workers: process.env.CI ? 1 : undefined,
  /* Reporter to use. See https://playwright.dev/docs/test-reporters */
  reporter: [
    ['html', { outputFolder: 'tests/playwright-report' }],
    ['json', { outputFile: 'tests/playwright-report/results.json' }],
    ['github']
  ],
  /* Shared settings for all the projects below. See https://playwright.dev/docs/api/class-testoptions. */
  use: {
    /* Base URL to use in actions like `await page.goto('/')`. */
    // baseURL: 'http://127.0.0.1:3000',

    /* Collect trace when retrying the failed test. See https://playwright.dev/docs/trace-viewer */
    trace: 'on-first-retry',
    
    /* Capture screenshot on failure */
    screenshot: 'only-on-failure',
    
    /* Capture video on failure */
    video: 'retain-on-failure',
    
    /* Global timeout for all tests */
    actionTimeout: 30 * 1000, // 30 seconds
    navigationTimeout: 60 * 1000, // 60 seconds
  },

  /* Configure projects for different browsers/scenarios */
  projects: [
    {
      name: 'macos-installer-tests',
      testMatch: '**/*.spec.ts',
      use: {
        ...devices['Desktop Chrome'],
        // Increase timeouts for macOS system interactions
        actionTimeout: 60 * 1000, // 60 seconds for system actions
        
        // Enable video recording for debugging
        video: {
          mode: 'on',
          size: { width: 1280, height: 720 }
        },
        
        // Enable tracing for debugging
        trace: 'on',
      },
    },
  ],

  /* Global test timeout */
  timeout: 10 * 60 * 1000, // 10 minutes per test (installer can be slow)
  
  /* Global setup and teardown */
  globalSetup: require.resolve('./tests/global-setup.ts'),
  globalTeardown: require.resolve('./tests/global-teardown.ts'),
});