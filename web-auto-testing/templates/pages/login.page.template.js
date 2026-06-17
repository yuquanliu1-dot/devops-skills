/**
 * 登录页面对象模板
 *
 * 用途：封装登录页面的所有元素和操作
 *
 * 使用方法：
 * 1. 复制此模板到 pages/LoginPage.js
 * 2. 根据实际页面修改选择器
 * 3. 在测试中导入并使用
 */

const { BasePage } = require('./BasePage');

class LoginPage extends BasePage {
  /**
   * 构造函数 - 定义登录页面的所有元素
   * @param {Page} page - Playwright Page 对象
   */
  constructor(page) {
    super(page);

    // 登录表单元素（请根据实际页面修改选择器）
    this.usernameInput = page.locator('[data-testid="username"]');
    this.passwordInput = page.locator('[data-testid="password"]');
    this.loginButton = page.getByRole('button', { name: /登录|登录|login/i });
    this.rememberMeCheckbox = page.locator('[data-testid="remember-me"]');

    // 错误消息元素
    this.errorMessage = page.locator('[data-testid="error-message"]');
    this.usernameError = page.locator('[data-testid="username-error"]');
    this.passwordError = page.locator('[data-testid="password-error"]');

    // 链接元素
    this.forgotPasswordLink = page.getByRole('link', { name: /忘记密码|forgot password/i });
    this.registerLink = page.getByRole('link', { name: /注册|register|sign up/i });
  }

  /**
   * 导航到登录页
   */
  async goto() {
    await super.goto('/login');
  }

  /**
   * 执行登录操作
   * @param {string} username - 用户名
   * @param {string} password - 密码
   * @param {Object} options - 登录选项
   * @param {boolean} options.rememberMe - 是否记住登录状态
   */
  async login(username, password, options = {}) {
    // 等待页面加载
    await this.waitForPageReady();

    // 填写用户名
    await this.usernameInput.fill(username);

    // 填写密码
    await this.passwordInput.fill(password);

    // 记住我选项
    if (options.rememberMe) {
      await this.rememberMeCheckbox.check();
    }

    // 点击登录按钮
    await this.loginButton.click();

    // 等待登录完成
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * 验证登录成功
   * @returns {Promise<boolean>} 是否登录成功
   */
  async verifyLoginSuccess() {
    // 检查是否跳转到首页或 dashboard
    await this.page.waitForURL(/\/(dashboard|home)?/);
    return true;
  }

  /**
   * 验证登录失败
   * @param {string} expectedMessage - 期望的错误消息
   * @returns {Promise<boolean>} 是否显示预期错误消息
   */
  async verifyLoginFailure(expectedMessage) {
    await this.waitForVisible(this.errorMessage);
    const actualMessage = await this.getText(this.errorMessage);
    return actualMessage.includes(expectedMessage);
  }

  /**
   * 获取错误消息
   * @returns {Promise<string>} 错误消息文本
   */
  async getErrorMessage() {
    return await this.getText(this.errorMessage);
  }

  /**
   * 检查用户名字段是否显示错误
   * @returns {Promise<boolean>} 是否显示用户名错误
   */
  async isUsernameErrorVisible() {
    return await this.isElementVisible(this.usernameError);
  }

  /**
   * 检查密码字段是否显示错误
   * @returns {Promise<boolean>} 是否显示密码错误
   */
  async isPasswordErrorVisible() {
    return await this.isElementVisible(this.passwordError);
  }

  /**
   * 点击忘记密码链接
   */
  async clickForgotPassword() {
    await this.click(this.forgotPasswordLink);
  }

  /**
   * 点击注册链接
   */
  async clickRegister() {
    await this.click(this.registerLink);
  }

  /**
   * 清空登录表单
   */
  async clearForm() {
    await this.usernameInput.clear();
    await this.passwordInput.clear();
    if (await this.rememberMeCheckbox.isChecked()) {
      await this.rememberMeCheckbox.uncheck();
    }
  }

  /**
   * 截取登录页面截图
   * @param {string} suffix - 文件名后缀
   */
  async captureScreenshot(suffix = 'login-page') {
    await this.screenshot(`login-${suffix}.png`);
  }
}

module.exports = { LoginPage };
