# 电商登录示例

完整的 Playwright 数据驱动测试示例，演示如何使用多种数据源（JSON/CSV/Excel）进行电商登录测试。

## 应用信息

- **测试 URL**: https://example.com/shop
- **应用类型**: 电商网站登录功能
- **主要功能**: 用户登录、登出、密码验证

## 测试覆盖

| 用例编号 | 用例标题 | 测试内容 |
|---------|---------|---------|
| TC-001 | 正常登录测试 | 验证正确的用户名和密码可以登录 |
| TC-002 | 错误密码测试 | 验证错误密码显示提示 |
| TC-003 | 用户名为空测试 | 验证用户名为空的验证 |
| TC-004 | 密码为空测试 | 验证密码为空的验证 |
| TC-005 | 多用户登录 | 数据驱动测试多个用户 |
| TC-006 | 记住我功能 | 验证记住我复选框 |
| TC-007 | 忘记密码链接 | 验证忘记密码功能 |
| TC-008 | 登出功能测试 | 验证用户登出 |

## 数据驱动测试

### 测试数据源

本示例支持以下数据源：

1. **JSON 数据** - `test-data.json`
2. **CSV 数据** - `test-data.csv`
3. **Excel 数据** - `test-data.xlsx`

### 测试数据示例

**JSON 格式** (`test-data.json`):
```json
[
  {
    "username": "user1",
    "password": "pass123",
    "shouldSucceed": true,
    "description": "正常登录"
  },
  {
    "username": "user1",
    "password": "wrongpass",
    "shouldSucceed": false,
    "description": "密码错误"
  }
]
```

## 快速开始

### 1. 安装依赖

```bash
npm install
npm install -D csv-parse xlsx
```

### 2. 安装浏览器

```bash
npx playwright install
```

### 3. 运行测试

```bash
# 运行所有测试
npx playwright test

# 运行数据驱动测试
npx playwright test --grep "数据驱动"
```

### 4. 查看报告

```bash
npx playwright show-report
```

## 文件说明

| 文件 | 说明 |
|------|------|
| `e-commerce.spec.js` | Playwright 测试脚本 |
| `playwright.config.js` | 测试配置文件 |
| `test-data.json` | JSON 格式测试数据 |
| `TEST_PLAN.md` | 测试计划文档 |
| `TEST_CASES.md` | 测试用例详细说明 |

## 测试特点

### 1. 数据驱动测试

```javascript
// 从 JSON 读取数据
const testData = require('./test-data.json');

// 遍历测试数据
for (const data of testData) {
  test(`登录测试: ${data.description}`, async ({ page }) => {
    await login(page, data.username, data.password);

    if (data.shouldSucceed) {
      await expect(page).toHaveURL('/dashboard');
    } else {
      await expect(page.getByText('登录失败')).toBeVisible();
    }
  });
}
```

### 2. CSV 数据驱动

```javascript
// 从 CSV 读取数据
const { parse } = require('csv-parse/sync');
const csvData = parse(fs.readFileSync('./test-data.csv'), {
  columns: true
});

// 使用 test.each()
test.each(csvData.map(row => [row.username, row.password]))(
  '登录 %s',
  async ({ page }, username, password) => {
    await login(page, username, password);
  }
);
```

### 3. Excel 数据驱动

```javascript
// 从 Excel 读取数据
const xlsx = require('xlsx');
const workbook = xlsx.readFile('./test-data.xlsx');
const sheetData = xlsx.utils.sheet_to_json(workbook.Sheets['Sheet1']);

// 遍历 Excel 数据
sheetData.forEach((data) => {
  test(data.TestCase, async ({ page }) => {
    await login(page, data.Username, data.Password);
  });
});
```

## 预期输出

运行测试后会生成以下报告：

- `playwright-report/index.html` - HTML 测试报告
- `test-results.json` - JSON 格式测试结果
- `junit-results.xml` - JUnit 格式测试报告

## 注意事项

1. **测试环境**: 示例使用虚拟 URL，实际使用时需要替换
2. **数据格式**: 确保 JSON/CSV/Excel 文件格式正确
3. **依赖包**: CSV 和 Excel 支持需要额外安装依赖

## 常见问题

### Q: 如何切换数据源？

A: 修改 `e-commerce.spec.js` 中的数据读取部分：
```javascript
// 使用 JSON
const testData = require('./test-data.json');

// 使用 CSV
const csvData = parse(fs.readFileSync('./test-data.csv'), { columns: true });

// 使用 Excel
const excelData = xlsx.utils.sheet_to_json(workbook.Sheets['Sheet1']);
```

### Q: 如何添加新的测试数据？

A: 编辑对应的数据文件：
- JSON: 在 `test-data.json` 中添加新对象
- CSV: 在 `test-data.csv` 中添加新行
- Excel: 在 `test-data.xlsx` 中添加新行

### Q: 数据驱动测试失败怎么办？

A: 检查以下几点：
1. 数据文件路径是否正确
2. 数据格式是否正确
3. 必要的依赖包是否已安装
