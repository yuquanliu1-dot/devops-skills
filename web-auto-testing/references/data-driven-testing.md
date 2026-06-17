# 数据驱动测试指南

本文档提供 Playwright 数据驱动测试的完整指南，支持从多种数据源读取测试数据。

## 概述

数据驱动测试（Data-Driven Testing, DDT）是一种测试方法，将测试数据与测试逻辑分离，通过外部数据源驱动测试执行。

### 优势

- ✅ 数据与逻辑分离，易于维护
- ✅ 一套测试代码覆盖多组数据
- ✅ 新增测试用例只需添加数据
- ✅ 适合回归测试和边界测试

---

## 1. JSON 数据驱动测试

### 方案 1: 使用 require() 直接加载

```javascript
const { test, expect } = require('@playwright/test');

// 加载 JSON 测试数据
const testData = require('./test-data.json');

test.describe('JSON 数据驱动登录测试', () => {
  // 遍历测试数据
  for (const data of testData) {
    test(`登录测试: ${data.description}`, async ({ page }) => {
      await page.goto('/login');

      await page.getByLabel('用户名').fill(data.username);
      await page.getByLabel('密码').fill(data.password);
      await page.getByRole('button', { name: '登录' }).click();

      // 验证预期结果
      if (data.shouldSucceed) {
        await expect(page).toHaveURL('/dashboard');
      } else {
        await expect(page.getByText('登录失败')).toBeVisible();
      }
    });
  }
});
```

**test-data.json**:
```json
[
  {
    "description": "正常登录",
    "username": "testuser",
    "password": "password123",
    "shouldSucceed": true
  },
  {
    "description": "密码错误",
    "username": "testuser",
    "password": "wrongpassword",
    "shouldSucceed": false
  },
  {
    "description": "用户不存在",
    "username": "nonexistent",
    "password": "password123",
    "shouldSucceed": false
  }
]
```

---

### 方案 2: 使用 test.each() (推荐)

```javascript
const { test, expect } = require('@playwright/test');

test.describe('test.each() 数据驱动测试', () => {
  test.each([
    ['testuser', 'password123', true, '正常登录'],
    ['testuser', 'wrongpass', false, '密码错误'],
    ['', 'password123', false, '用户名为空'],
  ])('登录测试: %s - %s', async ({ page }, username, password, shouldSucceed, description) => {
    await page.goto('/login');

    await page.getByLabel('用户名').fill(username);
    await page.getByLabel('密码').fill(password);
    await page.getByRole('button', { name: '登录' }).click();

    if (shouldSucceed) {
      await expect(page).toHaveURL('/dashboard');
    } else {
      await expect(page.getByText('登录失败')).toBeVisible();
    }
  });
});
```

**使用对象数组**（更清晰）:
```javascript
test.each([
  { username: 'user1', password: 'pass1', shouldSucceed: true, desc: '正常登录' },
  { username: 'user1', password: 'wrong', shouldSucceed: false, desc: '密码错误' },
  { username: '', password: 'pass1', shouldSucceed: false, desc: '用户名为空' },
])('$desc', async ({ page }, data) => {
  await page.goto('/login');
  await page.getByLabel('用户名').fill(data.username);
  await page.getByLabel('密码').fill(data.password);
  await page.getByRole('button', { name: '登录' }).click();

  if (data.shouldSucceed) {
    await expect(page).toHaveURL('/dashboard');
  } else {
    await expect(page.getByText('登录失败')).toBeVisible();
  }
});
```

---

## 2. CSV 数据驱动测试

### 安装依赖

```bash
npm install csv-parse
```

### 方案 1: 使用 csv-parse/sync

```javascript
const { test, expect } = require('@playwright/test');
const { parse } = require('csv-parse/sync');
const { readFileSync } = require('fs');

// 读取并解析 CSV
const csvContent = readFileSync('./test-data.csv', 'utf-8');
const testData = parse(csvContent, {
  columns: true,
  skip_empty_lines: true,
});

test.describe('CSV 数据驱动测试', () => {
  for (const data of testData) {
    test(`搜索测试: ${data.searchTerm}`, async ({ page }) => {
      await page.goto('/search');

      await page.getByPlaceholder('请输入搜索内容').fill(data.searchTerm);
      await page.getByRole('button', { name: '搜索' }).click();

      // 验证结果数量
      await expect(page.locator('.result-item')).toHaveCount(parseInt(data.expectedCount));
    });
  }
});
```

**test-data.csv**:
```csv
searchTerm,expectedCount
playwright,10
selenium,8
cypress,5
```

---

### 方案 2: 使用 csv-parser (流式处理大文件)

```bash
npm install csv-parser
```

```javascript
const fs = require('fs');
const csvParser = require('csv-parser');

const results = [];

// 同步读取 CSV
function readCSV(filePath) {
  return new Promise((resolve, reject) => {
    const results = [];
    fs.createReadStream(filePath)
      .pipe(csvParser())
      .on('data', (data) => results.push(data))
      .on('end', () => resolve(results))
      .on('error', reject);
  });
}

test.describe('CSV 流式读取测试', async () => {
  const testData = await readCSV('./test-data.csv');

  for (const data of testData) {
    test(`CSV 测试: ${data.searchTerm}`, async ({ page }) => {
      // 测试逻辑...
    });
  }
});
```

---

## 3. Excel 数据驱动测试

### 安装依赖

```bash
npm install xlsx
```

### 方案 1: 读取整个工作簿

```javascript
const { test, expect } = require('@playwright/test');
const xlsx = require('xlsx');

// 读取 Excel 文件
const workbook = xlsx.readFile('./test-data.xlsx');
const sheetName = workbook.SheetNames[0];
const testData = xlsx.utils.sheet_to_json(workbook.Sheets[sheetName]);

test.describe('Excel 数据驱动测试', () => {
  for (const data of testData) {
    test(`Excel 测试: ${data.TestCase}`, async ({ page }) => {
      await page.goto('/login');

      await page.getByLabel('用户名').fill(data.Username);
      await page.getByLabel('密码').fill(data.Password);
      await page.getByRole('button', { name: '登录' }).click();

      if (data.ExpectedResult === 'Success') {
        await expect(page).toHaveURL('/dashboard');
      } else {
        await expect(page.getByText('登录失败')).toBeVisible();
      }
    });
  }
});
```

**test-data.xlsx**:
| TestCase | Username | Password | ExpectedResult |
|----------|----------|----------|----------------|
| 正常登录 | user1 | pass123 | Success |
| 密码错误 | user1 | wrong | Failure |
| 空用户名 | | pass123 | Failure |

---

### 方案 2: 读取特定工作表

```javascript
const xlsx = require('xlsx');

const workbook = xlsx.readFile('./test-data.xlsx');
const sheetData = xlsx.utils.sheet_to_json(workbook.Sheets['LoginTests']);

test.describe('特定工作表测试', () => {
  sheetData.forEach((data) => {
    test(data.TestCase, async ({ page }) => {
      // 测试逻辑...
    });
  });
});
```

---

### 方案 3: 使用缓冲区（适用于 CI/CD）

```javascript
const { test, expect } = require('@playwright/test');
const xlsx = require('xlsx');
const { readFileSync } = require('fs');

// 读取 Excel 为缓冲区
const buffer = readFileSync('./test-data.xlsx');
const workbook = xlsx.read(buffer, { type: 'buffer' });
const testData = xlsx.utils.sheet_to_json(workbook.Sheets[workbook.SheetNames[0]]);

test.describe('缓冲区读取测试', () => {
  testData.forEach((data) => {
    test(data.TestCase, async ({ page }) => {
      // 测试逻辑...
    });
  });
});
```

---

## 4. YAML 数据驱动测试

### 安装依赖

```bash
npm install js-yaml
```

### 读取 YAML 数据

```javascript
const { test, expect } = require('@playwright/test');
const yaml = require('js-yaml');
const { readFileSync } = require('fs');

// 读取并解析 YAML
const yamlContent = readFileSync('./test-data.yaml', 'utf-8');
const testData = yaml.load(yamlContent);

test.describe('YAML 数据驱动测试', () => {
  testData.loginTests.forEach((data) => {
    test(`YAML 测试: ${data.description}`, async ({ page }) => {
      await page.goto('/login');

      await page.getByLabel('用户名').fill(data.username);
      await page.getByLabel('密码').fill(data.password);
      await page.getByRole('button', { name: '登录' }).click();

      if (data.shouldSucceed) {
        await expect(page).toHaveURL('/dashboard');
      } else {
        await expect(page.getByText('登录失败')).toBeVisible();
      }
    });
  });
});
```

**test-data.yaml**:
```yaml
loginTests:
  - description: 正常登录
    username: testuser
    password: password123
    shouldSucceed: true

  - description: 密码错误
    username: testuser
    password: wrongpassword
    shouldSucceed: false

  - description: 用户名为空
    username: ""
    password: password123
    shouldSucceed: false
```

---

## 5. 数据驱动测试最佳实践

### 5.1 数据文件组织

```
project/
├── tests/
│   ├── login.spec.js
│   └── search.spec.js
└── test-data/
    ├── login/
    │   ├── valid.json
    │   ├── invalid.json
    │   └── edge-cases.json
    ├── search/
    │   └── search-terms.csv
    └── config/
        └── test-config.yaml
```

### 5.2 环境特定数据

```javascript
// 根据环境加载数据
const env = process.env.TEST_ENV || 'dev';
const testData = require(`./test-data/${env}/login-data.json`);

test.describe('环境特定测试', () => {
  testData.forEach((data) => {
    test(data.description, async ({ page }) => {
      // 测试逻辑...
    });
  });
});
```

### 5.3 数据验证

```javascript
// 验证数据格式
function validateTestData(data) {
  if (!data.username || !data.password) {
    throw new Error(`无效的测试数据: ${JSON.stringify(data)}`);
  }
}

test.describe('带验证的数据驱动测试', () => {
  testData.forEach((data) => {
    test(data.description, async ({ page }) => {
      validateTestData(data);

      // 测试逻辑...
    });
  });
});
```

### 5.4 动态生成测试

```javascript
// 动态生成测试用例
test.describe('动态测试生成', () => {
  const testData = [
    { input: 1, expected: 2 },
    { input: 2, expected: 4 },
    { input: 3, expected: 6 },
  ];

  for (const data of testData) {
    test(`计算 ${data.input} * 2 = ${data.expected}`, async ({ page }) => {
      await page.goto('/calculator');
      await page.getByLabel('输入').fill(data.input.toString());
      await page.getByRole('button', { name: '计算' }).click();
      await expect(page.getByTestId('result')).toHaveText(data.expected.toString());
    });
  }
});
```

---

## 6. 数据驱动测试进阶场景

### 6.1 组合数据驱动

```javascript
// 从多个来源组合数据
const users = require('./data/users.json');
const products = require('./data/products.json');

test.describe('组合数据测试', () => {
  for (const user of users) {
    test.describe(`用户: ${user.name}`, () => {
      for (const product of products) {
        test(`购买产品: ${product.name}`, async ({ page }) => {
          // 使用用户和产品数据
          await login(page, user);
          await purchase(page, product);
        });
      }
    });
  }
});
```

### 6.2 测试数据工厂

```javascript
// 数据工厂模式
class TestDataFactory {
  static createUser(overrides = {}) {
    return {
      username: 'testuser',
      password: 'password123',
      email: 'test@example.com',
      ...overrides,
    };
  }

  static createProduct(overrides = {}) {
    return {
      name: 'Test Product',
      price: 99.99,
      quantity: 1,
      ...overrides,
    };
  }
}

test.describe('数据工厂测试', () => {
  test('创建用户测试', async ({ page }) => {
    const user = TestDataFactory.createUser({ username: 'customuser' });
    // 使用用户数据...
  });
});
```

### 6.3 参数化测试配置

```javascript
// 参数化测试配置
const testConfigs = [
  { browser: 'chromium', viewport: { width: 1920, height: 1080 } },
  { browser: 'firefox', viewport: { width: 1366, height: 768 } },
  { browser: 'webkit', viewport: { width: 375, height: 667 } },
];

for (const config of testConfigs) {
  test.describe(`${config.browser} 测试`, () => {
    test.use({ viewport: config.viewport });

    test('响应式测试', async ({ page }) => {
      await page.goto('/');
      await expect(page.locator('h1')).toBeVisible();
    });
  });
}
```

---

## 7. 完整示例：电商登录数据驱动测试

### 测试脚本

```javascript
const { test, expect } = require('@playwright/test');
const xlsx = require('xlsx');

// 读取 Excel 测试数据
const workbook = xlsx.readFile('./test-data/login-tests.xlsx');
const testData = xlsx.utils.sheet_to_json(workbook.Sheets['Sheet1']);

test.describe('电商登录 - 数据驱动测试', () => {
  test.beforeEach(async ({ page }) => {
    await page.goto('/login');
  });

  for (const data of testData) {
    test(`登录测试: ${data.TestCase}`, async ({ page }) => {
      // 输入用户名和密码
      await page.getByLabel('用户名').fill(data.Username);
      await page.getByLabel('密码').fill(data.Password);

      // 点击登录按钮
      await page.getByRole('button', { name: '登录' }).click();

      // 验证预期结果
      if (data.ExpectedResult === 'Success') {
        await expect(page).toHaveURL('/dashboard');
        await expect(page.getByRole('heading', { name: '欢迎' })).toBeVisible();
      } else {
        await expect(page.getByText('登录失败')).toBeVisible();
        await expect(page.getByText(data.ErrorMessage || '用户名或密码错误')).toBeVisible();
      }
    });
  }
});
```

### Excel 数据文件

**login-tests.xlsx**:

| TestCase | Username | Password | ExpectedResult | ErrorMessage |
|----------|----------|----------|----------------|--------------|
| 正常登录 | user1 | pass123 | Success | |
| 密码错误 | user1 | wrongpass | Failure | 密码错误 |
| 用户名为空 | | pass123 | Failure | 用户名不能为空 |
| 密码为空 | user1 | | Failure | 密码不能为空 |
| 用户不存在 | nonexistent | pass123 | Failure | 用户不存在 |

---

## 总结

### 数据驱动测试选择指南

| 数据源 | 适用场景 | 优势 | 劣势 |
|--------|----------|------|------|
| **JSON** | 简单数据、小规模 | 原生支持、易于编辑 | 大文件不便维护 |
| **CSV** | 表格数据、大规模 | 易于编辑、Excel 兼容 | 不支持复杂数据结构 |
| **Excel** | 业务数据、非技术人员 | 直观、支持公式 | 需要额外库 |
| **YAML** | 配置数据、层次结构 | 可读性强、支持注释 | 解析稍慢 |

### 关键要点

1. ✅ **数据与逻辑分离** - 数据文件独立于测试代码
2. ✅ **验证数据格式** - 确保数据完整性
3. ✅ **使用 test.each()** - Playwright 原生支持，推荐使用
4. ✅ **环境特定数据** - 不同环境使用不同数据文件
5. ✅ **错误处理** - 数据异常时提供清晰的错误信息
