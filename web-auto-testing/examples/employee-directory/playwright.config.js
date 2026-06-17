const { defineConfig, devices } = require('@playwright/test');

/**
 * Playwright 配置文件
 * 用于员工通信录示例的自动化测试
 */
module.exports = defineConfig({
  // 测试文件位置
  testDir: './',
  testMatch: '**/*.spec.js',

  // 完全并行执行所有测试
  fullyParallel: true,

  // 在 CI 中重试 2 次，本地不重试
  retries: process.env.CI ? 2 : 0,

  // 并行 worker 数量
  workers: process.env.CI ? 1 : undefined,

  // 测试报告器配置
  reporter: [
    // HTML 报告
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
    // 基础 URL（通过环境变量配置）
    baseURL: process.env.TEST_URL || 'http://localhost:3000',

    // 测试超时
    actionTimeout: 10 * 1000,
    navigationTimeout: 30 * 1000,

    // 截图配置
    screenshot: 'only-on-failure',

    // 视频录制配置
    video: 'retain-on-failure',

    // 追踪配置
    trace: 'retain-on-failure',

    // 浏览器视口大小
    viewport: { width: 1920, height: 1080 },

    // 忽略 HTTPS 错误
    ignoreHTTPSErrors: true,

    // 使用系统安装的 Chrome 浏览器（无需下载 Playwright 浏览器）
    channel: 'chrome',
  },

  // 测试项目配置（多浏览器）
  projects: [
    {
      name: 'chromium',
      use: {
        ...devices['Desktop Chrome'],
        // VSCode 中默认开启有头模式，方便调试
        headless: process.env.CI ? true : false,
        // 减慢执行速度，便于观察
        launchOptions: {
          slowMo: 50,
        },
        // 使用系统 Chrome
        channel: 'chrome',
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
  ],
});
