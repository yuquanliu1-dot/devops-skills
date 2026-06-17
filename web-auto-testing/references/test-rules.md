# 测试规则与最佳实践

本文档包含 Web 自动化测试的强制规则和最佳实践。

---

## 🛡️ 强制规则（必须遵守）

### 必须使用

1. **必须使用 @playwright/test 框架**（不是 playwright 的直接 API）
2. **必须生成标准的 test.describe 结构**
3. **必须使用 page.locator() 定位元素**
4. **必须使用 expect() 进行断言**
5. **必须配置多格式报告器**（HTML、JSON、JUnit）
6. **测试脚本必须可独立运行**
7. **必须处理动态内容**（使用 waitForLoadState）
8. **生成测试后必须验证选择器**（使用 `verify_selectors.py`）
9. **MCP 模式失败时必须截图**，保存至 `artifacts/screenshots/{feature}-{case}-failed.png`

---

## ❌ 禁止事项

1. ❌ 禁止生成同步 Playwright API 代码
2. ❌ 禁止使用手写 HTML 报告生成
3. ❌ 禁止省略错误处理
4. ❌ 禁止创建测试间有依赖关系的用例
5. ❌ **禁止使用 ref 属性**（ref="e10" 等）
6. ❌ 禁止使用固定延迟代替明确等待
7. ❌ 禁止生成 CSS 类选择器作为首选
8. ❌ 禁止在组件库应用中盲目使用语义化选择器（可能被拦截）

> 📘 断言规则详见 [Playwright API 参考](playwright-api.md) → 断言规则（强制执行）

---

## 🔍 选择器规则

### 优先级（严格遵循）

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

### 强制规则

**必须**：`getByText()` 和 `locator()` 必须加 `.first()`

```javascript
// ❌ 错误
await page.getByText('登录成功').toBeVisible();

// ✅ 正确
await page.getByText('登录成功').first().toBeVisible();
```

---

## ⚠️ ref 属性陷阱

**警告**：MCP 快照中的 `ref` 属性在实际页面中不存在，禁止使用 `[ref="e7"]`

**正确做法**：使用浏览器开发者工具 (F12) 检查元素，优先使用 id、name、role

---

## 📋 断言规则（强制执行）

### 规则 1：所有 getByText() 断言必须添加 .first()

```javascript
// ❌ 错误
await expect(page.getByText('登录成功')).toBeVisible();

// ✅ 正确
await expect(page.getByText('登录成功').first()).toBeVisible();
```

### 规则 2：所有 locator() 断言必须添加 .first() 或更具体的选择器

```javascript
// ❌ 错误
await expect(page.locator('table')).toBeVisible();

// ✅ 正确
await expect(page.locator('table').first()).toBeVisible();
await expect(page.getByRole('table')).toBeVisible();  // 更好的方式
```

### 规则 3：常量定义时也要添加 .first()

```javascript
// ❌ 错误
const countElement = frame.getByText('100');

// ✅ 正确
const countElement = frame.getByText('100').first();
await expect(countElement).toBeVisible();
```

---

## 🔧 等待策略

### 优先级（推荐 → 不推荐）

1. ✅ 等待 DOM 加载: `await page.waitForLoadState('domcontentloaded');`
2. ✅ 等待元素附加: `await expect(locator).toBeAttached();`
3. ✅ 等待元素可见: `await expect(locator).toBeVisible();`
4. ✅ 等待 API: `await page.waitForResponse('**/api/data');`
5. ✅ 等待 URL: `await page.waitForURL('/dashboard');`

⚠️ 不推荐使用 `networkidle`（现代 Web 应用常有长连接）

❌ 避免使用固定延迟: `await page.waitForTimeout(5000);`

---

## 📖 业界最佳实践参考

- Playwright 官方文档：https://playwright.dev/docs/actionability
- Microsoft：推荐 domcontentloaded + 元素等待
- Google/Meta：推荐显式等待 + 断言

---

**版本**：1.0.0
**最后更新**：2026-03-28
**维护者**：Claude Code
