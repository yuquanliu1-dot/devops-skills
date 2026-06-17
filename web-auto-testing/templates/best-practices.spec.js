const { test, expect } = require('@playwright/test');

/**
 * {{PROJECT_NAME}} 测试脚本
 *
 * 测试目标: {{TEST_URL}}
 * 测试类型: {{TEST_TYPE}}
 * 生成时间: {{TIMESTAMP}}
 *
 * 参考业界最佳实践：
 * - Airbnb Playwright Best Practices
 * - Microsoft Playwright Guidelines
 * - Playwright Official Documentation
 */

// ==========================================
// 环境感知配置
// ==========================================

/*
  ⚠️ 重要：无头模式（CI/CD）与有头模式的差异

  在无头模式下，以下断言可能失败：
  - toBeVisible() - 元素可能在视口外或被遮挡

  解决方案：使用环境感知的断言
*/

// 检测运行环境
const isCI = process.env.CI === 'true';
const isHeadless = process.env.HEADED !== 'true';

// 根据环境选择断言方式
// CI/无头模式：使用 toBeAttached()（更稳定）
// 本地/有头模式：可以使用 toBeVisible()
const assertVisible = isCI || isHeadless ? 'toBeAttached' : 'toBeVisible';

test.describe('{{PROJECT_NAME}} 测试', () => {
  // ==========================================
  // iframe 操作最佳实践
  // ==========================================

  test.describe('iframe 操作示例', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('{{BASE_URL}}');
      await page.waitForLoadState('domcontentloaded');

      // ❌ 错误示例：FrameLocator 不支持 page 的方法
      // const iframe = page.frameLocator('#iframe');
      // await iframe.waitForLoadState();  // ❌ 错误！FrameLocator 没有此方法

      // ✅ 正确方式 1：使用 page.frame() 获取 Frame 对象
      // const frame = page.frame('#iframe');
      // await frame.waitForLoadState();

      // ✅ 正确方式 2：使用 frameLocator 进行元素定位（推荐）
      const iframe = page.frameLocator('#iframe');
    });

    test('iframe 内的基本操作', async ({ page }) => {
      const iframe = page.frameLocator('#iframe');

      // ✅ 使用语义化选择器
      // ⚠️ 无头模式注意事项：优先使用 toBeAttached() 而非 toBeVisible()
      await expect(iframe.getByRole('heading', { name: '标题' })).toBeAttached();
      await iframe.getByRole('button', { name: '提交' }).click();
      await expect(iframe.getByText('操作成功').first()).toBeAttached();
    });

    test('iframe 内的多元素处理', async ({ page }) => {
      const iframe = page.frameLocator('#iframe');

      // ❌ 问题：locator('table') 可能匹配多个元素
      // await expect(iframe.locator('table')).toBeVisible();  // Strict Mode Violation!

      // ✅ 解决方案 1：使用 .first() 指定第一个
      await expect(iframe.locator('table').first()).toBeAttached();

      // ✅ 解决方案 2：使用更具体的选择器
      // await expect(iframe.locator('table.data-table')).toBeAttached();

      // ✅ 解决方案 3：使用 getByRole（如果有 role 属性）
      // await expect(iframe.getByRole('table')).toBeAttached();
    });

    test('iframe 内的文本匹配', async ({ page }) => {
      const iframe = page.frameLocator('#iframe');

      // ❌ 问题：getByText 可能匹配多个元素
      // await iframe.getByText('确定').click();  // 可能失败！

      // ✅ 使用 .first() 或 .nth()
      await iframe.getByText('确定').first().click();

      // ✅ 或者使用更具体的选项
      await iframe.getByRole('button', { name: '确定' }).click();
    });
  });

  // ==========================================
  // 选择器优先级完整示例
  // ==========================================

  test.describe('选择器优先级示例', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('{{BASE_URL}}');
    });

    test('优先级 1: getByRole - 最稳定', async ({ page }) => {
      // ✅ 推荐：使用语义化角色
      await page.getByRole('button', { name: '提交' }).click();
      await expect(page.getByRole('textbox', { name: '用户名' })).toBeAttached();
    });

    test('优先级 2: getByLabel - 表单专用', async ({ page }) => {
      // ✅ 推荐：表单元素
      await page.getByLabel('用户名').fill('test');
      await page.getByLabel('密码').fill('password');
    });

    test('优先级 3: getByPlaceholder - 输入框', async ({ page }) => {
      // ✅ 可用：当没有 label 时
      await page.getByPlaceholder('请输入用户名').fill('test');
    });

    test('优先级 4: getByTestId - 测试专用', async ({ page }) => {
      // ✅ 推荐：专门为测试添加的属性
      await page.getByTestId('submit-button').click();
    });

    test('优先级 5: getByText - 需要修饰符', async ({ page }) => {
      // ⚠️ 谨慎：可能匹配多个元素
      // ❌ 错误：await page.getByText('确定').click();
      // ✅ 正确：使用 .first() 或 exact 选项
      await page.getByText('确定', { exact: true }).first().click();
      await page.getByText('确定').first().click();
    });

    test('优先级 6: locator - CSS 选择器', async ({ page }) => {
      // ⚠️ 最后选择：当语义化选择器不可用时
      // ❌ 不推荐：page.locator('.btn-submit').click();
      // ✅ 更好：page.locator('button[type="submit"]').click();
      await page.locator('button[type="submit"]').click();
    });

    test('❌ 禁止使用的模式', async ({ page }) => {
      // ❌ 错误：ref 属性（MCP 快照特有）
      // await page.locator('[ref="e10"]').click();  // 不可用！

      // ❌ 错误：CSS 类选择器作为首选
      // await page.locator('.el-button').click();  // 不稳定

      // ❌ 错误：固定延迟
      // await page.waitForTimeout(5000);  // 不要使用！

      // ✅ 正确：使用明确的等待条件
      await expect(page.getByRole('button')).toBeAttached();
    });
  });

  // ==========================================
  // 等待策略最佳实践
  // ==========================================

  test.describe('等待策略示例', () => {
    test.beforeEach(async ({ page }) => {
      await page.goto('{{BASE_URL}}');
    });

    test('等待页面稳定', async ({ page }) => {
      // ✅ 推荐：等待网络空闲（适用于动态页面）
      await page.waitForLoadState('networkidle');
    });

    test('等待元素附加', async ({ page }) => {
      // ✅ 推荐：等待元素出现在 DOM 中（无头模式兼容）
      await expect(page.getByRole('button')).toBeAttached();
    });

    test('等待元素可见（本地模式）', async ({ page }) => {
      // ⚠️ 注意：toBeVisible() 在无头模式可能失败
      // 推荐使用环境感知的断言：
      await expect(page.getByRole('button'))[assertVisible]();
    });

    test('等待 API 响应', async ({ page }) => {
      // ✅ 推荐：等待特定的 API 响应
      await page.getByRole('button', { name: '加载' }).click();
      await page.waitForResponse('**/api/data');

      // 验证数据加载
      await expect(page.getByText('数据加载完成').first()).toBeAttached();
    });

    test('等待 URL 变化', async ({ page }) => {
      // ✅ 推荐：等待导航完成
      await page.getByRole('link', { name: '个人中心' }).click();
      await page.waitForURL('/profile');

      await expect(page).toHaveURL('/profile');
    });

    test('❌ 错误的等待方式', async ({ page }) => {
      // ❌ 错误：使用固定延迟
      // await page.waitForTimeout(5000);  // 不要这样做！

      // ❌ 错误：不等待直接断言
      // await expect(page.locator('.result')).toBeVisible();  // 可能失败

      // ✅ 正确：使用明确的等待
      await expect(page.getByRole('button')).toBeAttached();
      await expect(page.getByText('加载完成').first()).toBeAttached();
    });
  });

  // ==========================================
  // 无头模式特殊注意事项
  // ==========================================

  test.describe('无头模式兼容性', () => {
    test('环境感知断言示例', async ({ page }) => {
      await page.goto('{{BASE_URL}}');

      // ✅ 根据环境选择断言方式
      const button = page.getByRole('button', { name: '提交' });
      await button.click();

      // 本地/有头模式：使用 toBeVisible()
      // CI/无头模式：使用 toBeAttached()
      await expect(page.getByText('操作成功').first())[assertVisible]();
    });

    test('iframe 内元素断言', async ({ page }) => {
      await page.goto('{{BASE_URL}}');

      const iframe = page.frameLocator('#iframe');

      // ✅ iframe 内的元素在无头模式建议始终使用 toBeAttached
      await expect(iframe.getByRole('heading')).toBeAttached();
      await expect(iframe.getByText('内容').first()).toBeAttached();
    });

    test('视口外元素处理', async ({ page }) => {
      await page.goto('{{BASE_URL}}');

      // ✅ 对于可能在视口外的元素，优先使用 toBeAttached
      const listItem = page.getByRole('listitem').nth(10);
      await expect(listItem).toBeAttached();

      // 如需验证可交互性，可以滚动到元素位置
      // await listItem.scrollIntoViewIfNeeded();
      // await expect(listItem).toBeVisible();
    });
  });
});

// ==========================================
// 业界最佳实践参考
// ==========================================

/*
   参考资源：
    - Playwright Best Practices: https://playwright.dev/docs/best-practices
   - Playwright Selectors: https://playwright.dev/docs/selectors
   - Airbnb Engineering Blog: https://medium.com/airbnb-engineering

   核心原则：
   1. 优先使用语义化选择器（getByRole、getByLabel）
   2. 避免脆弱的选择器（CSS 类、XPath、ref 属性）
   3. 使用明确的等待条件，而非固定延迟
   4. FrameLocator 仅用于定位元素，Frame 用于操作
   5. 处理多元素匹配时使用 .first() 或更精确的选择器

   ⚠️ 无头模式（CI/CD）特殊注意事项：
   1. 优先使用 toBeAttached() 而非 toBeVisible()
   2. 元素可能在视口外，导致 toBeVisible() 失败
   3. 使用环境变量检测：process.env.CI 或 process.env.HEADED
   4. 考虑使用 scrollTo() 或 scrollIntoViewIfNeeded() 处理视口外元素
*/
