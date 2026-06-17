# Playwright 测试模式指南

本文档提供 Playwright 测试的常用设计模式和最佳实践，帮助构建可维护、可扩展的测试套件。

---

## 1. 页面对象模式（Page Object Model, POM）

### 概述

页面对象模式将页面元素定位和交互逻辑封装在独立的类中，使测试代码更清晰、更易维护。

### 1.1 基础 POM 实现

```javascript
// pages/LoginPage.js
class LoginPage {
  constructor(page) {
    this.page = page;
    // 定位器
    this.usernameInput = page.getByLabel('用户名');
    this.passwordInput = page.getByLabel('密码');
    this.loginButton = page.getByRole('button', { name: '登录' });
    this.errorMessage = page.getByText('登录失败');
  }

  // 操作方法
  async login(username, password) {
    await this.usernameInput.fill(username);
    await this.passwordInput.fill(password);
    await this.loginButton.click();
  }

  async getErrorMessage() {
    return await this.errorMessage.textContent();
  }
}

module.exports = { LoginPage };
```

```javascript
// tests/login.spec.js
const { test, expect } = require('@playwright/test');
const { LoginPage } = require('../pages/LoginPage');

test.describe('登录测试 - POM 模式', () => {
  test('成功登录', async ({ page }) => {
    const loginPage = new LoginPage(page);

    await page.goto('/login');
    await loginPage.login('testuser', 'password123');

    await expect(page).toHaveURL('/dashboard');
  });

  test('登录失败', async ({ page }) => {
    const loginPage = new LoginPage(page);

    await page.goto('/login');
    await loginPage.login('testuser', 'wrongpassword');

    const error = await loginPage.getErrorMessage();
    expect(error).toContain('登录失败');
  });
});
```

---

### 1.2 POM 最佳实践

```javascript
// pages/BasePage.js - 基础页面类
class BasePage {
  constructor(page) {
    this.page = page;
  }

  async navigate(url) {
    await this.page.goto(url);
    await this.page.waitForLoadState('networkidle');
  }

  async waitForElement(selector) {
    await expect(this.page.locator(selector)).toBeVisible();
  }

  async clickElement(selector) {
    await this.page.locator(selector).click();
  }

  async fillText(selector, text) {
    await this.page.locator(selector).fill(text);
  }
}

module.exports = { BasePage };
```

```javascript
// pages/DashboardPage.js - 继承基础页面
const { BasePage } = require('./BasePage');

class DashboardPage extends BasePage {
  constructor(page) {
    super(page);
    this.welcomeMessage = page.getByRole('heading', { name: '欢迎' });
    this.logoutButton = page.getByRole('button', { name: '退出' });
    this.userMenu = page.getByTestId('user-menu');
  }

  async logout() {
    await this.userMenu.click();
    await this.logoutButton.click();
  }

  async isWelcomeVisible() {
    return await this.welcomeMessage.isVisible();
  }
}

module.exports = { DashboardPage };
```

---

### 1.3 完整 POM 示例

```javascript
// pages/LoginPage.js
class LoginPage {
  constructor(page) {
    this.page = page;
    this.usernameInput = page.getByLabel('用户名');
    this.passwordInput = page.getByLabel('密码');
    this.loginButton = page.getByRole('button', { name: '登录' });
  }

  async goto() {
    await this.page.goto('/login');
    await this.page.waitForLoadState('networkidle');
  }

  async login(username, password) {
    await this.usernameInput.fill(username);
    await this.passwordInput.fill(password);
    await this.loginButton.click();
  }
}

// pages/DashboardPage.js
class DashboardPage {
  constructor(page) {
    this.page = page;
    this.productsLink = page.getByRole('link', { name: '产品' });
    this.ordersLink = page.getByRole('link', { name: '订单' });
  }

  async gotoProducts() {
    await this.productsLink.click();
  }

  async gotoOrders() {
    await this.ordersLink.click();
  }
}

// tests/ecommerce.spec.js
const { test, expect } = require('@playwright/test');
const { LoginPage } = require('../pages/LoginPage');
const { DashboardPage } = require('../pages/DashboardPage');

test.describe('电商测试 - 完整 POM', () => {
  let loginPage;
  let dashboardPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    dashboardPage = new DashboardPage(page);
  });

  test('用户登录并查看产品', async ({ page }) => {
    await loginPage.goto();
    await loginPage.login('user1', 'pass123');

    await expect(page).toHaveURL('/dashboard');
    await dashboardPage.gotoProducts();

    await expect(page.getByRole('heading', { name: '产品列表' })).toBeVisible();
  });
});
```

---

## 2. 并行测试

### 2.1 启用并行测试

**playwright.config.js**:
```javascript
module.exports = defineConfig({
  // 完全并行执行所有测试
  fullyParallel: true,

  // 最大并行 worker 数量
  workers: process.env.CI ? 2 : 4,

  // 每个 spec 文件并行执行
  testDir: './tests',
});
```

---

### 2.2 test.describe.parallel() - 并行测试组

```javascript
const { test, expect } = require('@playwright/test');

test.describe.parallel('并行测试组', () => {
  test('测试 1', async ({ page }) => {
    await page.goto('/');
    await expect(page.locator('h1')).toBeVisible();
  });

  test('测试 2', async ({ page }) => {
    await page.goto('/about');
    await expect(page.locator('h1')).toBeVisible();
  });

  test('测试 3', async ({ page }) => {
    await page.goto('/contact');
    await expect(page.locator('h1')).toBeVisible();
  });
});
```

---

### 2.3 并行测试注意事项

```javascript
// ❌ 错误：并行测试间共享状态
test.describe('共享数据', () => {
  let sharedData = []; // 并行测试会互相干扰

  test('测试 1', async ({ page }) => {
    sharedData.push('data1'); // 可能会冲突
  });
});

// ✅ 正确：每个测试独立数据
test.describe('独立数据', () => {
  test('测试 1', async ({ page }) => {
    const data = ['data1']; // 独立数据
  });
});
```

---

## 3. 参数化测试

### 3.1 test.each() - 数据驱动参数化

```javascript
const { test, expect } = require('@playwright/test');

test.describe('参数化登录测试', () => {
  test.each([
    { browser: 'chromium', user: 'user1' },
    { browser: 'firefox', user: 'user2' },
    { browser: 'webkit', user: 'user3' },
  ])('浏览器 $browser 用户 $user', async ({ page }, data) => {
    await page.goto('/login');
    await page.getByLabel('用户名').fill(data.user);
    await page.getByLabel('密码').fill('password123');
    await page.getByRole('button', { name: '登录' }).click();
    await expect(page).toHaveURL('/dashboard');
  });
});
```

---

### 3.2 test.describe.configure() - 模式配置

```javascript
test.describe.configure({ mode: 'parallel' });

test.describe('配置为并行模式', () => {
  test('测试 1', async ({ page }) => {
    // 这些测试会并行执行
  });

  test('测试 2', async ({ page }) => {
    // 这些测试会并行执行
  });
});
```

---

## 4. 测试钩子

### 4.1 beforeAll 和 afterAll

```javascript
const { test, expect } = require('@playwright/test');

test.describe('测试钩子示例', () => {
  let database;

  test.beforeAll(async () => {
    // 在所有测试前执行一次
    console.log('初始化数据库连接');
    database = await connectToDatabase();
  });

  test.afterAll(async () => {
    // 在所有测试后执行一次
    console.log('关闭数据库连接');
    await database.close();
  });

  test('测试 1', async ({ page }) => {
    // 使用 database
  });

  test('测试 2', async ({ page }) => {
    // 使用 database
  });
});
```

---

### 4.2 beforeEach 和 afterEach

```javascript
test.describe('beforeEach/afterEach 示例', () => {
  test.beforeEach(async ({ page }) => {
    // 每个测试前执行
    console.log('导航到登录页');
    await page.goto('/login');
  });

  test.afterEach(async ({ page }) => {
    // 每个测试后执行
    console.log('清理测试数据');
    await page.evaluate(() => localStorage.clear());
  });

  test('测试 1', async ({ page }) => {
    // 已经在登录页
    await page.getByLabel('用户名').fill('user1');
  });

  test('测试 2', async ({ page }) => {
    // 已经在登录页
    await page.getByLabel('用户名').fill('user2');
  });
});
```

---

### 4.3 钩子执行顺序

```javascript
test.describe('钩子执行顺序演示', () => {
  test.beforeAll(async () => {
    console.log('1. beforeAll - 测试组开始前执行一次');
  });

  test.afterAll(async () => {
    console.log('8. afterAll - 测试组结束后执行一次');
  });

  test.beforeEach(async () => {
    console.log('2, 5. beforeEach - 每个测试前执行');
  });

  test.afterEach(async () => {
    console.log('4, 7. afterEach - 每个测试后执行');
  });

  test('测试 1', async ({ page }) => {
    console.log('3. 测试 1 执行');
  });

  test('测试 2', async ({ page }) => {
    console.log('6. 测试 2 执行');
  });
});
```

**输出顺序**:
```
1. beforeAll
2. beforeEach
3. 测试 1 执行
4. afterEach
5. beforeEach
6. 测试 2 执行
7. afterEach
8. afterAll
```

---

## 5. 测试配置模式

### 5.1 test.use() - 测试级别配置

```javascript
const { test, expect } = require('@playwright/test');

// 配置特定测试组
test.use({
  viewport: { width: 1920, height: 1080 },
  locale: 'zh-CN',
  timezoneId: 'Asia/Shanghai',
});

test.describe('大屏幕中文测试', () => {
  test('测试', async ({ page }) => {
    // 使用配置的 viewport 和 locale
    await page.goto('/');
    expect(page.viewportSize().width).toBe(1920);
  });
});
```

---

### 5.2 test.step() - 测试步骤

```javascript
test('登录流程', async ({ page }) => {
  await test.step('导航到登录页', async () => {
    await page.goto('/login');
    await expect(page.getByRole('heading', { name: '登录' })).toBeVisible();
  });

  await test.step('输入凭证', async () => {
    await page.getByLabel('用户名').fill('testuser');
    await page.getByLabel('密码').fill('password123');
  });

  await test.step('提交登录', async () => {
    await page.getByRole('button', { name: '登录' }).click();
  });

  await test.step('验证登录成功', async () => {
    await expect(page).toHaveURL('/dashboard');
    await expect(page.getByRole('heading', { name: '仪表板' })).toBeVisible();
  });
});
```

---

### 5.3 条件跳过测试

```javascript
test.describe('条件跳过', () => {
  // 跳过特定浏览器
  test.skip(({ browserName }) => browserName !== 'chromium', '仅在 Chromium 上运行');

  test('Chromium 专用测试', async ({ page }) => {
    // 只在 Chromium 上运行
  });

  // 根据条件跳过
  test('可能跳过的测试', async ({ page }) => {
    test.skip(process.env.SKIP_FLAKY === 'true', '测试不稳定，暂时跳过');

    // 测试逻辑...
  });

  // 固定跳过
  test.skip(true, '功能未实现，暂时跳过');

  test('未实现的测试', async ({ page }) => {
    // 不会执行
  });
});
```

---

## 6. Fixture 模式

### 6.1 自定义 Fixture

```javascript
// tests/fixtures.js
const { test as base } = require('@playwright/test');

// 扩展 base test
export const test = base.extend({
  // 自定义 fixture
  authenticatedPage: async ({ page }, use) => {
    // 设置：登录
    await page.goto('/login');
    await page.getByLabel('用户名').fill('testuser');
    await page.getByLabel('密码').fill('password123');
    await page.getByRole('button', { name: '登录' }).click();
    await page.waitForURL('/dashboard');

    // 使用 fixture
    await use(page);

    // 清理：登出
    await page.getByRole('button', { name: '退出' }).click();
  },

  // 另一个 fixture
  testData: async ({}, use) => {
    const data = { username: 'testuser', password: 'password123' };
    await use(data);
  },
});

export const expect = test.expect;
```

```javascript
// tests/login.spec.js
const { test, expect } = require('./fixtures');

test('使用自定义 fixture', async ({ authenticatedPage }) => {
  // 已经登录
  await authenticatedPage.goto('/profile');
  await expect(authenticatedPage.getByRole('heading', { name: '个人资料' })).toBeVisible();
});
```

---

### 6.2 Worker Fixture（进程级别）

```javascript
// tests/fixtures.js
const { test as base } = require('@playwright/test');

export const test = base.extend({
  // worker fixture：在 worker 启动时创建，所有测试共享
  database: async ({}, use) => {
    const db = await connectToDatabase();
    await use(db);
    await db.close();
  },
});
```

---

## 7. 重试和超时模式

### 7.1 配置重试

**playwright.config.js**:
```javascript
module.exports = defineConfig({
  // 全局重试配置
  retries: 2,

  // 条件重试
  use: {
    actionTimeout: 10000,
  },
});
```

---

### 7.2 测试级别重试

```javascript
test.describe('测试级别重试', () => {
  // 此测试会重试 3 次
  test.retry(3)('不稳定的测试', async ({ page }) => {
    // 测试逻辑...
  });

  // 此测试不重试
  test.retry(0)('稳定的测试', async ({ page }) => {
    // 测试逻辑...
  });
});
```

---

### 7.3 配置超时

```javascript
test.describe('超时配置', () => {
  // 测试组超时
  test.setTimeout(60000);

  test('长运行测试', async ({ page }) => {
    // 60 秒超时
    await page.goto('/');
    // 长时间操作...
  });

  test('特定超时', async ({ page }) => {
    test.setTimeout(120000); // 120 秒
    // 更长时间操作...
  });

  test('短超时', async ({ page }) => {
    test.setTimeout(5000); // 5 秒
    // 快速操作...
  });

  test('步骤超时', async ({ page }) => {
    await test.step('步骤 1', async () => {
      test.step.setTimeout(10000);
      // 10 秒超时
    });
  });
});
```

---

## 8. 组织大型测试套件

### 8.1 项目结构

```
tests/
├── e2e/
│   ├── login/
│   │   └── login.spec.js
│   ├── checkout/
│   │   └── checkout.spec.js
│   └── dashboard/
│       └── dashboard.spec.js
├── integration/
│   └── api/
│       └── api.spec.js
└── unit/
    └── utils/
        └── utils.spec.js
```

---

### 8.2 多项目配置

**playwright.config.js**:
```javascript
module.exports = defineConfig({
  projects: [
    {
      name: 'chromium',
      use: { browserName: 'chromium' },
    },

    {
      name: 'firefox',
      use: { browserName: 'firefox' },
    },

    {
      name: 'webkit',
      use: { browserName: 'webkit' },
    },

    {
      name: 'e2e-tests',
      testMatch: /e2e\/.*\.spec\.js/,
    },

    {
      name: 'api-tests',
      testMatch: /integration\/api\/.*\.spec\.js/,
    },
  ],
});
```

---

## 9. 调试模式

### 9.1 调试特定测试

```javascript
test.describe('调试演示', () => {
  // 只运行此测试
  test.only('调试此测试', async ({ page }) => {
    await page.goto('/');
    // 调试逻辑...
  });

  // 跳过其他测试
  test('被跳过的测试', async ({ page }) => {
    // 不会执行
  });
});
```

---

### 9.2 使用 test.info()

```javascript
test('使用 test.info()', async ({ page }) => {
  const info = test.info();

  console.log('测试标题:', info.title);
  console.log('测试文件:', info.file);
  console.log('重试次数:', info.retry);
  console.log('并行索引:', info.parallelIndex);

  // 根据重试次数调整行为
  if (info.retry > 0) {
    console.log('这是重试运行');
  }
});
```

---

## 10. 完整示例：电商测试套件

```javascript
// pages/LoginPage.js
class LoginPage {
  constructor(page) {
    this.page = page;
    this.usernameInput = page.getByLabel('用户名');
    this.passwordInput = page.getByLabel('密码');
    this.loginButton = page.getByRole('button', { name: '登录' });
  }

  async goto() {
    await this.page.goto('/login');
  }

  async login(username, password) {
    await this.usernameInput.fill(username);
    await this.passwordInput.fill(password);
    await this.loginButton.click();
  }
}

// pages/DashboardPage.js
class DashboardPage {
  constructor(page) {
    this.page = page;
    this.productLink = page.getByRole('link', { name: '产品' });
    this.cartLink = page.getByRole('link', { name: '购物车' });
  }

  async gotoProducts() {
    await this.productLink.click();
  }

  async gotoCart() {
    await this.cartLink.click();
  }
}

// tests/ecommerce.spec.js
const { test, expect } = require('@playwright/test');
const { LoginPage } = require('../pages/LoginPage');
const { DashboardPage } = require('../pages/DashboardPage');

test.describe('电商测试套件', () => {
  let loginPage;
  let dashboardPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    dashboardPage = new DashboardPage(page);
  });

  test.describe.configure({ mode: 'serial' });

  test('用户登录', async ({ page }) => {
    await loginPage.goto();
    await loginPage.login('user1', 'pass123');

    await expect(page).toHaveURL('/dashboard');
  });

  test('浏览产品', async ({ page }) => {
    await loginPage.goto();
    await loginPage.login('user1', 'pass123');
    await dashboardPage.gotoProducts();

    await expect(page.getByRole('heading', { name: '产品列表' })).toBeVisible();
  });

  test('添加到购物车', async ({ page }) => {
    await loginPage.goto();
    await loginPage.login('user1', 'pass123');
    await dashboardPage.gotoProducts();

    await page.getByRole('button', { name: '添加到购物车' }).first().click();
    await dashboardPage.gotoCart();

    await expect(page.locator('.cart-item')).toHaveCount(1);
  });
});
```

---

## 总结

### 关键要点

1. ✅ **使用 POM** - 分离页面逻辑和测试逻辑
2. ✅ **合理使用钩子** - beforeAll、beforeEach、afterAll、afterEach
3. ✅ **启用并行测试** - fullyParallel: true
4. ✅ **参数化测试** - test.each() 数据驱动
5. ✅ **自定义 Fixture** - 复用测试设置代码
6. ✅ **配置重试和超时** - 提高测试稳定性
7. ✅ **组织测试结构** - 按功能模块分组

### 模式选择指南

| 模式 | 适用场景 | 复杂度 |
|------|----------|--------|
| **POM** | 大型应用、多页面测试 | 中等 |
| **并行测试** | 回归测试、多浏览器 | 简单 |
| **参数化测试** | 数据驱动测试 | 简单 |
| **Fixture** | 复杂测试设置 | 中等 |
| **测试钩子** | 初始化和清理 | 简单 |
