/**
 * 页面对象（Page Object）基类模板
 *
 * 用途：提供所有页面对象的通用方法和属性
 *
 * 使用方法：
 * 1. 复制此模板到 pages/BasePage.js
 * 2. 让具体页面类继承 BasePage
 * 3. 在具体页面类中添加特定元素和方法
 */

class BasePage {
  /**
   * 构造函数
   * @param {Page} page - Playwright Page 对象
   */
  constructor(page) {
    this.page = page;
  }

  /**
   * 导航到指定路径
   * @param {string} path - URL 路径
   */
  async goto(path = '/') {
    await this.page.goto(path);
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * 等待页面完全加载
   */
  async waitForPageReady() {
    await this.page.waitForLoadState('networkidle');
    await this.page.waitForLoadState('domcontentloaded');
  }

  /**
   * 获取页面标题
   * @returns {Promise<string>} 页面标题
   */
  async getTitle() {
    return await this.page.title();
  }

  /**
   * 获取当前 URL
   * @returns {Promise<string>} 当前 URL
   */
  async getUrl() {
    return this.page.url();
  }

  /**
   * 刷新页面
   */
  async reload() {
    await this.page.reload();
    await this.waitForPageReady();
  }

  /**
   * 截图
   * @param {string} filename - 文件名
   */
  async screenshot(filename) {
    await this.page.screenshot({
      path: `artifacts/${filename}`,
      fullPage: true
    });
  }

  /**
   * 等待元素可见
   * @param {Locator} locator - 元素定位器
   */
  async waitForVisible(locator) {
    await locator.waitFor({ state: 'visible' });
  }

  /**
   * 等待元素隐藏
   * @param {Locator} locator - 元素定位器
   */
  async waitForHidden(locator) {
    await locator.waitFor({ state: 'hidden' });
  }

  /**
   * 等待导航完成
   * @param {string} urlPattern - URL 模式（可选）
   */
  async waitForNavigation(urlPattern) {
    if (urlPattern) {
      await this.page.waitForURL(urlPattern);
    } else {
      await this.page.waitForLoadState('networkidle');
    }
  }

  /**
   * 检查元素是否存在
   * @param {Locator} locator - 元素定位器
   * @returns {Promise<boolean>} 元素是否存在
   */
  async isElementVisible(locator) {
    try {
      await locator.waitFor({ state: 'visible', timeout: 5000 });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * 获取元素文本
   * @param {Locator} locator - 元素定位器
   * @returns {Promise<string>} 元素文本内容
   */
  async getText(locator) {
    return await locator.textContent();
  }

  /**
   * 点击元素
   * @param {Locator} locator - 元素定位器
   */
  async click(locator) {
    await locator.click();
  }

  /**
   * 填写输入框
   * @param {Locator} locator - 元素定位器
   * @param {string} value - 填写值
   */
  async fill(locator, value) {
    await locator.fill(value);
  }

  /**
   * 选择下拉选项
   * @param {Locator} locator - 元素定位器
   * @param {string} value - 选项值
   */
  async selectOption(locator, value) {
    await locator.selectOption(value);
  }

  /**
   * 等待并处理弹窗
   * @param {Function} acceptCallback - 接受弹窗的回调
   */
  async handleDialog(acceptCallback) {
    this.page.on('dialog', async (dialog) => {
      await acceptCallback(dialog);
    });
  }
}

module.exports = { BasePage };
