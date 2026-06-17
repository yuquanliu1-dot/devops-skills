# 测试产物管理指南

测试产物（Artifacts）包括截图、视频、追踪文件等，是调试和问题定位的重要资源。本文档详细说明如何有效管理测试产物。

---

## 目录

1. [产物类型](#产物类型)
2. [命名规范](#命名规范)
3. [配置策略](#配置策略)
4. [CI/CD 集成](#cicd-集成)
5. [存储策略](#存储策略)
6. [最佳实践](#最佳实践)

---

## 产物类型

### 1. 截图（Screenshots）

**用途**：直观展示测试失败时的页面状态

**配置**：
```javascript
// playwright.config.js
export default defineConfig({
  use: {
    // 失败时自动截图
    screenshot: 'only-on-failure', // 'on' | 'only-on-failure' | 'off'

    // 截图保存路径
    screenshotsPath: 'artifacts/screenshots/',
  },
});
```

**手动截图**：
```javascript
// 完整页面截图
await page.screenshot({
  path: 'artifacts/full-page.png',
  fullPage: true
});

// 仅视口截图
await page.screenshot({
  path: 'artifacts/viewport.png',
  fullPage: false
});

// 元素截图
await page.locator('.chart').screenshot({
  path: 'artifacts/chart.png'
});

// 背景透明截图
await page.screenshot({
  path: 'artifacts/transparent.png',
  transparent: true
});
```

### 2. 视频（Videos）

**用途**：记录测试执行过程，帮助重现问题

**配置**：
```javascript
// playwright.config.js
export default defineConfig({
  use: {
    // 仅失败时保留视频
    video: 'retain-on-failure', // 'on' | 'retain-on-failure' | 'off'

    // 视频保存路径
    videosPath: 'artifacts/videos/',

    // 视频尺寸
    videoSize: { width: 1280, height: 720 },
  },
});
```

**视频文件信息**：
- 格式：WebM
- 包含：完整测试执行过程
- 文件大小：取决于测试时长

### 3. 追踪（Traces）

**用途**：完整的测试执行记录，包含所有调试信息

**配置**：
```javascript
// playwright.config.js
export default defineConfig({
  use: {
    // 重试时记录追踪
    trace: 'on-first-retry', // 'on' | 'on-first-retry' | 'retain-on-failure' | 'off'

    // 追踪保存路径
    tracesDir: 'artifacts/traces/',
  },
});
```

**查看追踪**：
```bash
npx playwright show-trace artifacts/trace.zip
```

**追踪包含**：
- 每个操作的 DOM 快照
- 网络请求和响应
- 控制台日志
- 时间线
- 源代码位置

### 4. 测试报告（Reports）

**HTML 报告**：
```javascript
// playwright.config.js
export default defineConfig({
  reporter: [
    ['html', { outputFolder: 'playwright-report' }]
  ],
});
```

**JSON 报告**：
```javascript
reporter: [
  ['json', { outputFile: 'test-results.json' }]
]
```

**JUnit 报告**：
```javascript
reporter: [
  ['junit', { outputFile: 'junit-results.xml' }]
]
```

---

## 命名规范

### 推荐命名格式

```
{feature}-{scenario}-{step}-{status}.{ext}
```

### 示例

| 类型 | 命名示例 | 说明 |
|------|---------|------|
| 截图 | `login-success-after-submit.png` | 登录成功后截图 |
| 截图 | `login-failed-invalid-credentials.png` | 登录失败截图 |
| 截图 | `checkout-payment-error.png` | 支付错误截图 |
| 视频 | `search-empty-results.webm` | 搜索无结果视频 |
| 追踪 | `checkout-complete.zip` | 完整结账流程追踪 |

### 动态命名

```javascript
// 包含时间戳
const timestamp = new Date().toISOString().replace(/[:.]/g, '-');
await page.screenshot({
  path: `artifacts/login-${timestamp}.png`
});

// 包含测试信息
await page.screenshot({
  path: `artifacts/${test.info().title.replace(/\s+/g, '-')}.png`
});

// 包含用户信息
const username = 'test-user-123';
await page.screenshot({
  path: `artifacts/profile-${username}.png`
});
```

---

## 配置策略

### 开发环境配置

```javascript
// playwright.config.js (开发)
export default defineConfig({
  use: {
    screenshot: 'only-on-failure',
    video: 'off',
    trace: 'retain-on-failure',
  },
});
```

### CI/CD 环境配置

```javascript
// playwright.config.js (CI)
export default defineConfig({
  use: {
    screenshot: 'only-on-failure',
    video: 'retain-on-failure',
    trace: 'on-first-retry',
  },
});
```

### 调试配置

```javascript
// playwright.config.js (调试)
export default defineConfig({
  use: {
    screenshot: 'on',
    video: 'on',
    trace: 'on',
  },
});
```

### 条件配置

```javascript
// playwright.config.js
export default defineConfig({
  use: {
    screenshot: process.env.CI ? 'only-on-failure' : 'on',
    video: process.env.CI ? 'retain-on-failure' : 'off',
    trace: process.env.DEBUG ? 'on' : 'on-first-retry',
  },
});
```

---

## CI/CD 集成

### GitHub Actions

```yaml
# .github/workflows/playwright.yml
name: Playwright Tests

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest

    steps:
      - uses: actions/checkout@v3

      - name: Setup Node.js
        uses: actions/setup-node@v3
        with:
          node-version: 18

      - name: Install dependencies
        run: npm ci

      - name: Install Playwright browsers
        run: npx playwright install --with-deps

      - name: Run tests
        run: npx playwright test
        env:
          CI: true

      - name: Upload test artifacts
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-artifacts
          path: |
            playwright-report/
            artifacts/
            test-results/
          retention-days: 30

      - name: Upload report
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report
          path: playwright-report/
          retention-days: 30

      - name: Comment PR with results
        if: github.event_name == 'pull_request'
        uses: actions/github-script@v6
        with:
          script: |
            const fs = require('fs');
            const results = JSON.parse(fs.readFileSync('test-results.json', 'utf8'));
            const passed = results.stats.expected;
            const failed = results.stats.unexpected;
            const flaky = results.stats.flaky;

            const body = `
            ## 测试结果
            - ✅ 通过: ${passed}
            - ❌ 失败: ${failed}
            - ⚠️ 不稳定: ${flaky}

            [查看完整报告](https://github.com/${{ github.repository }}/actions/runs/${{ github.run_id }})
            `;

            github.rest.issues.createComment({
              issue_number: context.issue.number,
              owner: context.repo.owner,
              repo: context.repo.repo,
              body: body
            });
```

### Jenkins Pipeline

```groovy
// Jenkinsfile
pipeline {
  agent any

  stages {
    stage('Setup') {
      steps {
        sh 'npm ci'
        sh 'npx playwright install --with-deps'
      }
    }

    stage('Test') {
      steps {
        sh 'npx playwright test'
      }
    }

    stage('Report') {
      steps {
        // 发布 HTML 报告
        publishHTML([
            reportDir: 'playwright-report',
            reportFiles: 'index.html',
            reportName: 'Playwright Report',
            keepAll: true,
            alwaysLinkToLastBuild: true
        ])

        // 发布 JUnit 结果
        junit 'junit-results.xml'

        // 归档产物
        archiveArtifacts artifacts: 'artifacts/**/*', allowEmptyArchive: true
        archiveArtifacts artifacts: 'playwright-report/**/*', allowEmptyArchive: true
      }
    }
  }

  post {
    always {
      // 清理旧产物
      cleanWs()
    }
  }
}
```

### GitLab CI

```yaml
# .gitlab-ci.yml
stages:
  - test
  - report

test:
  stage: test
  image: mcr.microsoft.com/playwright:v1.40.0-jammy
  script:
    - npm ci
    - npx playwright test
  artifacts:
    when: always
    paths:
      - playwright-report/
      - artifacts/
      - test-results/
    reports:
      junit: junit-results.xml
    expire_in: 30 days
  only:
    - merge_requests
    - main

pages:
  stage: report
  dependencies:
    - test
  script:
    - mkdir public
    - cp -r playwright-report/* public/
  artifacts:
    paths:
      - public
  only:
    - main
```

---

## 存储策略

### 本地存储

**目录结构**：
```
artifacts/
├── screenshots/
│   ├── login/
│   │   ├── success.png
│   │   └── failure.png
│   └── checkout/
│       └── payment-error.png
├── videos/
│   ├── test1.webm
│   └── test2.webm
└── traces/
    ├── trace1.zip
    └── trace2.zip
```

### 云存储

**AWS S3**：
```javascript
// 上传到 S3
const AWS = require('aws-sdk');
const s3 = new AWS.S3();

async function uploadArtifacts() {
  const fs = require('fs');
  const files = fs.readdirSync('artifacts');

  for (const file of files) {
    const content = fs.readFileSync(`artifacts/${file}`);
    await s3.putObject({
      Bucket: 'test-artifacts',
      Key: `${process.env.BUILD_ID}/${file}`,
      Body: content
    }).promise();
  }
}
```

**Azure Blob Storage**：
```javascript
const { BlobServiceClient } = require('@azure/storage-blob');

async function uploadArtifacts() {
  const blobServiceClient = BlobServiceClient.fromConnectionString(
    process.env.AZURE_CONNECTION_STRING
  );
  const containerClient = blobServiceClient.getContainerClient('test-artifacts');

  for (const file of fs.readdirSync('artifacts')) {
    const blockBlobClient = containerClient.getBlockBlobClient(file);
    await blockBlobClient.uploadFile(`artifacts/${file}`);
  }
}
```

---

## 最佳实践

### 1. 失败时自动收集产物

```javascript
// tests/fixtures/artifacts.js
const { test } = require('@playwright/test');

test.afterEach(async ({ page }, testInfo) => {
  if (testInfo.status !== testInfo.expectedStatus) {
    // 测试失败时截图
    await page.screenshot({
      path: `artifacts/${testInfo.title}-failed.png`
    });

    // 记录控制台日志
    const logs = await page.evaluate(() => {
      return window.consoleLogs || [];
    });
    console.log('Console logs:', logs);
  }
});
```

### 2. 条件记录产物

```javascript
// 只在关键步骤截图
async function captureStep(page, stepName) {
  await page.screenshot({
    path: `artifacts/${stepName}.png`
  });
}

// 在测试中使用
await captureStep(page, 'before-login');
await loginPage.login('user', 'pass');
await captureStep(page, 'after-login');
```

### 3. 清理旧产物

```javascript
// scripts/cleanup-artifacts.js
const fs = require('fs');
const path = require('path');
const MAX_AGE_DAYS = 30;

function cleanupOldArtifacts(artifactsDir) {
  const now = Date.now();
  const maxAge = MAX_AGE_DAYS * 24 * 60 * 60 * 1000;

  const files = fs.readdirSync(artifactsDir);

  for (const file of files) {
    const filePath = path.join(artifactsDir, file);
    const stats = fs.statSync(filePath);
    const age = now - stats.mtime.getTime();

    if (age > maxAge) {
      fs.unlinkSync(filePath);
      console.log(`Deleted: ${file}`);
    }
  }
}

cleanupOldArtifacts('artifacts');
```

### 4. 压缩大型产物

```javascript
// 压缩视频和追踪文件
const archiver = require('archiver');
const fs = require('fs');

async function compressArtifacts() {
  const output = fs.createWriteStream('artifacts.zip');
  const archive = archiver('zip');

  archive.pipe(output);
  archive.directory('artifacts/', false);
  await archive.finalize();
}

compressArtifacts();
```

### 5. 设置产物保留期限

```javascript
// playwright.config.js
export default defineConfig({
  reporter: [
    ['html', {
      outputFolder: 'playwright-report',
      // 配置服务器清除旧报告
      host: '0.0.0.0',
      port: 9323,
    }]
  ],
});
```

---

## 示例配置文件

### 完整的 playwright.config.js

```javascript
import { defineConfig } from '@playwright/test';

export default defineConfig({
  // 测试文件目录
  testDir: './tests/e2e',

  // 超时配置
  timeout: 30000,
  expect: {
    timeout: 5000,
  },

  // 失败重试
  retries: process.env.CI ? 2 : 0,

  // 并行执行
  fullyParallel: true,
  workers: process.env.CI ? 1 : undefined,

  // 报告器
  reporter: [
    ['html', { outputFolder: 'playwright-report' }],
    ['json', { outputFile: 'test-results.json' }],
    ['junit', { outputFile: 'junit-results.xml' }],
    ['list'],
  ],

  // 产物配置
  use: {
    // 基础 URL
    baseURL: process.env.BASE_URL || 'http://localhost:3000',

    // 截图
    screenshot: 'only-on-failure',
    screenshotsPath: 'artifacts/screenshots/',

    // 视频
    video: process.env.CI ? 'retain-on-failure' : 'off',
    videosPath: 'artifacts/videos/',

    // 追踪
    trace: 'on-first-retry',
    tracesDir: 'artifacts/traces/',

    // 浏览器视口
    viewport: { width: 1280, height: 720 },
  },

  // 测试服务器
  webServer: {
    command: 'npm run dev',
    url: 'http://localhost:3000',
    reuseExistingServer: !process.env.CI,
    timeout: 120000,
  },
});
```

---

## 参考资料

- [Playwright 报告器](https://playwright.dev/docs/test-reporters)
- [Playwright Trace Viewer](https://playwright.dev/docs/trace-viewer)
- [Playwright 截图和视频](https://playwright.dev/docs/screenshots)
- [GitHub Actions Artifacts](https://docs.github.com/en/actions/using-workflows/storing-workflow-data-as-artifacts)
