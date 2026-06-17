# 不稳定测试管理指南

不稳定测试（Flaky Tests）是指在没有代码变更的情况下，有时通过、有时失败的测试。这是自动化测试中最常见且最令人头疼的问题之一。

---

## 目录

1. [识别不稳定测试](#识别不稳定测试)
2. [常见不稳定原因](#常见不稳定原因)
3. [修复策略](#修复策略)
4. [隔离方法](#隔离方法)
5. [预防措施](#预防措施)
6. [工作流程](#工作流程)

---

## 识别不稳定测试

### 方法1：重复运行测试

```bash
# 单个测试重复运行10次
npx playwright test tests/example.spec.js --repeat-each=10

# 带重试机制运行
npx playwright test tests/example.spec.js --retries=3

# 完整测试套件重复运行
npx playwright test --repeat-each=3
```

### 方法2：分析测试报告

```bash
# 生成 JSON 报告
npx playwright test --reporter=json > results.json

# 使用脚本分析不稳定测试
node scripts/analyze-flaky-tests.js results.json
```

### 方法3：CI/CD 历史分析

查看 CI/CD 历史记录，寻找间歇性失败的测试：

```bash
# GitHub Actions
# 查看 Actions 标签页，寻找带黄色警告的运行

# Jenkins
# 查看测试趋势图，识别不稳定的测试

# GitLab CI
# 查看 Pipelines 历史，注意间歇性失败
```

---

## 常见不稳定原因

### 1. 竞态条件（Race Conditions）

**症状**：测试有时通过，有时失败，错误信息通常是元素未找到或不可点击

**原因**：代码在元素准备好之前就尝试交互

```javascript
// ❌ 不稳定的代码
await page.click('[data-testid="submit-button"]');

// ✅ 稳定的代码
await page.locator('[data-testid="submit-button"]').click();
```

**为什么 locator 更稳定**：
- locator 内置自动等待
- 等待元素出现在 DOM 中
- 等待元素可见
- 等待元素可操作

### 2. 网络时序问题

**症状**：API 请求还在进行中时继续操作

**原因**：没有等待网络请求完成

```javascript
// ❌ 不稳定的代码
await page.click('[data-testid="search-button"]');
await expect(page.locator('.results')).toBeVisible();

// ✅ 稳定的代码
await page.click('[data-testid="search-button"]');
await page.waitForResponse(resp =>
  resp.url().includes('/api/search') && resp.status() === 200
);
await expect(page.locator('.results')).toBeVisible();

// ✅ 或者使用网络空闲
await page.waitForLoadState('networkidle');
```

### 3. 动画和过渡效果

**症状**：动画期间点击失败

```javascript
// ❌ 不稳定的代码
await page.click('[data-testid="menu-item"]');

// ✅ 稳定的代码
await page.locator('[data-testid="menu-item"]').waitFor({ state: 'visible' });
await page.locator('[data-testid="menu-item"]').click();

// ✅ 或者等待动画结束
await page.waitForFunction(() => {
  const el = document.querySelector('[data-testid="menu-item"]');
  return getComputedStyle(el).animationName === 'none';
});
```

### 4. 多元素匹配

**症状**：getByText 或 getByLabel 匹配到多个元素

```javascript
// ❌ 不稳定的代码
await page.getByText('登录').click();

// ✅ 稳定的代码
await page.getByText('登录').first().click();

// ✅ 更好的方案
await page.getByRole('button', { name: '登录' }).click();
```

### 5. 测试间数据污染

**症状**：测试单独运行通过，批量运行失败

**原因**：测试间共享数据或状态

```javascript
// ❌ 不稳定的代码
test('创建用户', async ({ page }) => {
  await page.goto('/users/new');
  await page.fill('#name', 'Test User');
  await page.click('[data-testid="save"]');
});

test('编辑用户', async ({ page }) => {
  await page.goto('/users/1/edit'); // 假设用户 ID 为 1
  // 如果上一个测试失败，用户可能不存在
});

// ✅ 稳定的代码
test('创建用户', async ({ page }) => {
  const uniqueId = Date.now();
  await page.goto('/users/new');
  await page.fill('#name', `Test User ${uniqueId}`);
  await page.click('[data-testid="save"]');
});

// ✅ 或者清理测试数据
test.afterEach(async ({ page }) => {
  await page.goto('/cleanup');
  await page.click('[data-testid="clear-all-data"]');
});
```

### 6. 硬编码等待时间

**症状**：在不同机器上表现不同

```javascript
// ❌ 不稳定的代码
await page.waitForTimeout(5000);

// ✅ 稳定的代码
await page.waitForLoadState('networkidle');
await page.waitForSelector('[data-testid="loaded"]');
```

### 7. 依赖外部服务

**症状**：外部服务不稳定导致测试失败

**原因**：依赖的 API、数据库、第三方服务

```javascript
// ❌ 不稳定的代码
test('检查天气', async ({ page }) => {
  await page.goto('/weather');
  // 依赖外部天气 API
});

// ✅ 稳定的代码
test('检查天气', async ({ page }) => {
  // Mock 外部 API
  await page.route('**/api/weather', route => {
    route.fulfill({
      status: 200,
      body: JSON.stringify({ temp: 25, condition: 'sunny' })
    });
  });

  await page.goto('/weather');
});
```

### 8. 时间和日期依赖

**症状**：特定时间或日期测试失败

```javascript
// ❌ 不稳定的代码
test('显示今日日期', async ({ page }) => {
  await page.goto('/');
  const today = new Date().toDateString();
  await expect(page.getByText(today)).toBeVisible();
});

// ✅ 稳定的代码
test('显示今日日期', async ({ page }) => {
  // 设置固定的测试时间
  await page.clock.setFixedTime('2024-01-01T00:00:00Z');
  await page.goto('/');
  await expect(page.getByText('Mon Jan 01 2024')).toBeVisible();
});
```

---

## 修复策略

### 策略1：使用语义化选择器

优先级：
1. `getByRole()` - 最稳定（语义化）
2. `getByLabel()` - 表单元素
3. `getByPlaceholder()` - 输入框
4. `getByText()` - 配合 `.first()` 使用
5. `getByTestId()` - 测试专用属性
6. `id 属性` - 原生 HTML 优先
7. `组件库 class` - Element UI/Ant Design
8. `locator()` - 使用属性选择器
9. ❌ CSS 类 - 最后选择

### 策略2：正确的等待模式

```javascript
// 等待元素可见
await page.locator('.element').waitFor({ state: 'visible' });

// 等待元素隐藏
await page.locator('.element').waitFor({ state: 'hidden' });

// 等待网络空闲
await page.waitForLoadState('networkidle');

// 等待特定响应
await page.waitForResponse(resp => resp.url().includes('/api/data'));

// 等待导航
await page.waitForURL('/dashboard');
```

### 策略3：使用 Playwright 的自动等待

Playwright 的 `locator` 自动等待：
- 元素出现在 DOM 中
- 元素可见
- 元素稳定（不在动画中）
- 元素可接收事件
- 元素不被遮挡

### 策略4：隔离测试数据

```javascript
// 为每个测试生成唯一数据
const uniqueId = `test-${Date.now()}`;
const uniqueEmail = `test+${Date.now()}@example.com`;

// 使用测试专用数据库
test.use({ launchOptions: { args: ['--use-test-db'] } });

// 清理测试数据
test.afterEach(async ({ page }) => {
  await page.request.post('/api/test/cleanup');
});
```

### 策略5：Mock 外部依赖

```javascript
// Mock API 响应
await page.route('**/api/external', route => {
  route.fulfill({
    status: 200,
    contentType: 'application/json',
    body: JSON.stringify({ success: true })
  });
});

// Mock 延迟
await page.route('**/api/slow', route => {
  setTimeout(() => {
    route.fulfill({
      status: 200,
      body: '{}'
    });
  }, 100);
});
```

---

### 策略6：组件库自动识别

当测试使用组件库的应用时，自动识别 UI 框架并使用相应的选择器策略。

```javascript
// 检测页面使用的 UI 框架
async function detectUIFramework(page) {
  const frameworks = {
    'Element UI': {
      indicator: '.el-select',
      patterns: {
        dropdown: '.el-select',
        option: '.el-select-dropdown__item',
        input: '.el-input__inner',
        button: '.el-button'
      }
    },
    'Ant Design': {
      indicator: '.ant-select',
      patterns: {
        dropdown: '.ant-select',
        option: '.ant-select-item-option',
        input: '.ant-input',
        button: '.ant-btn'
      }
    },
    'Vuetify': {
      indicator: '.v-select',
      patterns: {
        dropdown: '.v-select',
        option: '.v-list-item',
        input: '.v-input',
        button: '.v-btn'
      }
    },
    // 原生 HTML 应用
    'Vanilla': {
      indicator: 'select, input[type="text"], button',
      patterns: {
        dropdown: 'select[id], select[name]',
        option: 'option',
        input: 'input[type="text"], input[type="email"]',
        button: 'button[id], button[type="submit"]'
      }
    }
  };

  for (const [name, config] of Object.entries(frameworks)) {
    // 跳过 Vanilla 的检查，它作为默认值
    if (name === 'Vanilla') continue;

    const count = await page.locator(config.indicator).count();
    if (count > 0) return name;
  }

  return 'Vanilla'; // 原生 HTML
}

// 根据检测到的框架生成选择器
async function generateFrameworkAwareSelector(page, action) {
  const framework = await detectUIFramework(page);

  // 原生 HTML 应用使用 id 优先策略
  if (framework === 'Vanilla') {
    switch (action.type) {
      case 'click_dropdown':
        // 优先使用 id 选择器
        const byId = page.locator(`#${action.id}`);
        if (await byId.count() > 0) return byId;
        // 其次使用语义化选择器
        return page.getByRole('combobox');
      case 'select_option':
        // 原生 select 使用 selectOption 方法
        return page.locator('select');
      case 'fill_input':
        // 优先使用 id
        if (action.id) return page.locator(`#${action.id}`);
        // 其次使用 name
        if (action.name) return page.locator(`[name="${action.name}"]`);
        // 最后使用 label
        return page.getByLabel(action.label);
      default:
        return page.locator(`*${action.text}*`);
    }
  }

  // 组件库应用
  const patterns = frameworks[framework].patterns;
  switch (action.type) {
    case 'click_dropdown':
      return page.locator(patterns.dropdown).nth(action.index);
    case 'select_option':
      return page.locator(patterns.option).filter({ hasText: action.text });
    default:
      return page.locator(`*${action.text}*`);
  }
}
```

**使用场景**：
- 组件库升级导致选择器失效
- 多个项目使用不同组件库
- 需要编写通用的测试代码

---

## 隔离方法

### 方法1：使用 test.fixme()

标记测试为待修复，测试会运行但显示为"已修复"：

```javascript
test('不稳定的搜索测试', async ({ page }) => {
  test.fixme(true, '间歇性失败 - Issue #123');
  // 测试代码...
});
```

### 方法2：使用 test.skip()

跳过不稳定的测试：

```javascript
// 无条件跳过
test('不稳定的测试', async ({ page }) => {
  test.skip(true, '暂时禁用 - Issue #123');
  // 测试代码...
});

// 条件跳过（如：在 CI 中跳过）
test('Firefox 不稳定的测试', async ({ page }) => {
  test.skip(process.env.CI && process.env.BROWSER === 'firefox', 'Firefox 在 CI 中不稳定');
  // 测试代码...
});
```

### 方法3：使用 @flaky 标记

在配置中定义标记：

```javascript
// playwright.config.js
export default defineConfig({
  grep: process.env.CI ? invertGrep(/@flaky/) : undefined,
});
```

使用标记：

```javascript
test('@flaky 不稳定的测试', async ({ page }) => {
  // 测试代码...
});
```

### 方法4：创建单独的测试套件

```javascript
// flaky.spec.js
test.describe('@flaky 不稳定测试套件', () => {
  test('测试1', async ({ page }) => {
    // 不稳定的测试
  });

  test('测试2', async ({ page }) => {
    // 不稳定的测试
  });
});
```

---

## 预防措施

### 1. 编写稳定的测试

- ✅ 使用语义化选择器
- ✅ 等待明确的条件
- ✅ 使用测试数据隔离
- ✅ Mock 外部依赖
- ✅ 设置合理的超时时间

### 2. 代码审查

检查清单：
- [ ] 是否使用了固定延迟？
- [ ] 选择器是否足够稳定？
- [ ] 测试是否独立？
- [ ] 是否正确等待网络？
- [ ] 是否有硬编码的数据？

### 3. 持续监控

- 设置 CI 定期运行测试
- 监控测试通过率趋势
- 识别反复失败的测试
- 定期审查不稳定测试列表

### 4. 建立测试质量标准

- 不稳定率 < 5%
- 修复 Issue 的 SLA（如：7天内）
- 长期不稳定的测试应删除或重写

---

## 工作流程

### 不稳定测试修复流程

```
1. 发现不稳定测试
   ├─ CI 报告
   ├─ 团队反馈
   └─ 监控告警
   ↓
2. 添加隔离标记
   ├─ test.fixme()
   └─ 创建 Issue
   ↓
3. 分析根本原因
   ├─ 使用 Trace Viewer
   ├─ 查看截图和视频
   └─ 多次运行测试
   ↓
4. 实施修复
   ├─ 修改选择器
   ├─ 添加等待
   ├─ Mock 依赖
   └─ 隔离数据
   ↓
5. 验证修复
   ├─ 运行 10 次
   ├─ 检查 CI 通过
   └─ 代码审查
   ↓
6. 清理标记
   ├─ 移除 fixme/skip
   └─ 关闭 Issue
```

### 使用 Trace Viewer 调试

```bash
# 运行测试并生成追踪
npx playwright test --trace on

# 查看追踪
npx playwright show-trace artifacts/trace.zip
```

Trace Viewer 显示：
- 每一步操作
- DOM 快照
- 网络请求
- 控制台日志
- 时间线

---

## 示例代码

### 完整的稳定测试示例

```javascript
const { test, expect } = require('@playwright/test');

test.describe('用户登录', () => {
  test.beforeEach(async ({ page }) => {
    // Mock 外部 API
    await page.route('**/api/auth/login', route => {
      route.fulfill({
        status: 200,
        contentType: 'application/json',
        body: JSON.stringify({ token: 'mock-token' })
      });
    });
  });

  test('成功登录', async ({ page }) => {
    // 导航到登录页
    await page.goto('/login');

    // 等待页面加载
    await page.waitForLoadState('networkidle');

    // 填写表单（使用稳定的定位器）
    await page.getByLabel('用户名').fill('testuser');
    await page.getByLabel('密码', { exact: true }).fill('password123');

    // 提交表单
    await page.getByRole('button', { name: '登录' }).click();

    // 等待 API 响应
    await page.waitForResponse(resp =>
      resp.url().includes('/api/auth/login') && resp.status() === 200
    );

    // 验证跳转
    await expect(page).toHaveURL(/\/dashboard/);

    // 验证登录成功提示
    await expect(page.getByText('登录成功')).toBeVisible();
  });

  // 清理测试数据
  test.afterEach(async ({ page }) => {
    await page.request.post('/api/test/cleanup');
  });
});
```

---

## 参考资料

- [Playwright 最佳实践](https://playwright.dev/docs/best-practices)
- [Playwright 调试指南](https://playwright.dev/docs/debug)
- [Trace Viewer](https://playwright.dev/docs/trace-viewer)
