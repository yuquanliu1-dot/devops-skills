# Playwright 最佳实践

本文档提供 Playwright 自动化测试的最佳实践，帮助构建稳定、可维护、高效的测试套件。

---

## 1. 选择器稳定性原则

### 1.1 选择器优先级（严格遵循）

```javascript
// ✅ 1. getByRole - 最稳定（推荐）
await page.getByRole('button', { name: '提交' }).click();
await page.getByRole('textbox', { name: '用户名' }).fill('test');

// ✅ 2. getByLabel - 表单元素
await page.getByLabel('邮箱').fill('test@example.com');

// ✅ 3. getByPlaceholder - 输入框占位符
await page.getByPlaceholder('请输入手机号').fill('13800138000');

// ✅ 4. getByText + .first() - 文本内容
await page.getByText('确定').first().click();

// ✅ 5. getByTestId - 测试专用属性
await page.getByTestId('submit-button').click();

// ⚠️ 6. locator + 属性选择器
await page.locator('input[name="username"]').fill('test');

// ❌ 7. CSS 类 - 不推荐（容易变化）
await page.locator('.btn-primary').click();

// ❌ 8. ref 属性 - 禁止使用（MCP 快照特有）
await page.locator('[ref="e10"]').click(); // 绝对禁止
```

---

### 1.2 选择器稳定性对比

| 选择器类型 | 稳定性 | 原因 |
|-----------|--------|------|
| `getByRole` | ⭐⭐⭐⭐⭐ | 基于语义，最稳定 |
| `getByLabel` | ⭐⭐⭐⭐⭐ | 表单关联，不易变化 |
| `getByTestId` | ⭐⭐⭐⭐ | 专用属性，可控 |
| `getByPlaceholder` | ⭐⭐⭐⭐ | 用户可见文本 |
| `getByText` | ⭐⭐⭐ | 文本可能变化 |
| `locator + id` | ⭐⭐⭐ | ID 可能变化 |
| `locator + class` | ⭐⭐ | CSS 类经常变化 |
| `ref 属性` | ❌ | MCP 快照特有，实际不存在 |

---

### 1.3 处理多元素匹配

```javascript
// ❌ 错误：可能匹配多个元素
await page.getByText('提交').click();

// ✅ 正确 1：使用 .first()
await page.getByText('提交').first().click();

// ✅ 正确 2：使用 .nth()
await page.getByText('提交').nth(1).click();

// ✅ 正确 3：使用 filter 精确定位
await page.getByRole('listitem').filter({ hasText: '重要' }).click();

// ✅ 正确 4：使用更具体的选择器
await page.getByRole('button', { name: '提交' }).click();
```

---

### 1.4 避免使用脆弱的选择器

```javascript
// ❌ 脆弱：依赖 CSS 类名
await page.locator('.container .btn.btn-primary').click();

// ❌ 脆弱：依赖 XPath
await page.locator('//div[@class="btn"]/button').click();

// ❌ 脆弱：依赖 DOM 结构
await page.locator('div > div > button').click();

// ✅ 稳定：使用语义化选择器
await page.getByRole('button', { name: '提交' }).click();
```

---

### 1.5 组件库特定选择器

当使用 Element UI、Ant Design 等组件库时，语义化选择器可能被组件内部元素拦截，需要使用组件库特定的 class。

#### Element UI 组件

```javascript
// ✅ 下拉框 (el-select) - 使用组件库 class
const dropdown = page.locator('.el-select').nth(0);
await dropdown.click();
await page.getByText('选项文本').first().click();

// ⚠️ ARIA 可能被拦截，不推荐
// await page.getByRole('combobox', { name: '研发类型' }).click();

// ✅ 输入框 (el-input)
await page.locator('.el-input__inner').fill('value');

// ✅ 按钮 (el-button)
await page.getByRole('button', { name: '提交' }).first().click();
```

#### Ant Design 组件

```javascript
// ✅ 下拉框 (ant-select)
const dropdown = page.locator('.ant-select').nth(0);
await dropdown.click();
await page.locator('.ant-select-item-option').filter({ hasText: '选项1' }).click();

// ✅ 日期选择器 (ant-picker)
await page.locator('.ant-picker').click();
await page.locator('.ant-picker-cell').filter({ hasText: '15' }).click();
```

#### Vuetify 组件

```javascript
// ✅ 下拉框 (v-select)
const dropdown = page.locator('.v-select').nth(0);
await dropdown.click();
await page.locator('.v-list-item').filter({ hasText: '选项' }).click();
```

**组件库选择器对照**：

| 组件库 | 下拉框 | 选项 | 输入框 | 按钮 |
|--------|--------|------|--------|------|
| **Element UI** | `.el-select` | `getByText().first()` | `.el-input__inner` | `getByRole('button')` |
| **Ant Design** | `.ant-select` | `.ant-select-item-option` | `.ant-input` | `getByRole('button')` |
| **Vuetify** | `.v-select` | `.v-list-item` | `.v-input` | `getByRole('button')` |

---

### 1.6 原生 HTML 应用选择器

当测试使用原生 HTML（不使用 React/Vue 等框架）的应用时，优先级与通用最佳实践不同。

#### 选择器优先级（原生 HTML）

```javascript
// ✅ 1. id 属性 - 最稳定（原生 HTML 优先）
await page.locator('#departmentSelect').selectOption('财务部');
await page.locator('#username').fill('testuser');
await page.locator('#submit-button').click();

// ✅ 2. name 属性 - 表单元素
await page.locator('input[name="username"]').fill('testuser');
await page.locator('select[name="department"]').selectOption('研发部');

// ✅ 3. getByRole - 语义化元素
await page.getByRole('button', { name: '提交' }).click();
await page.getByRole('textbox', { name: '用户名' }).fill('test');

// ✅ 4. getByLabel - 表单关联
await page.getByLabel('用户名').fill('test');

// ✅ 5. getByPlaceholder - 输入框
await page.getByPlaceholder('请输入用户名').fill('test');

// ⚠️ 6. getByText + .first() - 文本内容（可能重复）
await page.getByText('提交').first().click();

// ❌ CSS 类 - 不推荐（容易变化）
await page.locator('.btn-primary').click();
```

#### 原生 HTML 下拉框操作

```javascript
// ✅ 使用 selectOption 方法（原生 HTML 专用）
await page.locator('#departmentSelect').selectOption('财务部');

// ❌ 不要使用点击方式（这是组件库的操作方式）
// await page.locator('.el-select').nth(0).click();
```

#### 原生 HTML 与组件库应用对比

| 特征 | 原生 HTML 应用 | 组件库应用 |
|------|---------------|-----------|
| **下拉框操作** | `selectOption()` | 点击 + 选择选项 |
| **首选选择器** | `#id`, `[name]` | `getByRole()`, 组件库 class |
| **典型组件** | `<select>`, `<input>` | `el-select`, `ant-select` |
| **选择器稳定性** | ⭐⭐⭐⭐⭐ | ⭐⭐⭐⭐ |

#### 如何识别原生 HTML 应用

```javascript
// 检查是否使用组件库
const hasElementUI = await page.locator('.el-select').count() > 0;
const hasAntDesign = await page.locator('.ant-select').count() > 0;

// 如果都没有检测到，很可能是原生 HTML 应用
if (!hasElementUI && !hasAntDesign) {
  console.log('检测到原生 HTML 应用，使用 id 优先策略');
}
```

---

### 1.7 多层次选择器降级策略

当首选选择器失效时，按以下优先级尝试：

```javascript
const selectorStrategies = [
  // 优先级1: data-testid（最稳定）
  'page.getByTestId("submit-button")',

  // 优先级2: 组件库特定 class（次稳定）
  'page.locator(".el-select").nth(0)',

  // 优先级3: ARIA 属性（语义化，但可能被覆盖）
  'page.getByRole("combobox", { name: "研发类型" })',

  // 优先级4: 文本内容（可能重复，需要 .first()）
  'page.getByText("提交").first()',

  // 优先级5: CSS 选择器（脆弱，最后手段）
  'page.locator("div > div > button")'
];
```

**自动尝试多个策略**：

```javascript
async function findBestSelector(page, semantic) {
  // 尝试 data-testid
  const testId = semantic.name.toLowerCase().replace(/\s+/g, '-');
  const byTestId = page.getByTestId(testId);
  if (await byTestId.count() > 0) return byTestId;

  // 尝试组件库 class
  const componentClasses = ['.el-select', '.ant-select', '.v-select'];
  for (const cls of componentClasses) {
    const byClass = page.locator(cls);
    if (await byClass.count() > 0) return byClass.first();
  }

  // 最后使用语义化选择器
  return page.getByRole(semantic.role, { name: semantic.name });
}
```

---

## 2. 测试独立性原则

### 2.1 测试间不能有依赖

```javascript
// ❌ 错误：测试间有依赖
test.describe('有依赖的测试', () => {
  let userId;

  test('创建用户', async ({ page }) => {
    await page.goto('/users/create');
    await page.getByLabel('用户名').fill('testuser');
    await page.getByRole('button', { name: '创建' }).click();
    userId = await page.locator('.user-id').textContent(); // 共享状态
  });

  test('删除用户', async ({ page }) => {
    await page.goto(`/users/${userId}/delete`); // 依赖上一个测试
    await page.getByRole('button', { name: '删除' }).click();
  });
});

// ✅ 正确：每个测试独立
test.describe('独立的测试', () => {
  test('创建用户', async ({ page }) => {
    await page.goto('/users/create');
    await page.getByLabel('用户名').fill('testuser');
    await page.getByRole('button', { name: '创建' }).click();
    await expect(page.getByText('创建成功')).toBeVisible();
  });

  test('删除用户', async ({ page }) => {
    // 独立创建测试数据
    const userId = await createTestUser();
    await page.goto(`/users/${userId}/delete`);
    await page.getByRole('button', { name: '删除' }).click();
    await expect(page.getByText('删除成功')).toBeVisible();
  });
});
```

---

### 2.2 使用 beforeEach 清理状态

```javascript
test.describe('状态清理', () => {
  test.beforeEach(async ({ page }) => {
    // 清理 localStorage
    await page.goto('/');
    await page.evaluate(() => localStorage.clear());

    // 清理 cookies
    const context = page.context();
    await context.clearCookies();
  });

  test('测试 1', async ({ page }) => {
    // 干净的状态
  });

  test('测试 2', async ({ page }) => {
    // 干净的状态
  });
});
```

---

### 2.3 使用 afterEach 清理测试数据

```javascript
test.describe('测试数据清理', () => {
  let testUserId;

  test.beforeEach(async () => {
    // 创建测试数据
    testUserId = await createTestUser();
  });

  test.afterEach(async () => {
    // 清理测试数据
    await deleteTestUser(testUserId);
  });

  test('测试 1', async ({ page }) => {
    // 使用测试数据
  });
});
```

---

## 3. 等待策略

### 3.1 避免固定延迟

```javascript
// ❌ 错误：使用固定延迟
await page.click('#load-button');
await page.waitForTimeout(5000); // 不可靠
await expect(page.locator('.result')).toBeVisible();

// ✅ 正确：等待网络空闲
await page.click('#load-button');
await page.waitForLoadState('networkidle');
await expect(page.locator('.result')).toBeVisible();

// ✅ 正确：等待元素可见
await page.click('#load-button');
await expect(page.locator('.result')).toBeVisible();

// ✅ 正确：等待 API 响应
await page.click('#load-button');
await page.waitForResponse('**/api/data');
await expect(page.locator('.result')).toBeVisible();
```

---

### 3.2 等待策略选择

| 场景 | 推荐方法 | 示例 |
|------|----------|------|
| 页面初始加载 | `waitForLoadState('networkidle')` | `await page.waitForLoadState('networkidle')` |
| 等待元素可见 | `expect(locator).toBeVisible()` | `await expect(locator).toBeVisible()` |
| 等待 AJAX | `waitForResponse()` | `await page.waitForResponse('**/api/data')` |
| 等待导航 | `waitForURL()` | `await page.waitForURL('/dashboard')` |
| 等待条件 | `expect(async () => {...})` | `await expect(async () => check()).toBeTruthy()` |

---

### 3.3 等待 API 响应

```javascript
// ✅ 等待特定 API
await page.getByRole('button', { name: '加载' }).click();
await page.waitForResponse('**/api/data');
await expect(page.getByText('数据加载完成')).toBeVisible();

// ✅ 验证响应内容
await page.getByRole('button', { name: '保存' }).click();
await page.waitForResponse(async response => {
  const data = await response.json();
  expect(data.success).toBe(true);
  return response.url().includes('/api/save');
});

// ✅ 等待多个响应
const [response1, response2] = await Promise.all([
  page.waitForResponse('**/api/user'),
  page.waitForResponse('**/api/settings'),
  page.getByRole('button', { name: '加载全部' }).click(),
]);
```

---

### 3.4 轮询等待条件

```javascript
// ✅ 轮询等待特定条件
await expect(async () => {
  const text = await page.locator('.status').textContent();
  return text === '完成';
}, { timeout: 10000 }).toBeTruthy();

// ✅ 轮询等待数量变化
const initialCount = await page.locator('.item').count();
await page.getByRole('button', { name: '添加' }).click();

await expect(async () => {
  const newCount = await page.locator('.item').count();
  return newCount > initialCount;
}).toBeTruthy({ timeout: 5000 });
```

---

### 3.5 等待策略对比

| 策略 | 适用场景 | 优点 | 缺点 |
|------|---------|------|------|
| **toBeAttached()** | CI环境、动态内容 | 可靠、不依赖CSS | 不验证可见性 |
| **toBeVisible()** | 本地测试、最终验证 | 确保用户可见 | CI环境可能失败 |
| **waitForTimeout()** | Vue/React渲染后 | 简单 | 不精确、浪费时间 |
| **waitForLoadState('networkidle')** | SPA应用 | 确保资源加载完成 | 可能永远等不到 |
| **waitForSelector()** | 动态加载元素 | 精确、可控 | 需要知道选择器 |

**推荐组合**：

```javascript
// ✅ 最佳实践：组合等待策略
async function robustClick(page, selector) {
  // 1. 等待元素存在
  await expect(selector).toBeAttached({ timeout: 10000 });

  // 2. 点击
  await selector.click();

  // 3. 等待Vue/React渲染
  await page.waitForTimeout(300);

  // 4. 验证结果
  await expect(page.getByText('成功')).toBeAttached();
}
```

---

## 4. 性能优化

### 4.1 并行测试执行

**playwright.config.js**:
```javascript
module.exports = defineConfig({
  // 完全并行
  fullyParallel: true,

  // worker 数量
  workers: process.env.CI ? 2 : 4,
});
```

---

### 4.2 减少不必要的截图和视频

```javascript
module.exports = defineConfig({
  use: {
    // 仅在失败时截图
    screenshot: 'only-on-failure',

    // 仅在失败时录制视频
    video: 'retain-on-failure',

    // 仅在失败时保留 trace
    trace: 'retain-on-failure',
  },
});
```

---

### 4.3 复用浏览器上下文

```javascript
// ❌ 低效：每个测试创建新上下文
test('测试 1', async ({ browser }) => {
  const context = await browser.newContext();
  const page = await context.newPage();
  // 测试逻辑...
  await context.close();
});

// ✅ 高效：复用上下文
test.describe('共享上下文', () => {
  let context;

  test.beforeAll(async ({ browser }) => {
    context = await browser.newContext();
  });

  test.afterAll(async () => {
    await context.close();
  });

  test('测试 1', async () => {
    const page = await context.newPage();
    // 测试逻辑...
  });
});
```

---

### 4.4 避免不必要的等待

```javascript
// ❌ 低效：链式等待
await page.goto('/');
await page.waitForLoadState('load');
await page.waitForLoadState('domcontentloaded');
await page.waitForLoadState('networkidle');

// ✅ 高效：只等待必要的
await page.goto('/');
await page.waitForLoadState('networkidle');
```

---

## 5. 错误处理和调试

### 5.1 清晰的错误消息

```javascript
// ❌ 模糊的错误消息
test('登录测试', async ({ page }) => {
  await page.goto('/login');
  await login(page, 'user', 'pass');
  expect(await page.textContent('.error')).toBeTruthy();
});

// ✅ 清晰的错误消息
test('登录测试', async ({ page }) => {
  await page.goto('/login');
  await login(page, 'user', 'pass');

  const errorMessage = await page.locator('.error').textContent();
  expect(errorMessage, '登录应显示错误消息').toBeTruthy();
  expect(errorMessage).toContain('用户名或密码错误');
});
```

---

### 5.2 使用 test.step() 组织测试

```javascript
test('结账流程', async ({ page }) => {
  await test.step('添加商品到购物车', async () => {
    await page.goto('/products');
    await page.getByRole('button', { name: '添加到购物车' }).click();
  });

  await test.step('查看购物车', async () => {
    await page.goto('/cart');
    await expect(page.locator('.cart-item')).toHaveCount(1);
  });

  await test.step('结账', async () => {
    await page.getByRole('button', { name: '结账' }).click();
    await expect(page.getByText('订单已创建')).toBeVisible();
  });
});
```

---

### 5.3 调试技巧

#### 使用 Playwright Inspector

```bash
# 调试模式运行
npx playwright test --debug

# 有界面模式
npx playwright test --headed

# 慢动作模式
npx playwright test --headed --slow-mo=1000
```

**Inspector 功能**：
- 🎯 录制操作生成代码
- 🔍 检查选择器
- ⏯️ 单步执行
- 📸 查看页面快照

#### 检查选择器匹配

```javascript
// 检查选择器匹配多少个元素
const count = await page.getByText('提交').count();
console.log(`找到 ${count} 个匹配的元素`);

// 获取所有匹配元素
const elements = await page.getByText('提交').all();
console.log(`共 ${elements.length} 个`);
```

#### 使用 Trace 查看失败原因

```bash
# 运行测试
npx playwright test

# 查看trace
npx playwright show-trace trace.zip
```

**Trace Viewer 显示**：
- 每一步操作
- DOM 快照
- 网络请求
- 控制台日志
- 时间线

#### 调试特定测试

```javascript
// 使用 test.only() 调试单个测试
test.only('调试此测试', async ({ page }) => {
  await page.goto('/');
  // 调试逻辑...
});
```

---

## 6. 代码组织

### 6.1 使用页面对象模式

```javascript
// pages/LoginPage.js
class LoginPage {
  constructor(page) {
    this.page = page;
    this.usernameInput = page.getByLabel('用户名');
    this.passwordInput = page.getByLabel('密码');
    this.loginButton = page.getByRole('button', { name: '登录' });
  }

  async login(username, password) {
    await this.usernameInput.fill(username);
    await this.passwordInput.fill(password);
    await this.loginButton.click();
  }
}

// tests/login.spec.js
test('登录测试', async ({ page }) => {
  const loginPage = new LoginPage(page);
  await page.goto('/login');
  await loginPage.login('user', 'pass');
});
```

---

### 6.2 提取通用函数

```javascript
// utils/helpers.js
async function login(page, username, password) {
  await page.goto('/login');
  await page.getByLabel('用户名').fill(username);
  await page.getByLabel('密码').fill(password);
  await page.getByRole('button', { name: '登录' }).click();
  await page.waitForURL('/dashboard');
}

async function createTestUser(data) {
  const response = await apiRequest.post('/api/users', { data });
  return response.id;
}

module.exports = { login, createTestUser };
```

---

### 6.3 目录结构最佳实践

```
tests/
├── e2e/                    # 端到端测试
│   ├── auth/
│   │   └── login.spec.js
│   └── checkout/
│       └── checkout.spec.js
├── integration/            # 集成测试
│   └── api/
│       └── api.spec.js
├── pages/                  # 页面对象
│   ├── LoginPage.js
│   └── DashboardPage.js
├── fixtures/               # 测试数据
│   └── test-data.json
├── utils/                  # 工具函数
│   └── helpers.js
└── playwright.config.js    # 配置文件
```

---

## 7. 断言最佳实践

### 7.1 使用显式断言

```javascript
// ❌ 隐式断言（不稳定）
await page.click('#button');
// 假设点击成功

// ✅ 显式断言（稳定）
await page.click('#button');
await expect(page).toHaveURL('/success');
await expect(page.getByText('操作成功')).toBeVisible();
```

---

### 7.2 断言消息清晰

```javascript
// ❌ 模糊的断言
expect(await page.textContent('.status')).toBe('success');

// ✅ 清晰的断言消息
const status = await page.locator('.status').textContent();
expect(status, '状态应该是 success').toBe('success');

// ✅ 使用 toBeTruthy 的消息
await expect(page.getByText('欢迎'), '登录后应显示欢迎消息').toBeVisible();
```

---

### 7.3 软断言（Soft Assertions）

```javascript
import { expect } from '@playwright/test';

test('软断言示例', async ({ page }) => {
  await page.goto('/dashboard');

  // 收集所有断言失败
  await expect.soft(page.getByRole('heading', { name: '仪表板' })).toBeVisible();
  await expect.soft(page.getByRole('link', { name: '产品' })).toBeVisible();
  await expect.soft(page.getByRole('link', { name: '订单' })).toBeVisible();

  // 即使有失败，测试也会继续
  // 所有失败会在测试结束时报告
});
```

---

## 8. 配置管理

### 8.1 环境特定配置

```javascript
// playwright.config.js
module.exports = defineConfig({
  // 基础 URL
  baseURL: process.env.BASE_URL || 'http://localhost:3000',

  // 测试超时
  timeout: process.env.CI ? 60000 : 30000,

  // 并行 worker
  workers: process.env.CI ? 2 : 4,
});
```

---

### 8.2 多项目配置

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
      name: 'api-tests',
      testMatch: '**/api/**/*.spec.js',
    },
  ],
});
```

---

## 9. CI/CD 集成最佳实践

### 9.1 CI 中禁用 headed 模式

```javascript
// playwright.config.js
module.exports = defineConfig({
  use: {
    headless: process.env.CI ? true : false,
  },
});
```

---

### 9.2 生成 JUnit 报告

```javascript
module.exports = defineConfig({
  reporter: [
    ['html'],
    ['junit', { outputFile: 'junit-results.xml' }],
    ['json', { outputFile: 'test-results.json' }],
  ],
});
```

---

### 9.3 CI 环境适配

```javascript
// 环境检测
const isCI = process.env.CI === 'true';
const isHeadless = !process.env.DISPLAY;

// 环境感知的配置
const config = {
  timeout: isCI ? 10000 : 5000,
  visibilityCheck: isHeadless ? 'toBeAttached' : 'toBeVisible',
  screenshotOnFailure: isCI ? 'only-on-failure' : 'on'
};

// 使用示例
async function clickAndVerify(page, selector, expectedText) {
  await selector.click();
  await page.waitForLoadState('domcontentloaded');

  // CI环境使用toBeAttached，本地使用toBeVisible
  if (config.visibilityCheck === 'toBeAttached') {
    await expect(page.getByText(expectedText).first()).toBeAttached({
      timeout: config.timeout
    });
  } else {
    await expect(page.getByText(expectedText).first()).toBeVisible({
      timeout: config.timeout
    });
  }
}
```

---

## 10. 维护性最佳实践

### 10.1 定期更新依赖

```bash
# 更新 Playwright
npm install -D @playwright/test@latest

# 更新浏览器
npx playwright install
```

---

### 10.2 删除未使用的测试

```javascript
// 标记为跳过但保留测试
test.skip('待实现的测试', async ({ page }) => {
  // TODO: 实现此测试
});

// 或完全删除不使用的测试
```

---

### 10.3 定期审查测试

- 删除重复测试
- 合并相似测试
- 更新过时的选择器
- 优化慢速测试

---

## 总结

### 关键要点

1. ✅ **使用稳定的 select** - getByRole > getByLabel > getByTestId
2. ✅ **测试独立性** - 测试间不能有依赖
3. ✅ **避免固定延迟** - 使用明确的等待条件
4. ✅ **并行执行** - fullyParallel: true
5. ✅ **清晰的错误消息** - 帮助快速定位问题
6. ✅ **使用 POM** - 提高代码可维护性
7. ✅ **定期审查** - 保持测试套件健康

### 常见陷阱

| 陷阱 | 解决方案 |
|------|----------|
| 使用 ref 属性 | 使用语义化选择器 |
| 测试间有依赖 | 每个测试独立设置 |
| 使用固定延迟 | 使用明确等待 |
| CSS 类选择器 | 使用 getByRole |
| 测试太慢 | 启用并行、减少等待 |
```

---

## 测试代码审查清单

在编写或审查测试代码时，确保：

- [ ] 所有 `getByText()` 都添加了 `.first()` 或 `.nth()`
- [ ] Element UI 组件使用 `.el-select` 等组件库 class
- [ ] Ant Design 组件使用 `.ant-select` 等组件库 class
- [ ] CI 环境使用 `toBeAttached()` 而非 `toBeVisible()`
- [ ] iframe 操作使用 `frameLocator()` 而非 `page` 方法
- [ ] 点击操作后添加适当等待
- [ ] 动态内容加载使用 `waitForLoadState('networkidle')`
- [ ] 错误处理添加有意义的日志
- [ ] 选择器不依赖组件内部 DOM 结构
- [ ] 测试数据使用固定值而非随机值
- [ ] 超时时间在 CI 环境适当增加
- [ ] ❌ 不使用 `ref` 属性
