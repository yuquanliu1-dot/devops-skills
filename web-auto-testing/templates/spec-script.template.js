const { test, expect } = require('@playwright/test');

/**
 * {{PROJECT_NAME}} 测试脚本
 *
 * 测试目标: {{TEST_URL}}
 * 测试类型: {{TEST_TYPE}}
 * 生成时间: {{TIMESTAMP}}
 *
 * 环境感知配置：
 * - CI 环境：使用 toBeAttached() （无头模式兼容）
 * - 本地环境：使用 toBeVisible() （有头模式）
 */

// 环境检测
const isCI = process.env.CI === 'true';
const isHeadless = process.env.HEADED !== 'true';

// 根据环境选择断言方式
// CI/无头模式使用 toBeAttached，本地/有头模式使用 toBeVisible
const isVisible = isCI || isHeadless ? 'toBeAttached' : 'toBeVisible';

// ⭐ 页面稳定性监控函数（最佳实践）
// 检测页面跳转或异常状态，自动恢复
async function ensurePageStability(page) {
  const currentUrl = page.url();
  if (currentUrl === 'about:blank' || !currentUrl.startsWith('http')) {
    console.warn('⚠️ 检测到页面异常，尝试恢复...');
    await page.goto(page.context()._options.baseURL || page.url());
    await page.waitForLoadState('domcontentloaded');
  }
}

// 测试描述组
test.describe('{{PROJECT_NAME}} 测试', () => {
  // 每个测试前的设置
  test.beforeEach(async ({ page }) => {
    // ⭐ 页面稳定性监控
    await ensurePageStability(page);

    // 导航到测试页面
    await page.goto('{{BASE_URL}}');

    // ⭐ 等待页面加载完成 - 使用 domcontentloaded（最佳实践）
    // 注意：现代 Web 应用常有长连接，networkidle 易超时
    await page.waitForLoadState('domcontentloaded');
  });

  // ==========================================
  // 冒烟测试 (P0)
  // ==========================================

  test.describe('冒烟测试', () => {
    test('{{TEST_CASE_P0_1_TITLE}}', async ({ page }) => {
      // 步骤 1: {{STEP_1_ACTION}}
      await page.{{METHOD_1}}();

      // 步骤 2: {{STEP_2_ACTION}}
      await page.{{METHOD_2}}();

      // 验证: {{STEP_2_EXPECTED}}
      // ✅ 使用环境感知的断言（CI 兼容）
      await expect(page.{{LOCATOR}}).{{ASSERTION}}();
    });

    test('{{TEST_CASE_P0_2_TITLE}}', async ({ page }) => {
      // 测试步骤
      await page.{{METHOD}}();

      // 验证预期结果
      await expect(page.{{LOCATOR}}).{{ASSERTION}}();
    });
  });

  // ==========================================
  // 功能测试 (P1)
  // ==========================================

  test.describe('功能测试', () => {
    test('{{TEST_CASE_P1_1_TITLE}}', async ({ page }) => {
      // 使用语义化选择器（推荐）
      await page.getByRole('button', { name: '{{BUTTON_TEXT}}' }).click();

      // ✅ 环境感知断言：CI 用 toBeAttached，本地用 toBeVisible
      const assertMethod = isVisible === 'toBeAttached' ? 'toBeAttached' : 'toBeVisible';
      await expect(page.getByText('{{EXPECTED_TEXT}}').first())[assertMethod]();
    });

    test('{{TEST_CASE_P1_2_TITLE}}', async ({ page }) => {
      // 表单输入示例
      await page.getByLabel('{{LABEL_TEXT}}').fill('{{INPUT_VALUE}}');
      await page.getByRole('button', { name: '提交' }).click();

      // ✅ 环境感知断言
      await expect(page.getByText('操作成功').first())[isVisible]();
    });
  });

  // ==========================================
  // 边界测试 (P2)
  // ==========================================

  test.describe('边界测试', () => {
    test('输入验证测试', async ({ page }) => {
      // 测试空输入
      await page.getByLabel('用户名').fill('');
      await page.getByRole('button', { name: '提交' }).click();

      // ✅ 环境感知断言
      await expect(page.getByText('用户名不能为空').first())[isVisible]();
    });

    test('超长输入测试', async ({ page }) => {
      // 测试超长输入
      const longText = 'a'.repeat(1000);
      await page.getByLabel('描述').fill(longText);
      await page.getByRole('button', { name: '提交' }).click();

      // ✅ 环境感知断言
      await expect(page.getByText('输入过长').first())[isVisible]();
    });
  });

  // ==========================================
  // 数据驱动测试示例
  // ==========================================

  test.describe('数据驱动测试', () => {
    // 测试数据
    const testData = [
      { username: 'user1', password: 'pass1', shouldSucceed: true },
      { username: 'user2', password: 'wrong', shouldSucceed: false },
      { username: '', password: 'pass1', shouldSucceed: false },
    ];

    // 遍历测试数据
    for (const data of testData) {
      test(`登录测试: ${data.username}`, async ({ page }) => {
        await page.getByLabel('用户名').fill(data.username);
        await page.getByLabel('密码').fill(data.password);
        await page.getByRole('button', { name: '登录' }).click();

        if (data.shouldSucceed) {
          await expect(page).toHaveURL('/dashboard');
        } else {
          // ✅ 环境感知断言
          await expect(page.getByText('登录失败').first())[isVisible]();
        }
      });
    }
  });

  // ==========================================
  // 复杂场景示例
  // ==========================================

  test.describe('复杂场景', () => {
    test('处理懒加载内容', async ({ page }) => {
      // ⭐ 等待懒加载内容 - 使用 domcontentloaded + 元素等待（最佳实践）
      await page.waitForLoadState('domcontentloaded');

      // ✅ 环境感知断言 - 等待元素可见
      await expect(page.locator('.lazy-loaded').first()).toBeAttached();
    });

    test('等待 AJAX 响应', async ({ page }) => {
      // 点击触发 AJAX
      await page.getByRole('button', { name: '加载数据' }).click();

      // 等待 API 响应
      await page.waitForResponse('**/api/data');

      // ✅ 环境感知断言
      await expect(page.getByText('数据加载完成').first())[isVisible]();
    });

    test('iframe 内操作', async ({ page }) => {
      // ✅ 正确：FrameLocator 用于定位 iframe 内的元素
      const iframe = page.frameLocator('#content-frame');

      // ✅ 使用语义化选择器
      // 注意：iframe 内的元素在无头模式下也可能不可见
      // 建议使用 toBeAttached 确保元素存在于 DOM 中
      await expect(iframe.getByRole('heading', { name: '页面标题' })).toBeAttached();
      await iframe.getByRole('button', { name: '提交' }).click();

      // ⚠️ 注意：FrameLocator 不支持 waitForLoadState() 等页面方法
      // 如需等待页面状态，使用 Frame 对象：
      // const frame = page.frame('#content-frame');
      // await frame.waitForLoadState('networkidle');
    });
  });
});

// ==========================================
// 选择器最佳实践
// ==========================================

/*
  选择器优先级（严格遵循）:
  1. getByRole() - 最稳定
     await page.getByRole('button', { name: '提交' }).click();

  2. getByLabel() - 表单元素
     await page.getByLabel('用户名').fill('test');

  3. getByPlaceholder() - 输入框
     await page.getByPlaceholder('请输入').fill('test');

  4. getByText() + .first() - 文本内容
     await page.getByText('确定').first().click();

  5. locator + 属性 - CSS 选择器
     await page.locator('input[name="username"]').fill('test');

  ❌ 禁止使用 ref 属性（MCP 快照特有）
  ❌ 禁止使用 CSS 类选择器作为首选
*/

// ==========================================
// 等待策略（最佳实践）
// ==========================================

/*
  ⭐ 等待策略优先级:
  1. ✅ 等待 DOM 加载: await page.waitForLoadState('domcontentloaded');
  2. ✅ 等待元素附加: await expect(locator).toBeAttached();
  3. ✅ 等待元素可见: await expect(locator).toBeVisible();
  4. ✅ 等待 API: await page.waitForResponse('**/api/data');
  5. ✅ 等待 URL: await page.waitForURL('/dashboard');

  ⚠️ 不推荐使用 networkidle（现代 Web 应用常有长连接）
  ❌ 避免使用固定延迟: await page.waitForTimeout(5000);

  📖 业界最佳实践参考:
  - Playwright 官方文档：https://playwright.dev/docs/actionability
  - Microsoft：推荐 domcontentloaded + 元素等待
  - Google/Meta：推荐显式等待 + 断言
*/
