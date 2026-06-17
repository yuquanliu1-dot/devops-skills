# Playwright API 参考

本文档提供 Playwright 的核心 API 参考，包括定位策略、断言方法和等待机制。

## 核心 API

### 1. 定位器（Locator）

#### 1.1 page.getByRole() - 最稳定的定位方式

**语法**：
```javascript
page.getByRole(role, { options })
```

**常用 role 值**：
- `button` - 按钮
- `textbox` - 文本输入框
- `combobox` - 下拉框
- `link` - 链接
- `checkbox` - 复选框
- `radio` - 单选框
- `listitem` - 列表项

**示例**：
```javascript
// 精确匹配
await page.getByRole('button', { name: '提交' }).click();

// 正则匹配
await page.getByRole('button', { name: /提交/i }).click();

// 结合其他属性
await page.getByRole('textbox', { name: '用户名' }).fill('test');
```

**优先使用场景**：
- ✅ 交互元素（按钮、链接、表单）
- ✅ 有明确 role 属性的元素
- ✅ 需要可访问性支持的场景

---

#### 1.2 page.getByLabel() - 表单元素

**语法**：
```javascript
page.getByLabel(text, { options })
```

**示例**：
```javascript
// 通过 label 文本定位
await page.getByLabel('用户名').fill('testuser');
await page.getByLabel('密码', { exact: true }).fill('pass123');
```

**使用场景**：
- ✅ 表单输入框（input、textarea）
- ✅ 有 label 关联的元素

---

#### 1.3 page.getByPlaceholder() - 输入框

**语法**：
```javascript
page.getByPlaceholder(text, { options })
```

**示例**：
```javascript
await page.getByPlaceholder('请输入姓名').fill('张三');
await page.getByPlaceholder(/search/i, { exact: false }).fill('keyword');
```

---

#### 1.4 page.getByText() - 文本内容

**语法**：
```javascript
page.getByText(text, { options })
```

**示例**：
```javascript
// 精确匹配
await page.getByText('提交').click();

// 正则匹配
await page.getByText(/确定/i).click();

// 多元素匹配必须使用 .first() 或 .nth()
await page.getByText('确定').first().click();
await page.getByText('确定').nth(2).click();
```

**⚠️ 注意**： getByText 可能匹配多个元素，必须使用 `.first()` 或 `.nth()` 明确指定

---

#### 1.5 page.locator() - 通用定位器

**语法**：
```javascript
page.locator(selector, options)
```

**选择器类型**：
- CSS 选择器：`input[name="username"]`
- XPath：`//input[@name="username"]`
- Text 选择器：`text=Login`
- React/Vue selector：`_react=ComponentName`

**示例**：
```javascript
// CSS 选择器
await page.locator('input[name="username"]').fill('test');

// ID 选择器
await page.locator('#submit-btn').click();

// Class 选择器（最后选择）
await page.locator('.btn-primary').click();

// 组合选择器
await page.locator('button.submit[type="submit"]').click();
```

---

### 2. 断言（Expect）

#### 2.1 可见性断言

```javascript
// 元素可见
await expect(locator).toBeVisible();
await expect(locator).toBeHidden();

// 元素存在
await expect(locator).toBeAttached();
await expect(locator).toHaveCount(3);
```

#### 2.2 文本内容断言

```javascript
// 精确匹配
await expect(locator).toHaveText('提交');
await expect(locator).toHaveText(/success/i);

// 包含文本
await expect(locator).toContainText('用户');
await expect(locator).toHaveText('user123');
```

#### 2.3 属性断言

```javascript
// HTML 属性
await expect(locator).toHaveAttribute('href', '/login');
await expect(locator).toHaveClass('active');

// JS 属性
await expect(locator).toHaveJSProperty('disabled', true);
await expect(locator).toHaveValue('test');
```

#### 2.4 状态断言

```javascript
// 可编辑状态
await expect(locator).toBeEditable();
await expect(locator).toBeDisabled();
await expect(locator).toBeChecked();

// URL 断言
await expect(page).toHaveURL('/dashboard');
await expect(page).toHaveTitle('Dashboard');
```

#### 2.5 元素数量断言

```javascript
await expect(locator).toHaveCount(3);
await expect(locator).toHaveText(/\d+/);  // 正则匹配数字
```

#### 2.6 断言规则（强制执行）

**规则 1：所有 getByText() 断言必须添加 .first()**

```javascript
// ❌ 错误
await expect(page.getByText('登录成功')).toBeVisible();

// ✅ 正确
await expect(page.getByText('登录成功').first()).toBeVisible();
```

**规则 2：所有 locator() 断言必须添加 .first() 或更具体的选择器**

```javascript
// ❌ 错误
await expect(page.locator('table')).toBeVisible();

// ✅ 正确
await expect(page.locator('table').first()).toBeVisible();
await expect(page.getByRole('table')).toBeVisible();  // 更好的方式
```

**规则 3：常量定义时也要添加 .first()**

```javascript
// ❌ 错误
const countElement = frame.getByText('100');

// ✅ 正确
const countElement = frame.getByText('100').first();
await expect(countElement).toBeVisible();
```

---

### 3. 等待机制

#### 3.1 waitForLoadState() - 等待页面状态

```javascript
// 等待网络空闲
await page.waitForLoadState('networkidle');

// 等待 DOM 加载完成
await page.waitForLoadState('domcontentloaded');

// 等待所有网络请求完成
await page.waitForLoadState('load');
```

**使用场景**：
- ✅ 页面初始加载
- ✅ AJAX 操作后
- ✅ 导航后

---

#### 3.2 waitForSelector() - 等待元素

```javascript
// 等待元素出现
await page.waitForSelector('.result', { state: 'visible' });
await page.waitForSelector('.result', { state: 'attached' });
await page.waitForSelector('.result', { state: 'hidden' });

// 等待元素数量
await page.waitForSelector('li', { count: 10 });
```

---

#### 3.3 waitForResponse() - 等待 API 响应

```javascript
// 等待特定 API
await page.waitForResponse('**/api/data');
await page.waitForResponse(/api\/users.*/);

// 验证响应
await page.waitForResponse('**/api/data', async response => {
  const data = await response.json();
  expect(data).toHaveLength(10);
});
```

---

#### 3.4 waitForFunction() - 等待条件满足

```javascript
// 等待条件为 true
await page.waitForFunction(() => {
  return document.querySelector('.result') !== null;
});

// 等待并返回元素
const element = await page.waitForFunction(() => {
  return document.querySelector('.result');
});
```

---

## 定位策略优先级

**严格遵循以下优先级**：

1. **getByRole** - 最稳定（语义化）
2. **getByLabel** - 表单元素
3. **getByPlaceholder** - 输入框
4. **getByText** + `.first()` - 文本内容
5. **getByTestId** - 测试专用属性
6. **id 属性** - 原生 HTML 优先
7. **组件库 class** - Element UI/Ant Design
8. **locator + 属性** - CSS 选择器
9. **locator + CSS 类** - 最后选择
10. ❌ **ref 属性** - 禁止使用（MCP 快照特有）

---

## 常用操作

### 导航

```javascript
await page.goto(url);
await page.goBack();
await page.goForward();
await page.reload();
```

### 点击

```javascript
await page.getByRole('button', { name: '提交' }).click();
await page.locator('#submit').click();
await page.click('text=取消');
```

### 输入

```javascript
await page.getByPlaceholder('用户名').fill('testuser');
await page.locator('input[name="email"]').clear();
await page.locator('input[name="email"]').type('test@example.com');
```

### 选择下拉选项

```javascript
await page.getByRole('combobox').selectOption('选项1');
await page.locator('select').selectOption('value1');
```

### 悬停

```javascript
await page.getByRole('button', { name: '提交' }).hover();
await page.locator('.item').hover();
```

### 上传文件

```javascript
await page.locator('input[type="file"]').setFiles('path/to/file.pdf');
```

---

## 调试技巧

### 截图

```javascript
// 整页截图
await page.screenshot({ path: 'screenshot.png' });

// 元素截图
await page.locator('.result').screenshot({ path: 'element.png' });
```

### 查看日志

```javascript
// 监听控制台日志
page.on('console', msg => console.log(msg.text()));

// 监听请求
page.on('request', request => console.log(request.url()));
```

---

## 完整示例

```javascript
const { test, expect } = require('@playwright/test');

test.describe('登录功能测试', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
  });

  test('成功登录', async ({ page }) => {
    // 使用 getByRole（最稳定）
    await page.getByLabel('用户名').fill('testuser');
    await page.getByPlaceholder('密码', { exact: true }).fill('pass123');
    await page.getByRole('button', { name: '登录' }).click();

    // 断言：URL 变化
    await expect(page).toHaveURL('/dashboard');
  });

  test('输入框验证', async ({ page }) => {
    // 测试文本输入
    await page.getByPlaceholder('请输入姓名').fill('张三');
    await expect(page.getByPlaceholder('请输入姓名')).toHaveValue('张三');

    // 清空输入
    await page.getByPlaceholder('请输入姓名').clear();
    await expect(page.getByPlaceholder('请输入姓名')).toHaveValue('');
  });
});
```
