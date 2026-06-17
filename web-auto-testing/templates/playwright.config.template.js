const { defineConfig, devices } = require('@playwright/test');

/**
 * Playwright 配置文件
 * 用于 {{PROJECT_NAME}} 的自动化测试
 */
module.exports = defineConfig({
  // 测试文件匹配模式
  testDir: './tests',

  // 完全并行执行所有测试
  fullyParallel: true,

  // 在 CI 中禁止重试，本地开发允许重试
  retries: process.env.CI ? 0 : 2,

  // 并行 worker 数量
  workers: process.env.CI ? 2 : 4,

  // 测试报告器配置
  reporter: [
    // HTML 报告（带附件）
    ['html', {
      open: 'never',
      outputFolder: 'playwright-report',
    }],

    // JUnit 报告（用于 Jenkins）
    ['junit', {
      outputFile: 'junit-results.xml',
    }],

    // JSON 报告
    ['json', {
      outputFile: 'test-results.json',
    }],

    // 命令行报告
    ['list'],
  ],

  // 全局配置
  use: {
    // 基础 URL（支持环境变量覆盖）
    baseURL: process.env.BASE_URL || '{{BASE_URL}}',

    // 测试超时
    actionTimeout: 10 * 1000,
    navigationTimeout: 30 * 1000,

    // 截图配置
    screenshot: process.env.CI ? 'only-on-failure' : 'on',

    // 视频录制配置
    video: process.env.CI ? 'retain-on-failure' : 'on',

    // 追踪配置（用于调试）
    trace: process.env.CI ? 'retain-on-failure' : 'on-first-retry',

    // 浏览器视口大小
    viewport: { width: 1280, height: 720 },

    // 忽略 HTTPS 错误
    ignoreHTTPSErrors: true,

    // 使用系统安装的 Chrome 浏览器（无需下载 Playwright 浏览器）
    // 这可以避免网络下载问题，直接使用本机已安装的 Chrome
    channel: 'chrome',
  },

  // 测试项目配置（多浏览器）
  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        // 使用系统 Chrome
        channel: 'chrome',
        // 本地开发时显示浏览器窗口（方便调试），CI 环境使用无头模式
        headless: process.env.CI ? true : false,
      },
    },

    // Firefox 和 Safari 需要额外安装浏览器，如需使用请取消注释
    // {
    //   name: 'firefox',
    //   use: { ...devices['Desktop Firefox'] },
    // },
    //
    // {
    //   name: 'webkit',
    //   use: { ...devices['Desktop Safari'] },
    // },

    // 移动设备测试
    {
      name: 'Mobile Chrome',
      use: {
        ...devices['Pixel 5'],
        channel: 'chrome',
        headless: process.env.CI ? true : false,
      },
    },

    // iOS Safari 需要额外的 webkit 浏览器
    // {
    //   name: 'Mobile Safari',
    //   use: { ...devices['iPhone 12'] },
    // },
  ],

  // 开发服务器（可选）
  // webServer: {
  //   command: 'npm run start',
  //   port: 3000,
  //   timeout: 120 * 1000,
  //   reuseExistingServer: !process.env.CI,
  // },
});
