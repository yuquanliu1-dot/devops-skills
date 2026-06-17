/**
 * 快速验证模板
 *
 * 用途：在生成正式测试前，先用这个模板验证选择器
 *
 * 使用流程：
 * 1. 复制这个模板
 * 2. 填入需要测试的元素选择器
 * 3. 本地运行：npx playwright test quick-validation.spec.js --debug
 * 4. 确认所有选择器可用后，再生成完整测试
 *
 * 参考业界最佳实践：
 * - Playwright Official Best Practices
 * - Airbnb JavaScript Testing Style Guide
 * - Microsoft Playwright Guidelines
 */

const { test, expect } = require('@playwright/test');

test.describe('快速验证：选择器测试', () => {
  const baseURL = 'http://10.198.249.4:8888/index.html';

  test('验证：下拉框选择器', async ({ page }) => {
    await page.goto(baseURL);

    // ✅ 等待页面稳定（优于固定延迟）
    await page.waitForLoadState('networkidle');

    // ✅ 使用语义化选择器（优先级1）
    await page.getByRole('link', { name: '研发云全流程指导工具' }).click();

    const iframe = page.frameLocator('#content-frame');

    // TODO: 在这里填入要测试的选择器
    // 示例：验证 Element UI 下拉框
    // 注意：使用 .first() 处理多元素匹配（Strict Mode Violation 防护）
    const dropdown = iframe.locator('.el-select').first();

    // 验证1：元素存在
    await expect(dropdown).toBeAttached();

    // 验证2：可以点击
    await dropdown.click();

    // ✅ 使用明确的等待条件（而非固定延迟）
    await expect(iframe.getByRole('option')).toBeVisible();

    console.log('✅ 下拉框选择器验证通过');
  });

  test('验证：按钮选择器', async ({ page }) => {
    await page.goto(baseURL);
    await page.waitForLoadState('networkidle');

    // ✅ 使用语义化选择器
    await page.getByRole('link', { name: '研发云全流程指导工具' }).click();

    const iframe = page.frameLocator('#content-frame');

    // TODO: 填入按钮选择器
    // ✅ 优先使用 getByRole（最稳定）
    const button = iframe.getByRole('button', { name: '查看检查细则' });

    await expect(button).toBeAttached();
    await button.click();

    // ✅ 等待页面响应（而非固定延迟）
    await page.waitForLoadState('domcontentloaded');

    console.log('✅ 按钮选择器验证通过');
  });

  test('验证：文本断言', async ({ page }) => {
    await page.goto(baseURL);
    await page.waitForLoadState('networkidle');

    await page.getByRole('link', { name: '研发云全流程指导工具' }).click();

    const iframe = page.frameLocator('#content-frame');

    // TODO: 填入要验证的文本
    // ✅ 使用 .first() 处理多元素匹配
    // 或者使用更精确的选择器：getByRole + name
    const textElement = iframe.getByText('研发活动全流程上云检查细则').first();

    await expect(textElement).toBeAttached();

    console.log('✅ 文本断言验证通过');
  });
});

/**
 * 验证清单：
 *
 * ✅ 所有选择器都能找到元素
 * ✅ 所有交互都能执行（点击、填表等）
 * ✅ 所有断言都能通过
 * ✅ 在有界面模式运行成功
 *
 * 然后才能：
 * - 生成完整的测试用例
 * - 添加到CI流程
 * - 用于回归测试
 */
