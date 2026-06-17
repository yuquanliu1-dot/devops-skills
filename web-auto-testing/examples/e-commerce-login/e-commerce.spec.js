/**
 * 电商登录模块自动化测试
 * 测试地址: https://example.com/shop
 *
 * 数据驱动测试示例，支持 JSON/CSV/Excel 数据源
 *
 * 运行方式:
 * npx playwright test
 *
 * 查看报告:
 * npx playwright show-report
 */

const { test, expect } = require('@playwright/test');
const fs = require('fs');

// 测试基础URL
const BASE_URL = 'https://example.com/shop';

// 加载测试数据
const testData = require('./test-data.json');

// 辅助函数：登录
async function login(page, username, password) {
  await page.goto(`${BASE_URL}/login`);
  await page.waitForLoadState('networkidle');

  // 使用语义化选择器
  await page.getByLabel('用户名').fill(username);
  await page.getByLabel('密码').fill(password);
  await page.getByRole('button', { name: '登录' }).click();
}

test.describe('电商登录模块', () => {
  /**
   * TC-001: 正常登录测试
   */
  test('TC-001: 正常登录测试', async ({ page }) => {
    await login(page, 'user1', 'pass123');

    // 验证跳转到仪表板
    await expect(page).toHaveURL(`${BASE_URL}/dashboard`);
    await expect(page.getByRole('heading', { name: '欢迎' })).toBeVisible();
  });

  /**
   * TC-002: 密码错误测试
   */
  test('TC-002: 密码错误测试', async ({ page }) => {
    await login(page, 'user1', 'wrongpass');

    // 验证错误提示
    await expect(page.getByText('密码错误').first()).toBeVisible();
    await expect(page).toHaveURL(`${BASE_URL}/login`);
  });

  /**
   * TC-003: 用户名为空测试
   */
  test('TC-003: 用户名为空测试', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    // 用户名留空，只输入密码
    await page.getByLabel('密码').fill('pass123');
    await page.getByRole('button', { name: '登录' }).click();

    // 验证错误提示
    await expect(page.getByText('用户名不能为空').first()).toBeVisible();
  });

  /**
   * TC-004: 密码为空测试
   */
  test('TC-004: 密码为空测试', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    // 密码留空，只输入用户名
    await page.getByLabel('用户名').fill('user1');
    await page.getByRole('button', { name: '登录' }).click();

    // 验证错误提示
    await expect(page.getByText('密码不能为空').first()).toBeVisible();
  });

  /**
   * TC-005: 记住我功能
   */
  test('TC-005: 记住我功能', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    // 输入凭证并勾选记住我
    await page.getByLabel('用户名').fill('user1');
    await page.getByLabel('密码').fill('pass123');
    await page.getByLabel('记住我').check();
    await page.getByRole('button', { name: '登录' }).click();

    // 验证登录成功
    await expect(page).toHaveURL(`${BASE_URL}/dashboard`);

    // 保存存储状态
    await page.context().storageState({ path: 'auth.json' });
  });

  /**
   * TC-006: 忘记密码功能
   */
  test('TC-006: 忘记密码功能', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    // 点击忘记密码链接
    await page.getByRole('link', { name: '忘记密码' }).click();

    // 验证跳转到密码重置页面
    await expect(page).toHaveURL(`${BASE_URL}/forgot-password`);

    // 输入邮箱
    await page.getByLabel('邮箱').fill('user1@example.com');
    await page.getByRole('button', { name: '发送重置链接' }).click();

    // 验证提示
    await expect(page.getByText('密码重置链接已发送').first()).toBeVisible();
  });

  /**
   * TC-007: 忘记密码 - 无效邮箱
   */
  test('TC-007: 忘记密码 - 无效邮箱', async ({ page }) => {
    await page.goto(`${BASE_URL}/login`);

    // 点击忘记密码链接
    await page.getByRole('link', { name: '忘记密码' }).click();

    // 输入不存在的邮箱
    await page.getByLabel('邮箱').fill('nonexistent@example.com');
    await page.getByRole('button', { name: '发送重置链接' }).click();

    // 验证错误提示
    await expect(page.getByText('邮箱未注册').first()).toBeVisible();
  });

  /**
   * TC-008: 用户登出功能
   */
  test('TC-008: 用户登出功能', async ({ page }) => {
    // 先登录
    await login(page, 'user1', 'pass123');
    await expect(page).toHaveURL(`${BASE_URL}/dashboard`);

    // 点击用户菜单
    await page.getByTestId('user-menu').click();

    // 点击登出按钮
    await page.getByRole('button', { name: '登出' }).click();

    // 验证跳转到登录页
    await expect(page).toHaveURL(`${BASE_URL}/login`);
  });

  // ==========================================
  // 数据驱动测试
  // ==========================================

  test.describe('数据驱动登录测试', () => {
    // 方法1: 使用 forEach 遍历
    testData.forEach((data) => {
      test(`登录测试: ${data.description}`, async ({ page }) => {
        await login(page, data.username, data.password);

        if (data.shouldSucceed) {
          await expect(page).toHaveURL(`${BASE_URL}/dashboard`);
        } else {
          await expect(page.getByText('登录失败').first()).toBeVisible();
        }
      });
    });

    // 方法2: 使用 for 循环遍历测试数据（Playwright 推荐方式）
    const testCases = [
      { username: 'user1', password: 'pass123', shouldSucceed: true, description: '正常登录' },
      { username: 'user1', password: 'wrongpass', shouldSucceed: false, description: '密码错误' },
      { username: '', password: 'pass123', shouldSucceed: false, description: '用户名为空' },
      { username: 'user1', password: '', shouldSucceed: false, description: '密码为空' },
    ];

    for (const tc of testCases) {
      test(`数据驱动登录测试: ${tc.description}`, async ({ page }) => {
        await login(page, tc.username, tc.password);

        if (tc.shouldSucceed) {
          await expect(page).toHaveURL(`${BASE_URL}/dashboard`);
        } else {
          await expect(page.getByText('登录失败').first()).toBeVisible();
        }
      });
    }
  });

  // ==========================================
  // CSV 数据驱动示例（需要安装 csv-parse）
  // 运行前: npm install csv-parse
  // ==========================================

  // 注意: 由于 test.describe.skip 在模块加载时仍会执行 require，
  // 因此将可选依赖的示例注释掉，需要时取消注释
  /*
  test.describe('CSV 数据驱动测试', () => {
    const { parse } = require('csv-parse/sync');

    // 读取 CSV 数据
    const csvContent = fs.readFileSync('./test-data.csv', 'utf-8');
    const csvData = parse(csvContent, {
      columns: true,
      skip_empty_lines: true,
    });

    csvData.forEach((data) => {
      test(`CSV 登录测试: ${data.description}`, async ({ page }) => {
        await login(page, data.username, data.password);

        if (data.shouldSucceed === 'true') {
          await expect(page).toHaveURL(`${BASE_URL}/dashboard`);
        } else {
          await expect(page.getByText('登录失败').first()).toBeVisible();
        }
      });
    });
  });
  */

  // ==========================================
  // Excel 数据驱动示例（需要安装 xlsx）
  // 运行前: npm install xlsx
  // ==========================================

  /*
  test.describe('Excel 数据驱动测试', () => {
    const xlsx = require('xlsx');

    // 读取 Excel 数据
    const workbook = xlsx.readFile('./test-data.xlsx');
    const sheetData = xlsx.utils.sheet_to_json(workbook.Sheets['Sheet1']);

    sheetData.forEach((data) => {
      test(`Excel 登录测试: ${data.TestCase}`, async ({ page }) => {
        await login(page, data.Username, data.Password);

        if (data.ExpectedResult === 'Success') {
          await expect(page).toHaveURL(`${BASE_URL}/dashboard`);
        } else {
          await expect(page.getByText('登录失败').first()).toBeVisible();
        }
      });
    });
  });
  */
});
