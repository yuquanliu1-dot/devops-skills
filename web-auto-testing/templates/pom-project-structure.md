# 页面对象模式（POM）项目结构

## 目录结构

使用页面对象模式的标准测试项目结构：

```
web-auto-testing-project/
├── tests/                      # 测试文件目录
│   ├── e2e/                   # E2E 测试
│   │   ├── auth/              # 认证相关测试
│   │   │   ├── login.spec.js
│   │   │   └── logout.spec.js
│   │   ├── user/              # 用户相关测试
│   │   │   ├── profile.spec.js
│   │   │   └── settings.spec.js
│   │   └── dashboard/         # 仪表盘测试
│   │       └── overview.spec.js
│   └── fixtures/              # 测试数据和辅助函数
│       ├── test-data.js       # 测试数据
│       └── auth-helper.js     # 认证辅助函数
│
├── pages/                      # 页面对象目录 ⭐
│   ├── BasePage.js            # 基类（所有页面继承）
│   ├── LoginPage.js           # 登录页
│   ├── DashboardPage.js       # 仪表盘页
│   ├── ProfilePage.js         # 个人资料页
│   └── SettingsPage.js        # 设置页
│
├── test-data/                  # 测试数据目录
│   ├── users.json             # 用户数据
│   └── config.json            # 配置数据
│
├── artifacts/                  # 测试产物目录
│   ├── screenshots/           # 截图
│   ├── videos/                # 视频
│   └── traces/                # 追踪文件
│
├── utils/                      # 工具函数目录
│   ├── api-client.js          # API 客户端
│   └── data-generator.js      # 数据生成器
│
├── playwright.config.js        # Playwright 配置
├── package.json                # 项目依赖
└── README.md                   # 项目说明
```

---

## 页面对象类模板

### 1. BasePage.js - 基类

所有页面对象的基类，提供通用方法：

```javascript
class BasePage {
  constructor(page) {
    this.page = page;
  }

  async goto(path) {
    await this.page.goto(path);
    await this.page.waitForLoadState('networkidle');
  }

  async getTitle() {
    return await this.page.title();
  }

  async click(locator) {
    await locator.click();
  }

  async fill(locator, value) {
    await locator.fill(value);
  }

  // ... 更多通用方法
}
```

### 2. 具体页面类 - 示例

```javascript
// pages/LoginPage.js
const { BasePage } = require('./BasePage');

class LoginPage extends BasePage {
  constructor(page) {
    super(page);

    // 定义页面元素
    this.usernameInput = page.locator('[data-testid="username"]');
    this.passwordInput = page.locator('[data-testid="password"]');
    this.loginButton = page.getByRole('button', { name: '登录' });
  }

  // 封装页面操作
  async login(username, password) {
    await this.usernameInput.fill(username);
    await this.passwordInput.fill(password);
    await this.loginButton.click();
  }

  async verifyLoginSuccess() {
    await this.page.waitForURL('/dashboard');
  }
}
```

---

## 测试中使用页面对象

### 示例 1：简单测试

```javascript
// tests/e2e/auth/login.spec.js
const { test, expect } = require('@playwright/test');
const { LoginPage } = require('../../pages/LoginPage');
const { DashboardPage } = require('../../pages/DashboardPage');

test.describe('用户登录', () => {
  test('成功登录', async ({ page }) => {
    // 创建页面对象
    const loginPage = new LoginPage(page);
    const dashboardPage = new DashboardPage(page);

    // 执行登录
    await loginPage.goto();
    await loginPage.login('testuser', 'password123');
    await loginPage.verifyLoginSuccess();

    // 验证跳转到仪表盘
    await expect(page).toHaveURL(/\/dashboard/);
  });
});
```

### 示例 2：带测试数据的测试

```javascript
// tests/fixtures/test-data.js
const users = require('../../test-data/users.json');

test('使用不同用户登录', async ({ page }) => {
  const loginPage = new LoginPage(page);

  for (const user of users.validUsers) {
    await loginPage.goto();
    await loginPage.login(user.username, user.password);
    await loginPage.verifyLoginSuccess();

    // 登出后继续下一个用户
    await page.goto('/logout');
  }
});
```

---

## 页面对象最佳实践

### ✅ 应该做的

1. **封装页面操作**：将页面操作封装成方法
   ```javascript
   // ✅ 好的做法
   await loginPage.login('user', 'pass');

   // ❌ 不好的做法
   await page.fill('#username', 'user');
   await page.fill('#password', 'pass');
   await page.click('#login');
   ```

2. **返回页面对象**：方法可以返回其他页面对象，支持流式操作
   ```javascript
   async clickProfile() {
     await this.profileButton.click();
     return new ProfilePage(this.page);
   }

   // 使用
   const profilePage = await dashboardPage.clickProfile();
   ```

3. **使用语义化选择器**：优先使用 getByRole、getByLabel
   ```javascript
   this.loginButton = page.getByRole('button', { name: '登录' });
   this.usernameInput = page.getByLabel('用户名');
   ```

4. **元素定义与操作分离**：在构造函数中定义元素，方法中操作
   ```javascript
   constructor(page) {
     this.submitButton = page.getByRole('button', { name: '提交' });
   }

   async submit() {
     await this.submitButton.click();
   }
   ```

### ❌ 不应该做的

1. **不要在页面对象中添加断言**：断言应该在测试中
   ```javascript
   // ❌ 不好的做法
   async submit() {
     await this.submitButton.click();
     await expect(this.page).toHaveURL('/success');
   }

   // ✅ 好的做法
   async submit() {
     await this.submitButton.click();
   }
   // 在测试中添加断言
   await page.submit();
   await expect(page).toHaveURL('/success');
   ```

2. **不要暴露 page 对象**：避免直接操作 page 对象
   ```javascript
   // ❌ 不好的做法
   const page = loginPage.page;
   await page.click('#button');

   // ✅ 好的做法
   await loginPage.clickButton();
   ```

3. **不要在页面对象中处理测试数据**：测试数据应该在测试文件中

---

## 常见页面类型

### 1. 表单页面（FormPage）
- 输入验证
- 表单提交
- 错误消息处理

### 2. 列表页面（ListPage）
- 搜索和筛选
- 排序
- 分页
- 批量操作

### 3. 详情页面（DetailPage）
- 信息展示
- 编辑和删除
- 相关内容

### 4. 模态框/弹窗（ModalPage）
- 打开/关闭
- 确认/取消
- 内容验证

---

## 完整示例

### 页面类

```javascript
// pages/LoginPage.js
const { BasePage } = require('./BasePage');

class LoginPage extends BasePage {
  constructor(page) {
    super(page);
    this.usernameInput = page.locator('[data-testid="username"]');
    this.passwordInput = page.locator('[data-testid="password"]');
    this.loginButton = page.getByRole('button', { name: '登录' });
    this.errorMessage = page.locator('[data-testid="error-message"]');
  }

  async goto() {
    await super.goto('/login');
  }

  async login(username, password) {
    await this.usernameInput.fill(username);
    await this.passwordInput.fill(password);
    await this.loginButton.click();
  }

  async getErrorMessage() {
    return await this.errorMessage.textContent();
  }
}

module.exports = { LoginPage };
```

### 测试文件

```javascript
// tests/e2e/auth/login.spec.js
const { test, expect } = require('@playwright/test');
const { LoginPage } = require('../../pages/LoginPage');

test.describe('登录功能', () => {
  let loginPage;

  test.beforeEach(async ({ page }) => {
    loginPage = new LoginPage(page);
    await loginPage.goto();
  });

  test('有效凭证应成功登录', async ({ page }) => {
    await loginPage.login('testuser', 'password123');
    await expect(page).toHaveURL(/\/dashboard/);
  });

  test('无效凭证应显示错误消息', async ({ page }) => {
    await loginPage.login('invalid', 'wrongpassword');
    const error = await loginPage.getErrorMessage();
    expect(error).toContain('用户名或密码错误');
  });
});
```

---

## 总结

使用页面对象模式的优势：

1. ✅ **可维护性高**：页面元素集中管理，修改方便
2. ✅ **代码复用**：页面操作可在多个测试中复用
3. ✅ **易于阅读**：测试代码更接近业务语言
4. ✅ **降低耦合**：测试代码与页面实现解耦

参考模板文件：
- [page-object.template.js](../page-object.template.js) - 基类模板
- [pages/login.page.template.js](../pages/login.page.template.js) - 登录页模板
- [pages/list.page.template.js](../pages/list.page.template.js) - 列表页模板
- [pages/detail.page.template.js](../pages/detail.page.template.js) - 详情页模板
