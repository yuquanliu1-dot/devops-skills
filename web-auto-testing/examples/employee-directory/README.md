# 员工通信录示例

完整的 Playwright 自动化测试示例，演示如何测试一个包含 iframe、动态内容、筛选功能的 Web 应用。

## 应用信息

- **测试 URL**: http://localhost:3000 (或通过环境变量 TEST_URL 配置)/index.html
- **应用类型**: 员工通信录管理系统
- **主要功能**: 员工列表展示、部门筛选、姓名搜索、分页显示

## 测试覆盖

| 用例编号 | 用例标题 | 测试内容 |
|---------|---------|---------|
| TC-001 | 页面加载验证 | 验证页面标题、员工总数、部门数量 |
| TC-002 | 部门筛选功能 | 选择部门并验证筛选结果 |
| TC-003 | 姓名模糊搜索 | 输入关键词并验证搜索结果 |
| TC-004 | 重置按钮功能 | 清空筛选条件并重置列表 |
| TC-005 | 员工详情查看 | 查看单个员工的详细信息 |
| TC-006 | 分页功能测试 | 验证分页导航和数据显示 |
| TC-007 | 无结果场景测试 | 搜索不存在的员工 |
| TC-008 | 组合筛选测试 | 同时使用部门和姓名筛选 |
| TC-009 | 表格排序功能 | 验证点击表头排序 |
| TC-010 | 数据导出功能 | 验证导出按钮功能 |
| TC-011 | 页面刷新保持状态 | 刷新后保持筛选条件 |

## 快速开始

### 1. 安装依赖

```bash
npm install
```

### 2. 安装浏览器

```bash
npx playwright install
```

### 3. 运行测试

```bash
# 运行所有测试
npx playwright test

# 运行特定测试
npx playwright test --grep "TC-001"

# 运行有头模式（可视化）
npx playwright test --headed
```

### 4. 查看报告

```bash
npx playwright show-report
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `employee-directory.spec.js` | Playwright 测试脚本 |
| `playwright.config.js` | 测试配置文件 |
| `TEST_PLAN.md` | 测试计划文档 |
| `TEST_CASES.md` | 测试用例详细说明 |

## 测试特点

### 1. iframe 处理

```javascript
// 获取 iframe
const iframe = page.frameLocator('#content-frame');

// iframe 内操作
await expect(iframe.locator('text=员工通信录')).toBeVisible();
```

### 2. 动态内容处理

```javascript
// 等待网络空闲
await page.goto(BASE_URL, { waitUntil: 'networkidle' });

// 等待元素可见
await expect(iframe.locator('text=员工通信录')).toBeVisible({ timeout: 10000 });
```

### 3. 语义化选择器

```javascript
// 使用文本选择器 + .first()
await iframe.locator('text=/共.*人/').first().textContent();

// 使用 CSS 选择器
await iframe.locator('#departmentSelect').selectOption('财务部');

// 使用结构选择器
await iframe.locator('tbody tr:first-child td:nth-child(2)').textContent();
```

## 预期输出

运行测试后会生成以下报告：

- `playwright-report/index.html` - HTML 测试报告
- `test-results.json` - JSON 格式测试结果
- `junit-results.xml` - JUnit 格式测试报告

## 注意事项

1. **测试环境**: 确保测试应用可访问（http://localhost:3000 (或通过环境变量 TEST_URL 配置)）
2. **浏览器版本**: 支持 Chrome、Firefox、Safari
3. **网络依赖**: 需要稳定的网络连接

## 常见问题

### Q: 测试失败怎么办？

A: 检查以下几点：
1. 测试应用是否可访问
2. 浏览器是否正确安装
3. 网络连接是否稳定

### Q: 如何调试测试？

A: 使用以下方法：
1. 运行 `npx playwright test --debug`
2. 使用 `test.only()` 只运行单个测试
3. 使用 `npx playwright test --headed` 查看浏览器操作

### Q: 如何修改测试数据？

A: 编辑 `employee-directory.spec.js` 中的测试数据：
```javascript
// 修改部门名称
await iframe.locator('#departmentSelect').selectOption('新部门');

// 修改搜索关键词
await iframe.locator('input[placeholder*="姓名"]').fill('新关键词');
```
