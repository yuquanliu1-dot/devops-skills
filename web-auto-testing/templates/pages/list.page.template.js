/**
 * 列表页面对象模板
 *
 * 用途：封装列表页面的所有元素和操作
 * 适用场景：商品列表、用户列表、文章列表等
 *
 * 使用方法：
 * 1. 复制此模板到 pages/ListPage.js
 * 2. 根据实际页面修改选择器
 * 3. 在测试中导入并使用
 */

const { BasePage } = require('./BasePage');

class ListPage extends BasePage {
  /**
   * 构造函数 - 定义列表页面的所有元素
   * @param {Page} page - Playwright Page 对象
   */
  constructor(page) {
    super(page);

    // 搜索和筛选元素
    this.searchInput = page.locator('[data-testid="search-input"]');
    this.searchButton = page.getByRole('button', { name: /搜索|search/i });
    this.filterDropdown = page.locator('[data-testid="filter-dropdown"]');
    this.sortDropdown = page.locator('[data-testid="sort-dropdown"]');

    // 列表元素
    this.listContainer = page.locator('[data-testid="list-container"]');
    this.listItems = page.locator('[data-testid="list-item"]');
    this.emptyState = page.locator('[data-testid="empty-state"]');
    this.loadingSpinner = page.locator('[data-testid="loading-spinner"]');

    // 分页元素
    this.pagination = page.locator('[data-testid="pagination"]');
    this.previousButton = page.getByRole('button', { name: /上一页|previous/i });
    this.nextButton = page.getByRole('button', { name: /下一页|next/i });
    this.pageInfo = page.locator('[data-testid="page-info"]');

    // 批量操作元素
    this.selectAllCheckbox = page.locator('[data-testid="select-all"]');
    this.deleteSelectedButton = page.getByRole('button', { name: /删除选中|delete selected/i });
  }

  /**
   * 导航到列表页
   * @param {string} path - 列表页路径（默认为 /list）
   */
  async goto(path = '/list') {
    await super.goto(path);
    await this.waitForListLoaded();
  }

  /**
   * 等待列表加载完成
   */
  async waitForListLoaded() {
    await this.listContainer.waitFor({ state: 'visible' });
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * 搜索列表项
   * @param {string} keyword - 搜索关键词
   */
  async search(keyword) {
    await this.searchInput.fill(keyword);
    await this.searchButton.click();
    await this.waitForListLoaded();
  }

  /**
   * 按筛选条件过滤
   * @param {string} filterValue - 筛选值
   */
  async filterBy(filterValue) {
    await this.filterDropdown.selectOption(filterValue);
    await this.waitForListLoaded();
  }

  /**
   * 排序列表
   * @param {string} sortValue - 排序值
   */
  async sortBy(sortValue) {
    await this.sortDropdown.selectOption(sortValue);
    await this.waitForListLoaded();
  }

  /**
   * 获取列表项数量
   * @returns {Promise<number>} 列表项数量
   */
  async getItemCount() {
    await this.waitForListLoaded();
    return await this.listItems.count();
  }

  /**
   * 检查列表是否为空
   * @returns {Promise<boolean>} 列表是否为空
   */
  async isEmpty() {
    await this.waitForListLoaded();
    return await this.isElementVisible(this.emptyState);
  }

  /**
   * 点击指定索引的列表项
   * @param {number} index - 列表项索引（从0开始）
   */
  async clickItem(index) {
    const item = this.listItems.nth(index);
    await this.waitForVisible(item);
    await this.click(item);
  }

  /**
   * 点击指定文本的列表项
   * @param {string} text - 列表项文本
   */
  async clickItemByText(text) {
    const item = this.listItems.filter({ hasText: text }).first();
    await this.waitForVisible(item);
    await this.click(item);
  }

  /**
   * 获取列表项的文本内容
   * @param {number} index - 列表项索引
   * @returns {Promise<string>} 列表项文本
   */
  async getItemText(index) {
    const item = this.listItems.nth(index);
    return await this.getText(item);
  }

  /**
   * 选择列表项（复选框）
   * @param {number} index - 列表项索引
   */
  async selectItem(index) {
    const item = this.listItems.nth(index);
    const checkbox = item.locator('[type="checkbox"]');
    await checkbox.check();
  }

  /**
   * 全选列表项
   */
  async selectAll() {
    await this.selectAllCheckbox.check();
  }

  /**
   * 删除选中的列表项
   */
  async deleteSelected() {
    await this.deleteSelectedButton.click();
    // 确认删除（如果有确认弹窗）
    // await this.page.getByRole('button', { name: '确认' }).click();
    await this.waitForListLoaded();
  }

  /**
   * 点击下一页
   */
  async goToNextPage() {
    await this.click(this.nextButton);
    await this.waitForListLoaded();
  }

  /**
   * 点击上一页
   */
  async goToPreviousPage() {
    await this.click(this.previousButton);
    await this.waitForListLoaded();
  }

  /**
   * 获取当前页码信息
   * @returns {Promise<string>} 页码信息文本
   */
  async getPageInfo() {
    return await this.getText(this.pageInfo);
  }

  /**
   * 检查是否有下一页
   * @returns {Promise<boolean>} 是否有下一页
   */
  async hasNextPage() {
    const isEnabled = await this.nextButton.isEnabled();
    return isEnabled;
  }

  /**
   * 检查是否有上一页
   * @returns {Promise<boolean>} 是否有上一页
   */
  async hasPreviousPage() {
    const isEnabled = await this.previousButton.isEnabled();
    return isEnabled;
  }

  /**
   * 截取列表页面截图
   * @param {string} suffix - 文件名后缀
   */
  async captureScreenshot(suffix = 'list-page') {
    await this.screenshot(`list-${suffix}.png`);
  }

  /**
   * 滚动到列表底部
   */
  async scrollToBottom() {
    await this.listItems.last().scrollIntoViewIfNeeded();
  }
}

module.exports = { ListPage };
