# 常见问题排查

本文档包含 Web 自动化测试中常见问题的排查方法。

---

## Q1：生成的测试脚本无法运行？

**检查步骤**：

1. **确认依赖安装**
   ```bash
   npm install -D @playwright/test
   ```

2. **检查配置文件路径**
   - 确保 `playwright.config.js` 在项目根目录
   - 或在运行时指定配置文件路径

3. **验证系统 Chrome 浏览器**
   - Windows 通常已预装 Chrome
   - 配置文件中已设置 `channel: 'chrome'`
   - 无需下载额外的浏览器文件

4. **检查 Node.js 版本**
   ```bash
   node --version  # 需要 Node.js 16+
   ```

---

## Q2：Playwright 浏览器下载失败/网络超时？

**原因**：无法访问 Google 服务器下载浏览器（170+ MB）

**解决方案**：使用系统 Chrome（推荐，已默认配置）

```javascript
// playwright.config.js 中已配置
use: {
  channel: 'chrome',  // 使用系统 Chrome，无需下载
}
```

**无需运行**：`npx playwright install` （除非需要 Firefox/Safari）

---

## Q3：选择器找不到元素？

**常见原因**：

| 原因 | 解决方案 |
|------|----------|
| 使用了 ref 属性 | 使用语义化选择器（getByRole） |
| 选择器过于宽泛 | 添加更具体的属性 |
| 动态内容未加载 | 添加 `waitForLoadState('networkidle')` |
| 在 iframe 中 | 使用 `frameLocator()` 而非 `locator()` |

**解决方案**：
```javascript
// ❌ 错误：使用 ref 属性
await page.locator('[ref="e7"]').click();

// ✅ 正确：使用语义化选择器
await page.getByRole('button', { name: '提交' }).click();

// ✅ 动态内容：等待加载
await page.waitForLoadState('domcontentloaded');
await expect(page.getByText('加载完成').first()).toBeVisible();
```

---

## Q4：测试运行很慢？

**优化方法**：

1. **启用并行执行**
   ```javascript
   // playwright.config.js
   use: {
     fullyParallel: true,
   }
   ```

2. **减少产物配置**
   ```javascript
   use: {
     video: 'retain-on-failure',  // 仅失败时录制
     trace: 'retain-on-failure',  // 仅失败时追踪
   }
   ```

3. **避免固定延迟**
   ```javascript
   // ❌ 错误
   await page.waitForTimeout(5000);

   // ✅ 正确
   await page.waitForResponse('**/api/data');
   ```

4. **使用项目级并行**
   ```bash
   npx playwright test --workers=4
   ```

---

## Q5：选择器不稳定怎么办？

**诊断**：使用选择器验证脚本
```bash
python scripts/verify_selectors.py test.spec.js
```

**常见问题和解决方案**：

| 问题 | 解决方案 |
|------|----------|
| CSS 类名变化 | 使用 getByRole 或 data-testid |
| 动态生成的 ID | 使用稳定的属性（name, role） |
| 文本内容重复 | 添加 `.first()` 或使用更具体的文本 |
| 等待元素出现 | 添加 `waitForLoadState` 或 `toBeVisible` |

**最佳实践**：
```javascript
// 优先级 1：getByRole（最稳定）
await page.getByRole('button', { name: '提交' }).click();

// 优先级 2：getByLabel（表单元素）
await page.getByLabel('用户名').fill('test');

// 优先级 3：getByTestId（测试专用）
await page.getByTestId('submit-btn').click();

// 优先级 4：locator + 属性
await page.locator('button[name="submit"]').click();
```

---

## Q6：测试偶发失败？

**常见原因**：

1. **网络延迟**
   ```javascript
   // 等待 API 响应
   await page.waitForResponse('**/api/data');
   ```

2. **动画未完成**
   ```javascript
   // 等待动画结束
   await page.waitForLoadState('domcontentloaded');
   ```

3. **并发冲突**
   ```javascript
   // 使用独立数据
   const timestamp = Date.now();
   await page.getByLabel('用户名').fill(`test_${timestamp}`);
   ```

4. **元素被遮挡**
   ```javascript
   // 滚动到元素
   await page.getByRole('button', { name: '提交' }).scrollIntoViewIfNeeded();
   ```

---

## Q7：iframe 内操作失败？

**问题**：FrameLocator 不支持页面级方法

**解决方案**：
```javascript
// ❌ 错误：FrameLocator 不能用 waitForLoadState
const iframe = page.frameLocator('#content-frame');
await iframe.waitForLoadState('networkidle');  // 报错

// ✅ 正确：使用 Frame 对象
const frame = page.frame('#content-frame');
await frame.waitForLoadState('networkidle');

// ✅ 正确：FrameLocator 用于定位元素
const iframe = page.frameLocator('#content-frame');
await iframe.getByRole('button', { name: '提交' }).click();
```

---

## Q8：认证/登录处理失败？

**解决方案**：使用认证辅助脚本
```bash
python scripts/generate_test_with_auth.py --interactive
```

**或手动保存认证状态**：
```javascript
// 1. 登录后保存状态
await page.context().storageState({ path: 'auth.json' });

// 2. 后续使用保存的状态
const context = await browser.newContext({
  storageStatePath: 'auth.json'
});
```

---

## Q9：图表数据验证失败？

**问题**：Canvas 图表无法直接获取数据

**解决方案**：
```javascript
// 获取 ECharts 图表数据
const chartData = await page.evaluate(() => {
  const chart = document.querySelector('[data-testid="chart"]').__echarts_instance__;
  return chart.getOption();
});

// 验证数据点数量
expect(chartData.series[0].data.length).toBe(12);
```

详见：[数据准确性验证指南](data-verification.md)

---

## Q10：导出功能验证失败？

**问题**：下载文件路径不正确

**解决方案**：
```javascript
// 配置下载目录
const context = await browser.newContext({
  acceptDownloads: true,
  downloadsPath: path.join(__dirname, 'test-downloads')
});

// 等待下载事件
const [download] = await Promise.all([
  page.waitForEvent('download'),
  page.getByRole('button', { name: '导出' }).click()
]);

// 保存文件
await download.saveAs('./test-downloads/file.xlsx');
```

---

## 🔧 调试技巧

### 查看页面状态
```javascript
// 截图
await page.screenshot({ path: 'debug.png' });

// 查看页面 HTML
console.log(await page.content());

// 查看控制台日志
page.on('console', msg => console.log(msg.text()));
```

### 慢动作执行
```javascript
// 慢动作模式（每步延迟 500ms）
const browser = await playwright.chromium.launch({
  slowMo: 500,
  headless: false
});
```

### 暂停执行
```javascript
// 在某处暂停
await page.pause();
```

---

**版本**：1.0.0
**最后更新**：2026-03-28
**维护者**：Claude Code
