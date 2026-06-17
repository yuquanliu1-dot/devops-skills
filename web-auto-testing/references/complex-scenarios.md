# 复杂场景处理指南

本文档提供 Web 自动化测试中常见复杂场景的处理方案。

## 1. 懒加载处理

### 场景描述
页面内容通过滚动或交互动态加载，初始状态元素不存在。

### 解决方案

#### 方案 1: 等待特定元素出现

```javascript
test('懒加载内容测试', async ({ page }) => {
  await page.goto('/lazy-page');

  // 等待懒加载元素出现
  await expect(page.locator('.lazy-loaded-item').first()).toBeVisible({ timeout: 10000 });

  // 验证内容
  await expect(page.locator('.lazy-loaded-item').first()).toContainText('内容');
});
```

#### 方案 2: 等待网络空闲

```javascript
test('AJAX 懒加载', async ({ page }) => {
  await page.goto('/lazy-page');

  // 等待网络请求完成
  await page.waitForLoadState('networkidle');

  // 验证内容加载完成
  await expect(page.locator('.content').toHaveCount(10);
});
```

#### 方案 3: 滚动到元素位置

```javascript
test('滚动加载测试', async ({ page }) => {
  await page.goto('/scroll-page');

  // 滚动到元素位置
  await page.locator('.lazy-container').scrollIntoViewIfNeeded();

  // 等待元素加载
  await expect(page.locator('.lazy-item').first()).toBeVisible();
});
```

#### 方案 4: 等待请求完成

```javascript
test('等待特定请求', async ({ page }) => {
  await page.goto('/data-page');

  // 等待数据请求完成
  await page.waitForResponse('**/api/lazy-data', async response => {
    const data = await response.json();
    expect(data.items).toHaveLength(20);
  });

  // 验证数据渲染
  await expect(page.locator('.data-item').toHaveCount(20);
});
```

---

## 2. AJAX 请求处理

### 场景描述
页面通过 AJAX 异步加载数据，需要等待请求完成。

### 解决方案

#### 方案 1: 等待特定 API 响应

```javascript
test('AJAX 数据加载', async ({ page }) => {
  await page.goto('/data-page');

  // 点击触发 AJAX 的按钮
  await page.getByRole('button', { name: '加载数据' }).click();

  // 等待 API 响应
  await page.waitForResponse('**/api/data', async response => {
    expect(response.status()).toBe(200);
    const data = await response.json();
    expect(data.success).toBe(true);
  });

  // 验证数据渲染
  await expect(page.locator('.data-row').first()).toBeVisible();
});
```

#### 方案 2: 等待网络空闲

```javascript
test('等待 AJAX 完成', async ({ page }) => {
  await page.goto('/ajax-page');

  // 触发 AJAX
  await page.getByRole('button', { name: '查询' }).click();

  // 等待网络请求完成
  await page.waitForLoadState('networkidle');

  // 验证结果
  await expect(page.locator('.result')).toBeVisible();
});
```

#### 方案 3: 等待特定文本出现

```javascript
test('等待加载提示消失', async ({ page }) => {
  await page.goto('/loading-page');

  // 触发加载
  await page.getByRole('button', { name: '刷新' }).click();

  // 等待加载提示消失
  await expect(page.locator('.loading')).toBeHidden({ timeout: 10000 });

  // 等待数据出现
  await expect(page.getByText('数据加载完成')).toBeVisible();
});
```

#### 方案 4: 轮询等待

```javascript
test('轮询等待加载结果', async ({ page }) => {
  await page.goto('/polling-page');

  // 触发轮询
  await page.getByRole('button', { name: '查询' }).click();

  // 轮询等待
  await expect(async () => {
    const text = await page.locator('.status').textContent();
    return text === '完成';
  }).toBeTruthy({ timeout: 10000 });
});
```

---

## 3. 登录认证处理

### 场景描述
测试需要先登录才能访问某些功能。

### 方案 1: 使用 storageState 保存登录状态（推荐）

#### 步骤 1: 创建认证保存脚本

```javascript
// auth.setup.spec.js
import { defineConfig } from '@playwright/test';

const authFile = 'auth.json';

export default defineConfig({
  testDir: './tests',
});

test('登录并保存状态', async ({ page }) => {
  await page.goto('/login');

  // 输入用户名和密码
  await page.getByLabel('用户名').fill('testuser');
  await page.getByLabel('密码', { exact: true }).fill('password123');

  // 点击登录
  await page.getByRole('button', { name: '登录' }).click();

  // 等待跳转到 dashboard
  await page.waitForURL('/dashboard');

  // 保存登录状态
  await page.context().storageState({ path: authFile });
});
```

#### 步骤 2: 使用保存的状态

```javascript
// authenticated.spec.js
import { test, expect } = require('@playwright/test');
import { defineConfig } from '@playwright/test';

const authFile = 'auth.json';

export default defineConfig({
  testDir: './tests',
});

// 使用保存的登录状态
test.use({ storageState: authFile });

test('需要登录的测试', async ({ page }) => {
  // 已经处于登录状态
  await page.goto('/dashboard');

  // 直接测试功能
  await expect(page.getByRole('heading', { name: '仪表板' })).toBeVisible();
});
```

#### 步骤 3: 运行认证保存脚本

```bash
# 运行认证保存脚本
npx playwright test auth.setup.spec.js

# 运行测试
npx playwright test
```

---

### 方案 2: 在 beforeEach 中登录

```javascript
test.describe('需要登录的功能', () => {
  test.beforeEach(async ({ page }) => {
    // 每个测试前登录
    await page.goto('/login');

    await page.getByLabel('用户名').fill('testuser');
    await page.getByLabel('密码', { exact: true }).fill('password123');
    await page.getByRole('button', { name: '登录' }).click();

    // 等待登录成功
    await page.waitForURL('/dashboard');
  });

  test('功能A 测试', async ({ page }) => {
    await page.goto('/feature-a');
    // 测试逻辑...
  });

  test('功能B 测试', async ({ page }) => {
    await page.goto('/feature-b');
    // 测试逻辑...
  });
});
```

---

### 方案 3: 全局设置登录状态

```javascript
import { test, expect } = require('@playwright/test');

// 全局设置登录状态
test.use({ storageState: 'auth.json' });

test.describe('需要登录的功能', () => {
  test('功能A', async ({ page }) => {
    // 测试逻辑...
  });

  test('功能B', async ({ page }) => {
    // 测试逻辑...
  });
});
```

---

### 方案 4: API Token 认证

```javascript
test.describe('API Token 认证', () => {
  let token;

  test.beforeAll(async ({ page }) => {
    // 获取 token
    const response = await page.request.post('/api/auth/login', {
      data: {
        username: 'testuser',
        password: 'password123'
      }
    });
    token = response.json().token;
  });

  test('使用 token 访问接口', async ({ page }) => {
    await page.goto('/dashboard');

    // 设置请求头
    await page.route('**/api/**', async route => {
      const headers = await route.request().headers();
      headers['Authorization'] = `Bearer ${token}`;
      await route.continue();
    });

    // 触发 API 调用
    await page.getByRole('button', { name: '加载数据' }).click();

    // 验证结果
    await expect(page.locator('.result')).toBeVisible();
  });
});
```

---

## 4. iframe 测试

### 场景描述
应用使用 iframe 嵌入内容，需要在 iframe 内操作元素。

### 如何找到 iframe 的 id

**方法1：使用浏览器开发者工具**
1. 打开目标网页
2. 按 **F12** 打开开发者工具
3. 选择 **Elements** 标签
4. 按 **Ctrl+F** 搜索 `<iframe`
5. 查看并复制 iframe 的 **id** 属性

**方法2：使用 Playwright 代码查找**
```javascript
const iframeIds = await page.locator('iframe').evaluateAll(iframe =>
  iframe.id || 'no-id'
);
console.log(iframeIds);  // ['content-frame', 'no-id']
```

**方法3：使用 MCP 工具检查**
```javascript
// MCP 快照中的 ref 属性不对应实际页面
// 需要检查实际的 id 属性
const iframeHtml = await page.locator('iframe').first().evaluate(
  el => el.outerHTML
);
console.log(iframeHtml);  // <iframe id="content-frame" src="...">
```

### 重要：FrameLocator vs Frame

**FrameLocator** - 用于定位 iframe 内的元素
- ✅ 支持：`getByRole()`, `getByLabel()`, `locator()`, `click()`, `fill()`
- ❌ 不支持：`waitForLoadState()`, `waitForResponse()`, `goto()`, `evaluate()`

**Frame** - 用于页面级别的操作
- ✅ 支持：`waitForLoadState()`, `waitForResponse()`, `goto()`, `evaluate()`, `locator()`

### 解决方案

#### 方案 1: 基础 iframe 操作（使用语义化选择器）

```javascript
test('iframe 内元素测试', async ({ page }) => {
  await page.goto('/iframe-page');

  // ✅ 使用 FrameLocator 定位 iframe 内元素
  const iframe = page.frameLocator('#content-frame');

  // ✅ 使用语义化选择器（推荐）
  await expect(iframe.getByRole('heading', { name: '页面标题' })).toBeVisible();
  await iframe.getByRole('button', { name: '提交' }).click();

  // ✅ 表单填写使用 getByLabel
  await iframe.getByLabel('字段名').fill('test');
});
```

#### 方案 2: 等待 iframe 内元素加载

```javascript
test('iframe 内容加载测试', async ({ page }) => {
  await page.goto('/iframe-page');

  const iframe = page.frameLocator('#content-frame');

  // ✅ 等待 iframe 内元素加载（使用语义化选择器）
  await expect(iframe.getByRole('list')).toBeVisible({ timeout: 10000 });

  // ✅ 验证数据行数
  await expect(iframe.getByRole('row')).toHaveCount(10);
});
```

#### 方案 3: iframe 内切换视图

```javascript
test('iframe 视图切换', async ({ page }) => {
  await page.goto('/iframe-page');

  const iframe = page.frameLocator('#content-frame');

  // ✅ 使用语义化选择器切换视图
  await iframe.getByRole('button', { name: '卡片视图' }).click();
  await expect(iframe.getByRole('grid', { name: '卡片' })).toBeVisible();

  // 切换回表格视图
  await iframe.getByRole('button', { name: '表格视图' }).click();
  await expect(iframe.getByRole('table')).toBeVisible();
});
```

#### 方案 4: 等待 iframe 页面状态（需要使用 Frame）

```javascript
test('iframe 页面状态等待', async ({ page }) => {
  await page.goto('/iframe-page');

  // ❌ 错误：FrameLocator 不支持 waitForLoadState
  // const iframe = page.frameLocator('#content-frame');
  // await iframe.waitForLoadState('networkidle');  // TypeError!

  // ✅ 正确：获取 Frame 对象用于等待
  const frame = page.frame('#content-frame');
  await frame.waitForLoadState('networkidle');

  // ✅ 然后使用 FrameLocator 操作元素
  const iframe = page.frameLocator('#content-frame');
  await expect(iframe.getByRole('heading')).toBeVisible();
});
```

#### 方案 5: iframe 内 AJAX 请求（需要使用 Frame）

```javascript
test('iframe 内 AJAX 测试', async ({ page }) => {
  await page.goto('/iframe-page');

  // ❌ 错误：FrameLocator 不支持 waitForResponse
  // const iframe = page.frameLocator('#content-frame');
  // await iframe.waitForResponse(...);  // TypeError!

  // ✅ 正确：使用 Frame 监听响应
  const frame = page.frame('#content-frame');

  // 触发操作
  const frameLocator = page.frameLocator('#content-frame');
  await frameLocator.getByRole('button', { name: '加载' }).click();

  // 等待 iframe 内的 API 响应
  await frame.waitForResponse('**/api/iframe-data');

  // 验证结果
  await expect(frameLocator.getByRole('status')).toHaveText('完成');
});
```

#### 方案 6: 完整的 iframe 操作示例

```javascript
test('iframe 完整操作流程', async ({ page }) => {
  await page.goto('/iframe-page');
  await page.waitForLoadState('networkidle');

  // ✅ 步骤1: 等待 iframe 加载完成（使用 Frame）
  const frame = page.frame('#content-frame');
  await frame.waitForLoadState('domcontentloaded');

  // ✅ 步骤2: 使用 FrameLocator 定位元素
  const iframe = page.frameLocator('#content-frame');

  // ✅ 步骤3: 使用语义化选择器操作
  await expect(iframe.getByRole('heading', { name: '数据列表' })).toBeVisible();

  // ✅ 步骤4: 点击按钮
  await iframe.getByRole('button', { name: '查询' }).click();

  // ✅ 步骤5: 等待结果
  await expect(iframe.getByRole('status')).toHaveText('加载完成', { timeout: 10000 });

  // ✅ 步骤6: 验证数据
  await expect(iframe.getByRole('row')).toHaveCountGreaterThan(0);
});
```

### iframe 常见错误

| 错误代码 | 问题 | 正确做法 |
|---------|------|---------|
| `iframe.waitForLoadState()` | FrameLocator 不支持此方法 | 使用 `frame.waitForLoadState()` |
| `iframe.waitForResponse()` | FrameLocator 不支持此方法 | 使用 `frame.waitForResponse()` |
| `iframe.locator('text=内容')` | 文本选择器不稳定 | 使用 `iframe.getByText('内容').first()` |
| `iframe.locator('.btn')` | CSS 类不稳定 | 使用 `iframe.getByRole('button')` |
| **`iframe.getByRole().toBeVisible()`** | **无头模式可能失败** | **使用 `toBeAttached()`** |

---

## 5. 动态内容处理

### 场景描述
页面内容不固定，会根据用户操作动态变化。

### 解决方案

#### 方案 1: 等待 DOM 更新

```javascript
test('动态内容更新', async ({ page }) => {
  await page.goto('/dynamic-page');

  // 触发内容更新
  await page.getByRole('button', { name: '刷新' }).click();

  // 等待 DOM 更新
  await page.waitForLoadState('domcontentloaded');

  // 验证新内容
  await expect(page.locator('.updated-content')).toBeVisible();
});
```

#### 方案 2: 等待元素数量变化

```javascript
test('列表项动态添加', async ({ page }) => {
  await page.goto('/list-page');

  const initialCount = await page.locator('.list-item').count();

  // 触发添加
  await page.getByRole('button', { name: '添加' }).click();

  // 等待数量增加
  await expect(async () => {
    const newCount = await page.locator('.list-item').count();
    return newCount > initialCount;
  }).toBeTruthy({ timeout: 5000 });
});
```

#### 方案 3: 等待条件函数

```javascript
test('条件满足时操作', async ({ page }) => {
  await page.goto('/conditional-page');

  // 等待特定条件满足
  await expect(async () => {
    const value = await page.locator('#status').textContent();
    return value === 'completed';
  }).toBeTruthy({ timeout: 10000 });

  // 条件满足后操作
  await page.getByRole('button', { name: '下一步' }).click();
});
```

---

## 6. 弹窗和模态框处理

### 场景描述
点击按钮后弹出弹窗或模态框，需要在弹窗内操作。

### 解决方案

#### 方案 1: 等待弹窗出现

```javascript
test('模态框测试', async ({ page }) => {
  await page.goto('/modal-page');

  // 点击打开模态框
  await page.getByRole('button', { name: '打开' }).click();

  // 等待模态框可见
  await expect(page.locator('.modal')).toBeVisible();
  await expect(page.locator('.modal')).toBeEditable();

  // 在模态框内操作
  await page.locator('.modal input').fill('test');
  await page.getByRole('button', { name: '确认' }).click();
});
```

#### 方案 2: 监听弹窗事件

```javascript
test('监听弹窗', async ({ page }) => {
  await page.goto('/popup-page');

  // 监听弹窗事件
  page.on('popup', async popup => {
    await page.waitForTimeout(2000);
    await popup.close();
  });

  // 触发弹窗
  await page.getByRole('button', { name: '打开弹窗' }).click();
});
```

---

## 7. 多窗口/标签页处理

### 场景描述
操作会在新窗口/标签页中打开，需要在窗口间切换。

### 解决方案

#### 方案 1: 处理新窗口

```javascript
test('新窗口操作', async ({ page, context }) => {
  // 监听新窗口
  const [newPage] = await context.waitForEvent('page');

  // 在原页面操作
  await page.getByRole('button', { name: '打开新窗口' }).click();

  // 在新窗口中操作
  await newPage.getByRole('link', { name: '详情' }).click();

  // 切换回原窗口
  await page.bringToFront();
});
```

#### 方案 2: 处理多个窗口

```javascript
test('多窗口测试', async ({ context, browser }) => {
  // 创建多个页面
  const page1 = await context.newPage();
  const page2 = await context.newPage();

  // 在不同页面中操作
  await page1.goto('/page1');
  await page2.goto('/page2');

  // 关闭页面
  await page1.close();
  await page2.close();
});
```

---

## 8. 文件下载测试

### 场景描述
点击下载按钮后需要验证文件下载完成。

### 解决方案

#### 方案 1: 监听下载事件

```javascript
test('文件下载测试', async ({ page, download }) => {
  await page.goto('/download-page');

  // 监听下载事件
  const downloadPromise = page.waitForEvent('download');

  // 触发下载
  await page.getByRole('button', { name: '下载文件' }).click();

  // 等待下载完成
  const download = await downloadPromise;

  // 验证下载文件
  expect(download.suggestedFilename()).toBe('report.pdf');
  expect(download.failures()).toHaveLength(0);
});
```

#### 方案 2: 验证文件存在

```javascript
test('验证下载文件', async ({ page }) => {
  await page.goto('/download-page');

  // 触发下载
  await page.getByRole('button', { name: '下载' }).click();

  // 等待文件出现在下载列表
  await expect(page.getByText('report.pdf')).toBeVisible();
});
```

---

## 9. 前端数据筛选

### 场景描述

数据已在页面加载时全部获取，筛选由前端 JavaScript 实现（不是 AJAX）。

### 与 AJAX 筛选的区别

| 特征 | AJAX 筛选 | 前端筛选 |
|------|----------|----------|
| 网络请求 | 有 | 无 |
| 等待方式 | `waitForResponse()` | `waitForLoadState()` |
| 数据状态 | 动态加载 | 已在 DOM 中 |
| 典型应用 | 大数据分页 | 中小数据全量加载 |

### 解决方案

#### 方案 1: 等待 DOM 更新

```javascript
test('前端部门筛选测试', async ({ page }) => {
  await page.goto('/employee-directory');

  // 等待初始数据加载
  await expect(page.locator('.employee-row')).toHaveCount(941);

  // 执行筛选（原生 select）
  await page.locator('#departmentSelect').selectOption('财务部');

  // 等待 DOM 更新（不是网络请求）
  await page.waitForLoadState('domcontentloaded');

  // 验证筛选结果
  await expect(page.locator('.employee-row')).toHaveCount(9);
  await expect(page.getByText('找到 9 个员工')).toBeVisible();
});
```

#### 方案 2: iframe 内的前端筛选

```javascript
test('iframe 内前端筛选', async ({ page }) => {
  await page.goto('/directory');

  const iframe = page.frameLocator('#content-frame');

  // 执行筛选
  await iframe.locator('#departmentSelect').selectOption('研发部');
  await page.waitForTimeout(300);  // 等待前端渲染

  // 验证结果
  await expect(iframe.getByText(/找到 \d+ 个员工/)).toBeVisible();
});
```

#### 方案 3: 搜索框筛选

```javascript
test('前端搜索筛选', async ({ page }) => {
  const iframe = page.frameLocator('#content-frame');

  // 输入搜索关键词
  await iframe.getByLabel('输入姓名或手机号查询').fill('张三');
  await iframe.getByRole('button', { name: '搜索' }).click();

  // 等待前端筛选完成
  await page.waitForLoadState('domcontentloaded');

  // 验证结果
  await expect(iframe.getByText(/找到 \d+ 个员工/)).toBeVisible();

  // 测试无结果情况
  await iframe.getByLabel('输入姓名或手机号查询').fill('不存在的人名');
  await iframe.getByRole('button', { name: '搜索' }).click();
  await expect(iframe.getByText('没有找到匹配的员工')).toBeVisible();
});
```

---

## 10. 分页测试

### 场景描述

数据量较大时，应用使用分页显示。需要验证分页功能正常工作。

### 解决方案

#### 方案 1: 基础分页测试

```javascript
test('分页功能测试', async ({ page }) => {
  await page.goto('/employee-directory');

  // 验证初始状态
  await expect(page.getByText('第 1 页，共 95 页')).toBeVisible();
  await expect(page.getByRole('button', { name: '上一页' })).toBeDisabled();

  // 点击下一页
  await page.getByRole('button', { name: '下一页' }).click();
  await page.waitForTimeout(300);

  // 验证页面变化
  await expect(page.getByText('第 2 页，共 95 页')).toBeVisible();
  await expect(page.getByRole('button', { name: '上一页' })).not.toBeDisabled();
});
```

#### 方案 2: iframe 内的分页测试

```javascript
test('iframe 分页测试', async ({ page }) => {
  await page.goto('/directory');

  const iframe = page.frameLocator('#content-frame');

  // 验证初始状态
  await expect(iframe.getByText('第 1 页，共 95 页')).toBeVisible();

  // 连续点击下一页
  await iframe.getByRole('button', { name: '下一页' }).click();
  await page.waitForTimeout(300);

  await iframe.getByRole('button', { name: '下一页' }).click();
  await page.waitForTimeout(300);

  // 验证到达第3页
  await expect(iframe.getByText('第 3 页，共 95 页')).toBeVisible();
});
```

#### 方案 3: 分页 + 筛选组合测试

```javascript
test('分页和筛选组合', async ({ page }) => {
  const iframe = page.frameLocator('#content-frame');

  // 先筛选部门
  await iframe.locator('#departmentSelect').selectOption('财务部');
  await page.waitForTimeout(300);

  // 验证分页数量变化（95页 → 1页）
  await expect(iframe.getByText('第 1 页，共 1 页')).toBeVisible();
  await expect(iframe.getByRole('button', { name: '下一页' })).toBeDisabled();

  // 重置筛选
  await iframe.getByRole('button', { name: '重置' }).click();
  await page.waitForTimeout(300);

  // 验证恢复原分页
  await expect(iframe.getByText('第 1 页，共 95 页')).toBeVisible();
});
```

#### 方案 4: 最后一页测试

```javascript
test('最后一页测试', async ({ page }) => {
  const iframe = page.frameLocator('#content-frame');

  // 快速跳转到最后一页（如果支持）
  // 或多次点击下一页直到禁用

  let clickCount = 0;
  const maxClicks = 100;  // 防止无限循环

  while (clickCount < maxClicks) {
    const nextButton = iframe.getByRole('button', { name: '下一页' });
    const isDisabled = await nextButton.isDisabled();

    if (isDisabled) break;

    await nextButton.click();
    await page.waitForTimeout(200);
    clickCount++;
  }

  // 验证到达最后一页
  await expect(iframe.getByText('第 95 页，共 95 页')).toBeVisible();
  await expect(iframe.getByRole('button', { name: '下一页' })).toBeDisabled();
});
```

---

## 总结

处理复杂场景的关键：

1. ✅ **明确等待条件** - 使用明确的等待策略
2. ✅ **使用语义化选择器** - getByRole、getByLabel 等
3. ✅ **避免固定延迟** - 用 waitForLoadState 代替 waitForTimeout
4. ✅ **处理异步操作** - 等待 API 响应、网络空闲
5. ✅ **多元素匹配** - 使用 `.first()` 或 `.nth()` 明确指定
6. ✅ **考虑状态管理** - 使用 storageState、beforeEach 等

遵循这些原则，可以显著提高测试的稳定性和可维护性。
