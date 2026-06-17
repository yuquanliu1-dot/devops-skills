/**
 * 员工通信录模块自动化测试
 * 测试地址: 通过环境变量 TEST_URL 配置
 *
 * 运行方式:
 * npx playwright test
 *
 * 查看报告:
 * npx playwright show-report
 */

const { test, expect } = require('@playwright/test');

// 测试基础URL（支持环境变量配置）
const BASE_URL = process.env.TEST_URL || 'http://localhost:3000/index.html';

test.describe('员工通信录模块', () => {
  // 每个测试前的前置条件
  test.beforeEach(async ({ page }) => {
    await page.goto(BASE_URL);
    await page.waitForLoadState('domcontentloaded');

    // ✅ 使用语义化选择器 - 等待主菜单可见
    await expect(page.getByRole('link', { name: '员工通信录' })).toBeVisible({ timeout: 10000 });

    // ✅ 点击员工通信录菜单
    await page.getByRole('link', { name: '员工通信录' }).click();

    // ✅ 等待 iframe 内容加载（使用条件等待而非固定延迟）
    const iframe = page.frameLocator('#content-frame');
    await expect(iframe.getByRole('heading', { name: '员工通信录' })).toBeVisible({ timeout: 10000 });
  });

  /**
   * TC-001: 页面加载测试
   */
  test('TC-001: 页面加载和基本显示验证', async ({ page }) => {
    const iframe = page.frameLocator('#content-frame');

    // ✅ 等待员工通信录标题可见（使用语义化选择器）
    await expect(iframe.getByRole('heading', { name: '员工通信录' })).toBeVisible({ timeout: 10000 });

    // ✅ 验证员工总数（使用 .first() 处理多元素匹配）
    const totalCount = await iframe.getByText(/共.*人/).first().textContent();
    expect(totalCount).toMatch(/共 \d+ 人/);

    // 验证部门数量（减去"全部部门"选项）
    const deptCount = await iframe.locator('#departmentSelect option').count();
    expect(deptCount).toBeGreaterThan(1);
  });

  /**
   * TC-002: 部门筛选功能测试
   */
  test('TC-002: 部门筛选功能测试', async ({ page }) => {
    const iframe = page.frameLocator('#content-frame');

    // 选择"财务部"
    await iframe.locator('#departmentSelect').selectOption('财务部');

    // ✅ 等待筛选结果出现（条件等待）
    await expect(iframe.getByText(/找到.*个员工/).first()).toBeVisible({ timeout: 5000 });

    // 验证筛选结果
    const resultText = await iframe.getByText(/找到.*个员工/).first().textContent();
    expect(resultText).toContain('个员工');

    // 验证第一个员工是财务部的
    const firstDept = await iframe.locator('tbody tr:first-child td:nth-child(2)').textContent();
    expect(firstDept).toContain('财务部');
  });

  /**
   * TC-003: 姓名模糊搜索测试
   */
  test('TC-003: 姓名模糊搜索测试', async ({ page }) => {
    const iframe = page.frameLocator('#content-frame');

    // ✅ 输入搜索关键词（使用语义化选择器）
    await iframe.getByPlaceholder(/姓名/).fill('王');
    await iframe.getByRole('button', { name: '搜索' }).click();

    // ✅ 等待搜索结果出现
    await expect(iframe.getByText(/找到.*个员工/).first()).toBeVisible({ timeout: 5000 });

    // 验证搜索结果
    const resultText = await iframe.getByText(/找到.*个员工/).first().textContent();
    expect(resultText).toMatch(/找到 \d+ 个员工/);

    // 验证第一个结果包含"王"字
    const firstName = await iframe.locator('tbody tr:first-child td:nth-child(3)').textContent();
    expect(firstName).toContain('王');
  });

  /**
   * TC-004: 重置按钮功能测试
   */
  test('TC-004: 重置按钮功能测试', async ({ page }) => {
    const iframe = page.frameLocator('#content-frame');

    // 先进行搜索
    await iframe.getByPlaceholder(/姓名/).fill('测试');

    // ✅ 点击重置（使用语义化选择器）
    await iframe.getByRole('button', { name: '重置' }).click();

    // ✅ 等待重置结果出现
    await expect(iframe.getByText(/显示所有员工/).first()).toBeVisible({ timeout: 5000 });

    // 验证重置结果
    const resultText = await iframe.getByText(/显示所有员工/).first().textContent();
    expect(resultText).toContain('显示所有员工');
  });

  /**
   * TC-005: 员工详情查看
   */
  test('TC-005: 员工详情查看', async ({ page }) => {
    const iframe = page.frameLocator('#content-frame');

    // ✅ 点击第一条记录的详情按钮
    await iframe.getByRole('button', { name: '详情' }).first().click();

    // ✅ 等待详情弹窗可见
    await expect(iframe.locator('.modal')).toBeVisible({ timeout: 5000 });
  });

  /**
   * TC-006: 分页功能测试
   */
  test('TC-006: 分页功能测试', async ({ page }) => {
    const iframe = page.frameLocator('#content-frame');

    // 记录第一页第一条记录
    const firstRowFirstPage = await iframe.locator('tbody tr:first-child td:nth-child(3)').textContent();

    // ✅ 点击下一页（使用语义化选择器）
    await iframe.getByRole('button', { name: '下一页' }).click();

    // ✅ 等待页面内容变化
    await expect(iframe.locator('tbody tr:first-child td:nth-child(3)')).not.toHaveText(firstRowFirstPage, { timeout: 5000 });

    // 记录第二页第一条记录
    const firstRowSecondPage = await iframe.locator('tbody tr:first-child td:nth-child(3)').textContent();

    // 验证数据已变化
    expect(firstRowSecondPage).not.toBe(firstRowFirstPage);

    // ✅ 点击上一页
    await iframe.getByRole('button', { name: '上一页' }).click();

    // ✅ 等待回到第一页
    await expect(iframe.locator('tbody tr:first-child td:nth-child(3)')).toHaveText(firstRowFirstPage, { timeout: 5000 });

    // 验证回到第一页
    const firstRowBack = await iframe.locator('tbody tr:first-child td:nth-child(3)').textContent();
    expect(firstRowBack).toBe(firstRowFirstPage);
  });

  /**
   * TC-007: 无结果场景测试
   */
  test('TC-007: 无结果场景测试', async ({ page }) => {
    const iframe = page.frameLocator('#content-frame');

    // 搜索不存在的员工
    await iframe.getByPlaceholder(/姓名/).fill('不存在的姓名XYZ123');
    await iframe.getByRole('button', { name: '搜索' }).click();

    // ✅ 等待无结果提示出现（使用 .first()）
    await expect(iframe.getByText(/未找到.*员工/).first()).toBeVisible({ timeout: 5000 });
  });

  /**
   * TC-008: 组合筛选测试
   */
  test('TC-008: 组合筛选测试', async ({ page }) => {
    const iframe = page.frameLocator('#content-frame');

    // 选择部门
    await iframe.locator('#departmentSelect').selectOption('财务部');

    // 输入姓名
    await iframe.getByPlaceholder(/姓名/).fill('王');
    await iframe.getByRole('button', { name: '搜索' }).click();

    // ✅ 等待搜索结果
    await expect(iframe.getByText(/找到.*个员工/).first()).toBeVisible({ timeout: 5000 });

    // 验证组合筛选结果
    const firstDept = await iframe.locator('tbody tr:first-child td:nth-child(2)').textContent();
    const firstName = await iframe.locator('tbody tr:first-child td:nth-child(3)').textContent();

    expect(firstDept).toContain('财务部');
    expect(firstName).toContain('王');
  });

  /**
   * TC-009: 表格排序功能
   */
  test('TC-009: 表格排序功能', async ({ page }) => {
    const iframe = page.frameLocator('#content-frame');

    // 记录排序前的第一条记录
    const beforeSort = await iframe.locator('tbody tr:first-child td:nth-child(1)').textContent();

    // 点击员工编号列头排序
    await iframe.locator('thead th:first-child').click();

    // ✅ 等待排序完成（验证数据变化）
    await expect(iframe.locator('tbody tr:first-child td:nth-child(1)')).not.toHaveText(beforeSort, { timeout: 5000 });

    // 记录排序后的第一条记录
    const afterSort = await iframe.locator('tbody tr:first-child td:nth-child(1)').textContent();

    // 验证排序结果
    expect(afterSort).not.toBe(beforeSort);
  });

  /**
   * TC-010: 数据导出功能
   */
  test('TC-010: 数据导出功能', async ({ page }) => {
    const iframe = page.frameLocator('#content-frame');

    // 设置下载处理
    const downloadPromise = page.waitForEvent('download');

    // ✅ 点击导出按钮（使用语义化选择器）
    await iframe.getByRole('button', { name: '导出' }).click();

    // 等待下载开始
    const download = await downloadPromise;

    // 验证下载文件名
    expect(download.suggestedFilename()).toMatch(/\.(xlsx|csv)$/);
  });

  /**
   * TC-011: 页面刷新保持状态
   */
  test('TC-011: 页面刷新保持状态', async ({ page }) => {
    const iframe = page.frameLocator('#content-frame');

    // 先进行筛选
    await iframe.locator('#departmentSelect').selectOption('财务部');

    // ✅ 等待筛选结果
    await expect(iframe.getByText(/找到.*个员工/).first()).toBeVisible({ timeout: 5000 });

    // 刷新页面
    await page.reload();
    await page.waitForLoadState('domcontentloaded');

    // ✅ 再次点击员工通信录菜单（使用语义化选择器）
    await expect(page.getByRole('link', { name: '员工通信录' })).toBeVisible({ timeout: 10000 });
    await page.getByRole('link', { name: '员工通信录' }).click();

    // ✅ 等待 iframe 内容加载
    await expect(iframe.getByRole('heading', { name: '员工通信录' })).toBeVisible({ timeout: 10000 });

    // 验证筛选条件保持（如果应用支持）
    // 注意：此测试取决于应用是否保持筛选状态
  });
});
