# CI/CD 集成指南

本文档提供 Playwright 测试与主流 CI/CD 平台的集成指南，重点支持 Jenkins。

---

## 1. Jenkins 集成（重点）

### 1.1 Jenkins Pipeline 配置

**Jenkinsfile**:
```groovy
pipeline {
    agent any

    environment {
        NODE_VERSION = '18'
        PLAYWRIGHT_BROWSERS_PATH = '0'
    }

    stages {
        stage('Checkout') {
            steps {
                echo '检出代码...'
                checkout scm
            }
        }

        stage('安装 Node.js') {
            steps {
                echo '安装 Node.js...'
                nodejs(nodeJSInstallationName: "Node ${NODE_VERSION}") {
                    sh 'node --version'
                    sh 'npm --version'
                }
            }
        }

        stage('安装依赖') {
            steps {
                echo '安装项目依赖...'
                sh 'npm ci'
            }
        }

        stage('安装 Playwright 浏览器') {
            steps {
                echo '安装 Playwright 浏览器...'
                sh 'npx playwright install --with-deps chromium'
                sh 'npx playwright install --with-deps firefox'
                sh 'npx playwright install --with-deps webkit'
            }
        }

        stage('运行测试') {
            steps {
                echo '运行 Playwright 测试...'
                sh 'npm run test:ci'
            }
        }

        stage('上传报告') {
            steps {
                echo '上传测试报告...'
                publishHTML([
                    allowMissing: false,
                    alwaysLinkToLastBuild: true,
                    keepAll: true,
                    reportDir: 'playwright-report',
                    reportFiles: 'index.html',
                    reportName: 'Playwright 测试报告'
                ])

                // JUnit 报告
                junit 'junit-results.xml'

                // 归档测试结果
                archiveArtifacts artifacts: 'test-results.json', allowEmptyArchive: true
            }
        }
    }

    post {
        always {
            echo '清理工作空间...'
            cleanWs()
        }

        success {
            echo '测试通过！'
        }

        failure {
            echo '测试失败！'
        }
    }
}
```

---

### 1.2 声明式 Pipeline（详细版）

**Jenkinsfile**:
```groovy
pipeline {
    agent any

    options {
        // 构建超时
        timeout(time: 30, unit: 'MINUTES')

        // 保留最近的构建
        buildDiscarder(logRotator(numToKeepStr: '10'))

        // 禁止并发构建
        disableConcurrentBuilds()

        // 添加时间戳
        timestamps()
    }

    environment {
        // Node.js 版本
        NODE_VERSION = '18'

        // 测试环境
        TEST_ENV = 'staging'

        // 基础 URL
        BASE_URL = 'https://staging.example.com'

        // 浏览器缓存目录
        PLAYWRIGHT_BROWSERS_PATH = "${WORKSPACE}/.cache/ms-playwright"
    }

    stages {
        stage('准备环境') {
            steps {
                script {
                    echo "========================================="
                    echo "构建信息:"
                    echo "  构建号: ${env.BUILD_NUMBER}"
                    echo "  构建标签: ${env.BUILD_TAG}"
                    echo "  工作空间: ${env.WORKSPACE}"
                    echo "  测试环境: ${env.TEST_ENV}"
                    echo "========================================="
                }
            }
        }

        stage('检出代码') {
            steps {
                echo '检出代码...'
                checkout([
                    $class: 'GitSCM',
                    branches: [[name: '*/main']],
                    userRemoteConfigs: [[url: 'https://github.com/your-org/your-repo.git']]
                ])
            }
        }

        stage('安装 Node.js') {
            steps {
                echo '安装 Node.js...'
                nodejs(nodeJSInstallationName: "Node ${NODE_VERSION}") {
                    sh '''
                        node --version
                        npm --version
                    '''
                }
            }
        }

        stage('安装依赖') {
            steps {
                echo '安装项目依赖...'
                sh '''
                    npm ci
                    npm list @playwright/test
                '''
            }
        }

        stage('安装浏览器') {
            steps {
                echo '安装 Playwright 浏览器...'
                sh '''
                    npx playwright install --with-deps chromium
                    npx playwright install --with-deps firefox
                '''
            }
        }

        stage('运行测试') {
            steps {
                echo '运行 Playwright 测试...'
                sh '''
                    export BASE_URL=${BASE_URL}
                    export TEST_ENV=${TEST_ENV}
                    npm run test:ci
                '''
            }
        }

        stage('生成报告') {
            steps {
                echo '生成测试报告...'
                sh '''
                    npx playwright show-report || true
                '''
            }
        }
    }

    post {
        always {
            script {
                echo '发布测试报告...'

                // HTML 报告
                publishHTML([
                    reportDir: 'playwright-report',
                    reportFiles: 'index.html',
                    reportName: 'Playwright HTML 报告',
                    keepAll: true,
                    alwaysLinkToLastBuild: true,
                    allowMissing: false
                ])

                // JUnit 报告
                junit(
                    testResults: 'junit-results.xml',
                    allowEmptyResults: false
                )

                // 归档产物
                archiveArtifacts(
                    artifacts: 'test-results.json,junit-results.xml',
                    allowEmptyArchive: false,
                    fingerprint: true
                )
            }
        }

        success {
            echo '✅ 测试执行成功！'
            // 发送成功通知
            // emailext(subject: "测试成功: ${env.JOB_NAME} #${env.BUILD_NUMBER}", body: "...")
        }

        failure {
            echo '❌ 测试执行失败！'
            // 发送失败通知
            // emailext(subject: "测试失败: ${env.JOB_NAME} #${env.BUILD_NUMBER}", body: "...")
        }

        unstable {
            echo '⚠️ 测试执行不稳定！'
        }

        cleanup {
            echo '清理工作空间...'
            // 保留 HTML 报告，删除其他临时文件
            cleanWs(
                deleteDirs: true,
                patterns: [
                    [pattern: 'node_modules', type: 'INCLUDE'],
                    [pattern: '.cache', type: 'INCLUDE'],
                    [pattern: 'test-results', type: 'INCLUDE']
                ],
                notFailIfCleanup: false
            )
        }
    }
}
```

---

### 1.3 package.json 脚本

```json
{
  "scripts": {
    "test": "playwright test",
    "test:ci": "playwright test --reporter=junit,list --reporter=junit --output=junit-results.xml",
    "test:headed": "playwright test --headed",
    "test:debug": "playwright test --debug",
    "test:chromium": "playwright test --project=chromium",
    "test:firefox": "playwright test --project=firefox",
    "show-report": "playwright show-report"
  },
  "devDependencies": {
    "@playwright/test": "^1.40.0"
  }
}
```

---

### 1.4 Jenkins 插件要求

安装以下 Jenkins 插件：

1. **Node.js Plugin** - 支持 Node.js
2. **Pipeline Plugin** - 支持 Pipeline
3. **HTML Publisher Plugin** - 发布 HTML 报告
4. **JUnit Plugin** - 发布 JUnit 报告
5. **Git Plugin** - 支持 Git

---

### 1.5 Jenkins 多浏览器测试

**Jenkinsfile**:
```groovy
pipeline {
    agent any

    stages {
        stage('并行测试') {
            parallel {
                stage('Chromium 测试') {
                    steps {
                        sh 'npm run test:chromium'
                    }
                }

                stage('Firefox 测试') {
                    steps {
                        sh 'npm run test:firefox'
                    }
                }

                stage('WebKit 测试') {
                    steps {
                        sh 'npm run test:webkit'
                    }
                }
            }
        }
    }
}
```

---

### 1.6 Jenkins 定时构建

**Jenkinsfile**:
```groovy
pipeline {
    agent any

    triggers {
        // 每天凌晨 2 点运行
        cron('H 2 * * *')

        // 每 15 分钟检查一次代码变更
        // pollSCM('H/15 * * * *')
    }

    stages {
        stage('测试') {
            steps {
                sh 'npm run test:ci'
            }
        }
    }
}
```

---

## 2. GitHub Actions 集成

### 2.1 基础配置

**.github/workflows/playwright-tests.yml**:
```yaml
name: Playwright 测试

on:
  push:
    branches: [ main, develop ]
  pull_request:
    branches: [ main ]
  schedule:
    # 每天 UTC 2:00 运行
    - cron: '0 2 * * *'

jobs:
  test:
    runs-on: ubuntu-latest

    strategy:
      matrix:
        browser: [chromium, firefox, webkit]
      fail-fast: false

    steps:
      - name: 检出代码
        uses: actions/checkout@v3

      - name: 设置 Node.js
        uses: actions/setup-node@v3
        with:
          node-version: 18

      - name: 安装依赖
        run: npm ci

      - name: 安装 Playwright 浏览器
        run: npx playwright install --with-deps ${{ matrix.browser }}

      - name: 运行测试
        env:
          CI: true
        run: npx playwright test --project=${{ matrix.browser }}

      - name: 上传测试报告
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: playwright-report-${{ matrix.browser }}
          path: playwright-report/
          retention-days: 30

      - name: 上传测试结果
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: test-results-${{ matrix.browser }}
          path: test-results/
```

---

### 2.2 完整配置（带报告）

```yaml
name: Playwright 测试

on:
  push:
    branches: [ main ]
  pull_request:
    branches: [ main ]

jobs:
  test:
    timeout-minutes: 60
    runs-on: ubuntu-latest
    container:
      image: mcr.microsoft.com/playwright:v1.40.0-jammy

    steps:
      - name: 检出代码
        uses: actions/checkout@v3

      - name: 安装依赖
        run: npm ci

      - name: 安装 Playwright 浏览器
        run: npx playwright install --with-deps

      - name: 运行测试
        run: npx playwright test

      - name: 上传 HTML 报告
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: html-report
          path: playwright-report/index.html

      - name: 上传测试结果
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: test-results
          path: test-results.json

      - name: 上传 JUnit 报告
        if: always()
        uses: actions/upload-artifact@v3
        with:
          name: junit-results
          path: junit-results.xml

      - name: 发布测试报告
        if: github.event_name == 'push' && github.ref == 'refs/heads/main'
        uses: peaceiris/actions-gh-pages@v3
        with:
          github_token: ${{ secrets.GITHUB_TOKEN }}
          publish_dir: ./playwright-report
```

---

### 2.3 多配置矩阵

```yaml
jobs:
  test:
    runs-on: ubuntu-latest

    strategy:
      matrix:
        os: [ubuntu-latest, windows-latest, macos-latest]
        node: [16, 18, 20]
        browser: [chromium, firefox, webkit]
      fail-fast: false

    steps:
      - uses: actions/checkout@v3

      - name: 设置 Node.js ${{ matrix.node }}
        uses: actions/setup-node@v3
        with:
          node-version: ${{ matrix.node }}

      - run: npm ci

      - run: npx playwright install --with-deps

      - run: npx playwright test --project=${{ matrix.browser }}
```

---

## 3. GitLab CI 集成

### 3.1 基础配置

**.gitlab-ci.yml**:
```yaml
stages:
  - test

variables:
  NODE_VERSION: "18"
  PLAYWRIGHT_BROWSERS_PATH: "$CI_PROJECT_DIR/.cache/ms-playwright"

cache:
  key: ${CI_COMMIT_REF_SLUG}
  paths:
    - node_modules/
    - .cache/ms-playwright/

playwright:test:
  stage: test
  image: node:18

  before_script:
    - npm ci
    - npx playwright install --with-deps chromium

  script:
    - npm run test:ci

  artifacts:
    when: always
    paths:
      - playwright-report/
      - junit-results.xml
      - test-results.json
    expire_in: 1 week

  only:
    - main
    - merge_requests
```

---

### 3.2 完整配置

```yaml
stages:
  - test
  - report

variables:
  NODE_VERSION: "18"
  BASE_URL: "https://staging.example.com"

.playwright_base:
  image: node:18
  cache:
    key: ${CI_COMMIT_REF_SLUG}
    paths:
      - node_modules/
      - .cache/ms-playwright/
  before_script:
    - npm ci
    - npx playwright install --with-deps

chromium_tests:
  extends: .playwright_base
  stage: test
  script:
    - npm run test:chromium -- --reporter=junit --output=junit-chromium.xml
  artifacts:
    when: always
    paths:
      - playwright-report/
      - junit-chromium.xml
    reports:
      junit: junit-chromium.xml

firefox_tests:
  extends: .playwright_base
  stage: test
  script:
    - npm run test:firefox -- --reporter=junit --output=junit-firefox.xml
  artifacts:
    when: always
    paths:
      - playwright-report/
      - junit-firefox.xml
    reports:
      junit: junit-firefox.xml

publish_report:
  stage: report
  image: alpine:latest
  script:
    - echo "发布测试报告"
  artifacts:
    when: always
    paths:
      - playwright-report/
  only:
    - main
```

---

## 4. playwright.config.js CI/CD 配置

### 4.1 CI 优化配置

```javascript
const { defineConfig, devices } = require('@playwright/test');

module.exports = defineConfig({
  // CI 中使用较长的超时
  timeout: process.env.CI ? 60 * 1000 : 30 * 1000,

  // CI 中禁用视频以提高速度
  use: {
    video: process.env.CI ? 'retain-on-failure' : 'on',
    screenshot: process.env.CI ? 'only-on-failure' : 'on',
    trace: process.env.CI ? 'retain-on-failure' : 'on',
  },

  // 多项目配置
  projects: [
    {
      name: 'chromium',
      use: devices['Desktop Chrome'],
    },

    {
      name: 'firefox',
      use: devices['Desktop Firefox'],
    },

    {
      name: 'webkit',
      use: devices['Desktop Safari'],
    },
  ],

  // CI 中报告器配置
  reporter: [
    ['html', { open: 'never' }],
    ['junit', { outputFile: 'junit-results.xml' }],
    ['json', { outputFile: 'test-results.json' }],
    ['list'],
  ],

  // CI 中 worker 数量
  workers: process.env.CI ? 2 : 4,
});
```

---

### 4.2 环境变量支持

```javascript
module.exports = defineConfig({
  use: {
    // 从环境变量读取基础 URL
    baseURL: process.env.BASE_URL || 'http://localhost:3000',

    // 从环境变量读取超时设置
    actionTimeout: process.env.ACTION_TIMEOUT
      ? parseInt(process.env.ACTION_TIMEOUT)
      : 10000,

    // 浏览器缓存
    launchOptions: {
      args: process.env.CI
        ? ['--no-sandbox', '--disable-setuid-sandbox']
        : [],
    },
  },
});
```

---

## 5. Docker 容器集成

### 5.1 Dockerfile

```dockerfile
FROM mcr.microsoft.com/playwright:v1.40.0-jammy

WORKDIR /app

# 复制 package 文件
COPY package*.json ./

# 安装依赖
RUN npm ci

# 复制测试代码
COPY . .

# 安装 Playwright 浏览器
RUN npx playwright install --with-deps

# 运行测试
CMD ["npm", "run", "test:ci"]
```

---

### 5.2 Docker Compose

```yaml
version: '3.8'

services:
  playwright-tests:
    build: .
    environment:
      - BASE_URL=http://app:3000
      - TEST_ENV=staging
    volumes:
      - ./playwright-report:/app/playwright-report
      - ./test-results:/app/test-results

  app:
    image: your-app:latest
    ports:
      - "3000:3000"
```

---

## 6. 测试报告可视化

### 6.1 Allure 报告（可选）

**安装**:
```bash
npm install -D allure-playwright
```

**配置**:
```javascript
module.exports = defineConfig({
  reporter: [
    ['allure-playwright'],
    ['html'],
  ],
});
```

**生成报告**:
```bash
npx allure generate ./allure-results --clean
```

---

### 6.2 自定义 HTML 报告

```javascript
// custom-reporter.js
class CustomReporter {
  onBegin(config, suite) {
    console.log(`开始测试: ${suite.allTests().length} 个测试`);
  }

  onTestEnd(test, result) {
    console.log(`${test.title}: ${result.status}`);
  }

  onEnd(result) {
    console.log(`测试完成: ${result.status}`);
  }
}

module.exports = CustomReporter;
```

---

## 7. 故障排查

### 7.1 常见问题

| 问题 | 解决方案 |
|------|----------|
| 浏览器未安装 | 添加 `npx playwright install --with-deps` |
| 超时错误 | 增加 `timeout` 配置 |
| 显示器问题 | CI 中使用 `headless: true` |
| 报告未生成 | 检查路径配置和权限 |

---

### 7.2 调试 CI 失败

```bash
# 本地运行 CI 环境
HEADLESS=true npm run test:ci

# 查看详细日志
DEBUG=pw:api npm run test:ci

# 保留浏览器输出
CI=true npm run test:headed
```

---

## 总结

### CI/CD 集成要点

1. ✅ **Jenkins 优先** - 完整的 Pipeline 配置
2. ✅ **多浏览器并行** - 提高测试效率
3. ✅ **报告发布** - HTML + JUnit
4. ✅ **定时构建** - 定时回归测试
5. ✅ **环境隔离** - Docker 容器
6. ✅ **失败通知** - 邮件/即时通讯

### 快速开始

1. 复制对应的 CI/CD 配置文件
2. 配置环境变量（BASE_URL、TEST_ENV）
3. 运行测试并验证报告生成
4. 配置报告发布和通知
