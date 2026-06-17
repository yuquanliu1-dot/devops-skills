# 常见陷阱与解决方案

## 目录

- [陷阱 1: 使用 ref 属性](#陷阱-1-使用-ref-属性)
- [陷阱 2: 多元素匹配](#陷阱-2-多元素匹配)
- [陷阱 3: 不等待动态内容](#陷阱-3-不等待动态内容)
- [陷阱 4: 使用固定延迟](#陷阱-4-使用固定延迟)
- [陷阱 5: 忽略网络空闲状态](#陷阱-5-忽略网络空闲状态)
- [陷阱 6: 错误的选择器优先级](#陷阱-6-错误的选择器优先级)
- [陷阱 7: FrameLocator API 误用](#陷阱-7-framelocator-api-误用)
- [陷阱 8: 无头模式断言失败](#陷阱-8-无头模式断言失败)

---

## 陷阱 1: 使用 ref 属性

### ❌ 错误做法

```javascript
// ref 属性只在 MCP Playwright 快照中存在
await page.locator('[ref="e10"]').fill('姓名');
await page.locator('[ref="e15"]').click();
```

**为什么错误?**
- `ref` 属性是 MCP Playwright 工具生成的临时属性
- 只存在于页面快照中
- 实际测试运行时元素根本没有这个属性
- 会导致 `Element not found` 错误

### ✅ 正确做法

```javascript
// 使用语义化选择器
await page.getByRole('textbox', { name: /姓名|name/i }).fill('姓名');
await page.getByRole('button', { name: /提交|submit/i }).click();

// 或使用 HTML 属性
await page.locator('input[name="fullname"]').fill('姓名');
await page.locator('button[type="submit"]').click();

// 或使用 label
await page.getByLabel('姓名').fill('姓名');
```

### 如何识别 ref 属性

**快照示例:**
```html
<input ref="e10" placeholder="请输入姓名" />
<button ref="e15">提交</button>
```

**识别方法:**
- `ref="e10"` - ref 属性,数字或字母数字组合
- 只在 MCP Playwright 工具生成的快照中出现

---

## 陷阱 2: 多元素匹配

### ❌ 错误做法

```javascript
// 页面有多个 "941" 时会报错
await expect(page.locator('text=941')).toBeVisible();

// 严格模式: locator 指向多个元素时抛出错误
// Error: strict mode violation: locator('text=941') points to 3 elements
```

**为什么错误?**
- Playwright 默认使用严格模式
- 选择器匹配多个元素时会抛出错误
- 测试不稳定,可能每次匹配到不同元素

### ✅ 正确做法

```javascript
// 方法 1: 使用 first() 获取第一个匹配元素
await expect(page.locator('text=941').first()).toBeVisible();

// 方法 2: 使用 nth() 获取特定索引的元素
await expect(page.locator('text=941').nth(1)).toBeVisible();

// 方法 3: 使用更具体的选择器
await expect(page.locator('#totalCount:has-text("941")')).toBeVisible();
await expect(page.getByRole('listitem').filter({ hasText: '941' })).toBeVisible();

// 方法 4: 使用 getByRole + name 组合
await expect(page.getByRole('textbox', { name: '总数量' })).toBeVisible();
```

### 选择器优化示例

```javascript
// ❌ 太宽泛
page.locator('button')  // 匹配所有按钮
page.locator('text=确定')  // 匹配所有"确定"文本

// ✅ 更具体
page.getByRole('button', { name: '确定' })  // 只匹配确定按钮
page.locator('.modal button:has-text("确定")')  // 模态框中的确定按钮
page.locator('#submit-btn')  // 使用 ID
```

---

## 陷阱 3: 不等待动态内容

### ❌ 错误做法

```javascript
// 直接操作可能失败,数据未加载
await page.goto('/dynamic');
await page.locator('.result').click();  // 可能失败: 元素不存在

// 测试不稳定,有时成功有时失败
```

**为什么错误?**
- 现代应用大量使用 AJAX 动态加载
- 页面加载后数据还在请求中
- 元素尚未渲染完成就尝试操作

### ✅ 正确做法

```javascript
// 方法 1: 等待网络空闲(推荐)
await page.goto('/dynamic');
await page.waitForLoadState('networkidle');  // 等待所有网络请求完成
await page.locator('.result').click();

// 方法 2: 等待特定元素出现
await page.goto('/dynamic');
await expect(page.locator('.result')).toBeVisible({ timeout: 10000 });
await page.locator('.result').click();

// 方法 3: 等待 DOM 加载 + 网络空闲
await page.goto('/dynamic', { waitUntil: 'domcontentloaded' });
await page.waitForLoadState('networkidle');

// 方法 4: 等待特定条件
await page.goto('/dynamic');
await page.waitForFunction(() => {
  return document.querySelectorAll('.result').length > 0;
});
await page.locator('.result').click();
```

### waitForLoadState 参数说明

```javascript
// domcontentloaded - DOM 解析完成即可(默认)
await page.waitForLoadState('domcontentloaded');

// load - 页面及所有资源加载完成
await page.waitForLoadState('load');

// networkidle - 至少 500ms 内无网络请求(推荐用于动态页面)
await page.waitForLoadState('networkidle');

// 组合使用
await page.waitForLoadState('domcontentloaded');
await page.waitForLoadState('networkidle');
```

---

## 陷阱 4: 使用固定延迟

### ❌ 错误做法

```javascript
// 浪费时间且不稳定
await page.waitForTimeout(5000);  // 等待 5 秒
await page.click('button');

// 问题:
// 1. 如果页面 1 秒就加载完,浪费 4 秒
// 2. 如果页面需要 6 秒,测试失败
// 3. 测试运行时间长
```

**为什么错误?**
- 固定延迟浪费时间
- 无法适应不同网络环境
- 测试不稳定,时快时慢

### ✅ 正确做法

```javascript
// 方法 1: 使用条件等待(推荐)
await expect(page.locator('.button')).toBeVisible();
await page.click('button');

// 方法 2: 等待网络空闲
await page.waitForLoadState('networkidle');

// 方法 3: 等待 URL 变化
await page.waitForURL('**/dashboard');

// 方法 4: 等待特定状态
await page.waitForFunction(() => {
  return window.appState === 'ready';
});

// 方法 5: 等待元素可点击
await page.waitForSelector('button', { state: 'attached' });
await page.click('button');
```

### 何时可以用 waitForTimeout

```javascript
// ⚠️ 少数情况可以使用:
// 1. 等待动画完成
await page.click('button');
await page.waitForTimeout(300);  // 等待动画
await expect(page.locator('.modal')).toBeVisible();

// 2. 调试时临时使用
await page.waitForTimeout(5000);  // 方便观察

// 3. 等待外部服务(如支付回调)
await page.waitForTimeout(3000);  // 给服务端处理时间
```

---

## 陷阱 5: 忽略网络空闲状态

### ❌ 错误做法

```javascript
// 只等待 DOM 加载
await page.goto('/data');
await page.waitForLoadState('domcontentloaded');

// 立即操作,但数据可能还在加载
await expect(page.locator('.data-list')).toHaveCount(10);  // 可能失败
```

**为什么错误?**
- `domcontentloaded` 只保证 DOM 解析完成
- 不保证数据加载完成
- AJAX 请求可能还在进行

### ✅ 正确做法

```javascript
// 动态页面必须等待 networkidle
await page.goto('/data');
await page.waitForLoadState('networkidle');  // 关键!

await expect(page.locator('.data-list')).toHaveCount(10);

// 或等待特定元素
await page.goto('/data');
await expect(page.locator('.data-list li')).toHaveCount(10, {
  timeout: 10000
});
```

### 实战示例: 单页应用(SPA)

```javascript
test('单页应用导航', async ({ page }) => {
  await page.goto('/');

  // 点击导航链接(单页应用,不会重新加载页面)
  await page.getByRole('link', { name: '用户中心' }).click();

  // ⚠️ domcontentloaded 立即返回(因为页面已经加载)
  // ✅ 必须等待 networkidle
  await page.waitForLoadState('networkidle');

  // 现在可以安全地验证新页面内容
  await expect(page.getByRole('heading', { name: '用户中心' })).toBeVisible();
});
```

---

## 陷阱 6: 错误的选择器优先级

### ❌ 错误做法

```javascript
// 使用脆弱的选择器
await page.locator('.container div:nth-child(2) span').click();
await page.locator('div > div > button').click();

// 问题:
// 1. CSS 类可能变化
// 2. DOM 结构可能调整
// 3. 测试脆弱,布局变化即失效
```

**选择器稳定性排序:**
```
⭐⭐⭐ 最稳定: 语义化 (getByRole, getByLabel)
⭐⭐ 较稳定: HTML 属性 (input[name="xxx"])
⭐ 一般: 文本内容 (:has-text())
⚠️ 不稳定: CSS 类 (.class-name)
❌ 最脆弱: DOM 结构 (div > div > button)
```

### ✅ 正确做法

```javascript
// 优先级 1: 语义化选择器(最稳定)
await page.getByRole('button', { name: '提交' }).click();
await page.getByLabel('用户名').fill('testuser');
await page.getByPlaceholder('搜索').fill('keyword');

// 优先级 2: HTML 属性(较稳定)
await page.locator('input[name="username"]').fill('testuser');
await page.locator('button[type="submit"]').click();
await page.locator('[data-testid="submit-btn"]').click();

// 优先级 3: 文本内容(一般)
await page.locator('text=提交').click();
await page.locator('.item:has-text("重要")').click();

// ⚠️ 优先级 4: CSS 类(谨慎使用)
await page.locator('.submit-button').click();  // 类名可能变化

// ❌ 优先级 5: DOM 结构(避免使用)
await page.locator('div form button').click();  // 脆弱
```

### 📘 场景化选择器策略

> **重要**：不同类型的应用应使用不同的选择器优先级！

#### 通用应用（React/Vue/组件库）

```
1. getByRole() - 最稳定
2. getByLabel() - 表单元素
3. getByPlaceholder() - 输入框
4. id 属性 - 如果存在
5. 组件库 class - Element UI/Ant Design
```

#### 原生 HTML 应用（静态页面）

```
1. #id 属性 - 最稳定（原生 HTML 特有）
2. [name="xxx"] - 表单元素
3. getByRole() - 语义化元素
4. getByLabel() - 表单关联
```

**如何识别应用类型**：
- 原生 HTML：使用 `<select>`, `<input type="text">`, `<button>` 标签
- 组件库：使用 `.el-select`, `.ant-select`, `.v-select` 等 class

详细参考：[最佳实践 - 1.6 原生 HTML 应用选择器](best-practices.md#16-原生-html-应用选择器)

### 语义化选择器完整示例

```javascript
test('表单填写', async ({ page }) => {
  // ✅ 语义化选择器
  await page.getByRole('textbox', { name: /用户名|username/i }).fill('testuser');
  await page.getByRole('textbox', { name: /密码|password/i }).fill('password123');
  await page.getByRole('checkbox', { name: /同意条款/i }).check();
  await page.getByRole('button', { name: /登录|login/i }).click();

  // ✅ 验证成功
  await expect(page.getByRole('heading', { name: /欢迎|welcome/i })).toBeVisible();
  await expect(page.getByRole('link', { name: /个人中心/i })).toBeVisible();
});
```

---

## 陷阱 7: FrameLocator API 误用

### ❌ 错误做法

```javascript
// 错误：对 FrameLocator 调用 Page 的方法
const iframe = page.frameLocator('#content-frame');

// ❌ FrameLocator 不支持这些方法！
await iframe.waitForLoadState('networkidle');     // TypeError!
await iframe.waitForTimeout(500);                  // TypeError!
await iframe.waitForSelector('div');               // TypeError!
await iframe.goto('https://example.com');          // TypeError!
```

**为什么错误?**
- `FrameLocator` 是定位器类，用于定位 iframe 内的元素
- 它**不是** Page 对象，不支持页面级别的方法
- 只有 `Frame` 对象才支持页面方法

### ✅ 正确做法

```javascript
// ✅ 正确区分 FrameLocator 和 Frame

// FrameLocator - 用于定位 iframe 内的元素
const iframe = page.frameLocator('#content-frame');

// ✅ FrameLocator 只用于元素定位和操作
await iframe.getByRole('button', { name: '提交' }).click();
await iframe.getByLabel('用户名').fill('test');
await expect(iframe.getByText('操作成功')).toBeVisible();

// Frame - 用于页面级别的操作
const frame = page.frame('#content-frame');

// ✅ Frame 支持页面方法
await frame.waitForLoadState('networkidle');
await frame.waitForURL('**/success');
await frame.evaluate(() => console.log('Frame loaded'));
```

### Frame vs FrameLocator 对照表

| 功能 | FrameLocator | Frame |
|------|-------------|-------|
| **用途** | 定位 iframe 内的元素 | 页面级别的操作 |
| **获取方式** | `page.frameLocator(selector)` | `page.frame(selector)` |
| **元素定位** | ✅ 支持 `getByRole()`, `locator()` | ✅ 支持 `locator()`, `$()` |
| **点击操作** | ✅ 支持 `click()` | ✅ 支持 |
| **填表操作** | ✅ 支持 `fill()` | ✅ 支持 |
| **等待状态** | ❌ 不支持 | ✅ 支持 `waitForLoadState()` |
| **页面导航** | ❌ 不支持 | ✅ 支持 `goto()`, `waitForURL()` |
| **执行脚本** | ❌ 不支持 | ✅ 支持 `evaluate()` |

### 完整示例

```javascript
test('iframe 测试正确做法', async ({ page }) => {
  await page.goto('http://example.com');

  // ✅ 获取 Frame 对象用于等待
  const frameElement = await page.waitForSelector('#content-frame');
  const frame = await frameElement.contentFrame();
  await frame.waitForLoadState('networkidle');  // Frame 支持此方法

  // ✅ 使用 FrameLocator 定位元素
  const iframe = page.frameLocator('#content-frame');

  // ✅ 使用语义化选择器
  await expect(iframe.getByRole('heading', { name: '标题' })).toBeVisible();
  await iframe.getByRole('button', { name: '提交' }).click();

  // ✅ 验证结果
  await expect(iframe.getByText('操作成功')).toBeVisible();
});
```

### 常见错误消息

```
TypeError: iframe.waitForLoadState is not a function
TypeError: iframe.waitForTimeout is not a function
TypeError: iframe.goto is not a function
```

**解决方案**：使用 `page.frame()` 获取 Frame 对象来调用这些方法。

---

## 快速参考表

| 陷阱 | 错误示例 | 正确做法 |
|------|---------|---------|
| 使用 ref | `page.locator('[ref="e10"]')` | `page.getByRole('textbox')` |
| 多元素匹配 | `page.locator('text=941')` | `page.locator('text=941').first()` |
| 不等待动态内容 | 直接操作元素 | `waitForLoadState('networkidle')` |
| 固定延迟 | `waitForTimeout(5000)` | `expect().toBeVisible()` |
| 忽略网络空闲 | `waitForLoadState('domcontentloaded')` | `waitForLoadState('networkidle')` |
| 错误选择器 | `.container div button` | `getByRole('button')` |
| FrameLocator 误用 | `iframe.waitForLoadState()` | `frame.waitForLoadState()` |

---

## 实战检查清单

在编写测试时,确保:

- [ ] ❌ 不使用 `ref` 属性
- [ ] ✅ 使用语义化选择器 (`getByRole`, `getByLabel`)
- [ ] ✅ 处理多元素匹配 (`.first()`, 更具体的选择器)
- [ ] ✅ 等待动态内容 (`waitForLoadState('networkidle')`)
- [ ] ❌ 避免固定延迟 (`waitForTimeout`)
- [ ] ✅ 选择器从稳定到不稳定排列
- [ ] ✅ 正确区分 FrameLocator（定位元素）和 Frame（页面操作）
- [ ] ✅ 无头模式使用 `toBeAttached()` 而非 `toBeVisible()`

---

## 陷阱 8: 无头模式断言失败

### ❌ 错误做法

```javascript
// 测试在本地通过，但在 CI/CD（无头模式）失败
test('示例测试', async ({ page }) => {
  await page.goto('/page');
  await page.getByRole('button', { name: '加载' }).click();

  // ❌ 在无头模式可能失败
  await expect(page.getByText('数据加载完成')).toBeVisible();
  await expect(page.locator('.result')).toBeVisible();
  await expect(page.getByRole('status')).toBeVisible();
});
```

**为什么在无头模式会失败?**
- `toBeVisible()` 要求元素在视口内且不被遮挡
- 无头模式默认视口较小（1280x720），元素可能在视口外
- 无头模式没有实际渲染，某些 CSS 样式计算不同
- iframe 内的元素可能无法正确计算可见性

### ✅ 正确做法

#### 方案 1: 使用 toBeAttached()（推荐）

```javascript
// ✅ 使用 toBeAttached() - 只检查元素是否在 DOM 中
test('无头模式兼容测试', async ({ page }) => {
  await page.goto('/page');
  await page.getByRole('button', { name: '加载' }).click();

  // ✅ toBeAttached() 在无头模式稳定
  await expect(page.getByText('数据加载完成')).toBeAttached();
  await expect(page.locator('.result')).toBeAttached();
  await expect(page.getByRole('status')).toBeAttached();
});
```

#### 方案 2: 环境感知断言

```javascript
// ✅ 根据环境选择断言方式
const isCI = process.env.CI === 'true';
const isHeadless = process.env.HEADED !== 'true';

// CI/无头模式使用 toBeAttached，本地使用 toBeVisible
const assertVisible = isCI || isHeadless ? 'toBeAttached' : 'toBeVisible';

test('环境感知测试', async ({ page }) => {
  await page.goto('/page');
  await page.getByRole('button', { name: '加载' }).click();

  // ✅ 根据环境选择断言
  await expect(page.getByText('数据加载完成'))[assertVisible]();
});
```

#### 方案 3: 滚动到元素位置

```javascript
test('滚动后验证可见性', async ({ page }) => {
  await page.goto('/page');

  const element = page.getByRole('listitem').nth(10);

  // ✅ 先滚动到元素位置
  await element.scrollIntoViewIfNeeded();

  // 然后再验证可见性
  await expect(element).toBeVisible();
});
```

#### 方案 4: 使用 test.configure() 全局配置

```javascript
// ✅ 在配置文件中设置全局断言方式
// playwright.config.js
module.exports = defineConfig({
  use: {
    // 根据环境选择默认断言
    actionTimeout: 10000,
  },
});

// 或在测试文件中
test.describe('无头模式测试', () => {
  // 对整个测试组使用 toBeAttached
  test.configure({ retries: isCI ? 2 : 0 });

  test('测试1', async ({ page }) => {
    await page.goto('/page');
    await expect(page.getByRole('button')).toBeAttached();
  });
});
```

### toBeAttached vs toBeVisible 对照表

| 断言方法 | 检查内容 | 无头模式 | 有头模式 | 推荐场景 |
|---------|---------|---------|---------|---------|
| `toBeAttached()` | 元素在 DOM 中 | ✅ 稳定 | ✅ 稳定 | **CI/无头模式**（推荐） |
| `toBeVisible()` | 元素可见且在视口内 | ⚠️ 可能失败 | ✅ 稳定 | 本地调试、视觉验证 |
| `toBeInViewport()` | 元素在视口内 | ⚠️ 不稳定 | ✅ 稳定 | 视口相关测试 |

### 无头模式最佳实践

```javascript
// ✅ 推荐的无头模式测试写法
test('无头模式最佳实践', async ({ page }) => {
  // 1. 使用 toBeAttached() 而非 toBeVisible()
  await expect(page.getByRole('button')).toBeAttached();

  // 2. 优先使用语义化选择器（更稳定）
  await expect(page.getByRole('heading', { name: '标题' })).toBeAttached();

  // 3. 避免依赖元素位置
  await expect(page.getByText('内容')).toBeAttached();

  // 4. iframe 内的元素使用 toBeAttached()
  const iframe = page.frameLocator('#content-frame');
  await expect(iframe.getByRole('button')).toBeAttached();

  // 5. 如需验证可交互性，使用 toBeEditable() 或 toBeEnabled()
  await expect(page.getByRole('textbox')).toBeEditable();
  await expect(page.getByRole('button')).toBeEnabled();
});
```

### 常见错误消息

```
Error: element.isVisible() timed out
Error: waiting for selector ".result" to be visible failed
Error: Expected element to be visible, but it was not found in the viewport
```

**解决方案**：
1. 将 `toBeVisible()` 改为 `toBeAttached()`
2. 或使用环境感知的断言方式
3. 或添加 `scrollIntoViewIfNeeded()` 滚动到元素

---

## 陷阱 9: 组件库选择器失效

### ❌ 错误做法

```javascript
// Element UI 的 span 可能拦截点击
await page.getByRole('combobox', { name: '研发类型' }).click();
// Error: span intercepts pointer events

// Ant Design 通用 CSS 类不稳定
await page.locator('.ant-btn-primary').click();
// CSS 类可能变化
```

### ✅ 正确做法

```javascript
// Element UI: 使用组件库特定 class
await page.locator('.el-select').nth(0).click();
await page.getByText('选项文本').first().click();

// Ant Design: 使用组件库特定 class
await page.locator('.ant-select').nth(0).click();
await page.locator('.ant-select-item-option').filter({ hasText: '选项' }).click();
```

### 为什么会失败？

组件库（如 Element UI、Ant Design）在内部使用嵌套的 `span`、`div` 等元素来实现组件，这些元素可能拦截点击事件。使用语义化选择器（如 `getByRole`）时，可能点击到被拦截的元素。

**完整参考**：[最佳实践 - 组件库特定选择器](best-practices.md#15-组件库特定选择器)

---

## 快速参考表

| 陷阱 | 错误示例 | 正确做法 |
|------|---------|---------|
| 使用 ref | `page.locator('[ref="e10"]')` | `page.getByRole('textbox')` |
| 多元素匹配 | `page.locator('text=941')` | `page.locator('text=941').first()` |
| 不等待动态内容 | 直接操作元素 | `waitForLoadState('networkidle')` |
| 固定延迟 | `waitForTimeout(5000)` | `expect().toBeAttached()` |
| 忽略网络空闲 | `waitForLoadState('domcontentloaded')` | `waitForLoadState('networkidle')` |
| 错误选择器 | `.container div button` | `getByRole('button')` |
| FrameLocator 误用 | `iframe.waitForLoadState()` | `frame.waitForLoadState()` |
| **无头模式断言** | `toBeVisible()` | `toBeAttached()` |

---

## 相关资源

- [选择器优先级 - SKILL.md](../SKILL.md#选择器优先级)
- [调试技巧 - 调试指南](debugging-guide.md)
- [测试模板 - test-templates.md](test-templates.md)
- [故障排除 - troubleshooting.md](troubleshooting.md)
