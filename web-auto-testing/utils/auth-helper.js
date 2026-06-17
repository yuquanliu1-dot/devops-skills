/**
 * 认证辅助工具类
 * 用于处理登录检测、自动登录和会话管理
 */

class AuthHelper {
  constructor(page) {
    this.page = page;
  }

  /**
   * 检测当前页面是否为登录页面
   * @param {Object} options - 检测选项
   * @param {string[]} options.loginIndicators - 登录页面特征文本
   * @param {string[]} options.loginSelectors - 登录页面选择器
   * @returns {Promise<boolean>}
   */
  async isLoginPage(options = {}) {
    const {
      loginIndicators = [
        '请输入手机号',
        '请输入验证码',
        '发送验证码',
        '注册登录',
        '微信扫码登录',
        '登录账号',
        '密码登录',
        '手机号登录'
      ],
      // 更精确的登录页面特征 - 必须同时满足多个条件
      strictIndicators = [
        { text: '请输入手机号', required: true },
        { text: '请输入验证码', required: false },
        { text: '发送验证码', required: false }
      ],
      loginSelectors = [
        'input[placeholder*="手机号"]',
        'input[placeholder*="验证码"]',
        'input[type="password"]',
        'input[name="password"]',
        'input[placeholder*="密码"]',
        '.login-form',
        '#login-form'
      ]
    } = options;

    // 优先检查精确的登录页面特征
    let matchCount = 0;
    for (const indicator of strictIndicators) {
      try {
        const element = this.page.getByText(indicator.text).first();
        const count = await element.count();
        if (count > 0) {
          matchCount++;
          if (indicator.required) {
            console.log(`🔍 检测到登录页面特征: "${indicator.text}"`);
            return true;
          }
        }
      } catch (error) {
        // 继续检查
      }
    }

    // 如果匹配了2个以上特征,认为是登录页面
    if (matchCount >= 2) {
      console.log(`🔍 检测到多个登录页面特征 (${matchCount}个)`);
      return true;
    }

    // 方法1: 检查登录页面特征文本(但不包括单独的"登录"二字)
    for (const indicator of loginIndicators) {
      try {
        const element = this.page.getByText(indicator).first();
        const count = await element.count();
        if (count > 0) {
          console.log(`🔍 检测到登录特征文本: "${indicator}"`);
          return true;
        }
      } catch (error) {
        // 继续检查下一个特征
      }
    }

    // 方法2: 检查登录页面选择器
    for (const selector of loginSelectors) {
      try {
        const element = this.page.locator(selector).first();
        const count = await element.count();
        if (count > 0) {
          console.log(`🔍 检测到登录选择器: "${selector}"`);
          return true;
        }
      } catch (error) {
        // 继续检查下一个选择器
      }
    }

    // 方法3: 检查 URL 是否包含登录相关关键词
    const url = this.page.url();
    const loginUrlKeywords = ['/login', '/signin', '/auth', 'login', 'signin'];
    const hasLoginUrl = loginUrlKeywords.some(keyword =>
      url.toLowerCase().includes(keyword)
    );

    if (hasLoginUrl) {
      console.log(`🔍 检测到登录 URL: ${url}`);
      return true;
    }

    return false;
  }

  /**
   * 检测当前是否已登录
   * @param {Object} options - 检测选项
   * @param {string[]} options.loggedOutIndicators - 未登录特征
   * @returns {Promise<boolean>}
   */
  async isLoggedIn(options = {}) {
    const { loggedOutIndicators = [] } = options;

    // 如果检测到登录页面,则未登录
    const isLogin = await this.isLoginPage();
    if (isLogin) {
      return false;
    }

    // 检查是否有未登录的特征
    for (const indicator of loggedOutIndicators) {
      try {
        const element = this.page.getByText(indicator).first();
        const count = await element.count();
        if (count > 0) {
          console.log(`🔍 检测到未登录特征: "${indicator}"`);
          return false;
        }
      } catch (error) {
        // 继续检查
      }
    }

    return true;
  }

  /**
   * 检测登录成功的标志
   * 检查登录后的页面特征,如用户头像、输入框等
   * @param {Object} options - 检测选项
   * @returns {Promise<boolean>}
   */
  async isLoginSuccessful(options = {}) {
    const {
      successIndicators = [
        '给 DeepSeek 发送消息',
        '发送消息',
        'message',
        'input',
        'textarea'
      ]
    } = options;

    // 检查是否有登录成功的特征(如输入框、用户界面元素)
    for (const indicator of successIndicators) {
      try {
        // 查找输入框
        const textbox = this.page.getByRole('textbox', { name: indicator }).first();
        const count = await textbox.count();
        if (count > 0) {
          console.log(`✅ 检测到登录成功特征: 输入框 "${indicator}"`);
          return true;
        }
      } catch (error) {
        // 继续检查
      }
    }

    // 检查是否有任何可见的输入框
    try {
      const textboxes = this.page.locator('input[type="text"], textarea, [contenteditable="true"]');
      const count = await textboxes.count();
      if (count > 0) {
        console.log(`✅ 检测到 ${count} 个输入框,可能已登录`);
        return true;
      }
    } catch (error) {
      // 继续检查
    }

    return false;
  }

  /**
   * 确保已登录,如果未登录则执行登录操作
   * @param {Function} loginFunction - 自定义登录函数
   * @returns {Promise<boolean>} - 是否成功登录
   */
  async ensureLoggedIn(loginFunction) {
    const loggedIn = await this.isLoggedIn();

    if (loggedIn) {
      console.log('✅ 用户已登录');
      return true;
    }

    console.log('⚠️  用户未登录,正在尝试登录...');

    if (typeof loginFunction === 'function') {
      try {
        await loginFunction(this.page);
        console.log('✅ 登录成功');

        // 等待登录完成
        await this.page.waitForLoadState('networkidle');
        await this.page.waitForTimeout(2000);

        return true;
      } catch (error) {
        console.error('❌ 登录失败:', error.message);
        return false;
      }
    } else {
      console.error('❌ 未提供登录函数');
      return false;
    }
  }

  /**
   * 使用保存的认证状态文件登录
   * 注意: 这个方法需要在创建浏览器Context之前调用
   * 如果已经在运行中,建议使用 test.use({ storageState: 'auth.json' }) 在测试文件中
   * @param {string} authFilePath - 认证状态文件路径
   * @param {string} targetUrl - 目标 URL（默认: https://example.com）
   * @returns {Promise<boolean>}
   */
  async loginWithSavedState(authFilePath, targetUrl = 'https://example.com') {
    try {
      const fs = require('fs');
      if (!fs.existsSync(authFilePath)) {
        console.log(`[WARNING] 认证文件不存在: ${authFilePath}`);
        return false;
      }

      console.log('[INFO] 尝试使用认证状态...');

      // 方式1: 使用 Playwright 的官方 API (推荐)
      // 注意: 这个方法需要在 context 创建时设置,运行时设置可能不生效
      // 因此我们需要手动设置 cookies 和 localStorage
      const storageState = JSON.parse(fs.readFileSync(authFilePath, 'utf-8'));

      // 先导航到目标页面
      await this.page.goto(targetUrl, { waitUntil: 'domcontentloaded' });

      // 添加 cookies
      if (storageState.cookies && storageState.cookies.length > 0) {
        await this.page.context().addCookies([...storageState.cookies]);
        console.log(`[INFO] 已添加 ${storageState.cookies.length} 个 cookies`);
      }

      // 添加 localStorage
      if (storageState.origins && storageState.origins.length > 0) {
        for (const origin of storageState.origins) {
          if (origin.localStorage) {
            await this.page.evaluate((localStorageData) => {
              for (const item of localStorageData) {
                localStorage.setItem(item.name, item.value);
              }
            }, origin.localStorage);

            console.log(`[INFO] 已添加 ${origin.localStorage.length} 个 localStorage 项`);
          }
        }
      }

      // 重新加载页面
      await this.page.reload({ waitUntil: 'networkidle' });

      // 等待更长时间让页面完全加载
      await this.page.waitForTimeout(3000);

      // 验证是否登录成功
      const isLoggedIn = await this.isLoggedIn();
      if (isLoggedIn) {
        console.log('[OK] 使用保存的状态登录成功');
        return true;
      } else {
        console.log('[ERROR] 使用保存的状态登录失败 - 可能需要重新生成认证文件');
        console.log('[HINT] 运行: node scripts/setup-auth.js <target-url>');
        return false;
      }
    } catch (error) {
      console.error('[ERROR] 加载认证状态失败:', error.message);
      return false;
    }
  }

  /**
   * 等待跳转完成
   * 当页面可能跳转到登录页面时使用
   * @param {Object} options - 等待选项
   * @param {number} options.timeout - 超时时间(毫秒)
   * @param {string} options.waitUntil - 等待条件
   * @returns {Promise<boolean>} - 是否发生跳转
   */
  async waitForPossibleRedirect(options = {}) {
    const {
      timeout = 5000,
      waitUntil = 'domcontentloaded'
    } = options;

    try {
      // 等待可能的导航
      await this.page.waitForLoadState(waitUntil, { timeout });
      await this.page.waitForTimeout(1000); // 额外等待确保页面稳定

      // 检查是否跳转到了登录页
      const isLogin = await this.isLoginPage();
      if (isLogin) {
        console.log('⚠️  页面已跳转到登录页面');
        return true;
      }

      return false;
    } catch (error) {
      // 超时或其他错误
      return false;
    }
  }

  /**
   * 保存当前认证状态到文件
   * @param {string} authFilePath - 保存路径
   * @returns {Promise<boolean>}
   */
  async saveAuthState(authFilePath) {
    try {
      const fs = require('fs');
      const path = require('path');

      // 确保目录存在
      const dir = path.dirname(authFilePath);
      if (!fs.existsSync(dir)) {
        fs.mkdirSync(dir, { recursive: true });
      }

      // 保存认证状态
      await this.page.context().storageState({ path: authFilePath });
      console.log(`✅ 认证状态已保存到: ${authFilePath}`);
      return true;
    } catch (error) {
      console.error('❌ 保存认证状态失败:', error.message);
      return false;
    }
  }

  /**
   * 智能导航:自动处理登录页面的跳转
   * @param {string} url - 目标URL
   * @param {Object} options - 导航选项
   * @param {Function} options.onLogin - 检测到登录页时的回调
   * @returns {Promise<Object>} - 返回导航结果
   */
  async smartNavigate(url, options = {}) {
    const { onLogin, ...navigateOptions } = options;

    console.log(`🚀 正在导航到: ${url}`);

    // 导航到目标页面
    await this.page.goto(url, navigateOptions);

    // 等待页面稳定
    await this.page.waitForTimeout(2000);

    // 检查是否跳转到登录页
    const isLogin = await this.isLoginPage();

    if (isLogin) {
      console.log('⚠️  页面跳转到登录页面');

      // 如果提供了登录回调,执行登录
      if (typeof onLogin === 'function') {
        const loginSuccess = await onLogin(this.page);
        return {
          success: loginSuccess,
          requiredLogin: true,
          message: loginSuccess ? '已自动登录' : '登录失败'
        };
      }

      return {
        success: false,
        requiredLogin: true,
        message: '需要登录但未提供登录处理函数'
      };
    }

    return {
      success: true,
      requiredLogin: false,
      message: '导航成功,无需登录'
    };
  }

  /**
   * ✅ 新增: 检测是否为 OAuth/授权页面
   * @param {string} url - 要检查的 URL,默认为当前页面
   * @returns {boolean}
   */
  isAuthorizationPage(url = null) {
    const targetUrl = url || this.page.url();

    const authPagePatterns = [
      /\/auth\//i,
      /\/oauth\//i,
      /\/authorize/i,
      /\/login\/oauth/i,
      /accounts\.google\//,
      /github\.com\/login\/oauth/,
      /api\.auth0\.com/,
      /auth\.amazoncognito\.com/,
      /login\.microsoftonline\.com/,
      /weixin\.qq\.com/ // 微信授权
    ];

    return authPagePatterns.some(pattern => pattern.test(targetUrl));
  }

  /**
   * ✅ 新增: 等待 OAuth 授权流程完成
   * @param {Object} options - 选项
   * @param {number} options.timeout - 超时时间(毫秒),默认 30000
   * @param {string} options.expectedUrlPattern - 预期的最终 URL 模式
   * @returns {Promise<boolean>}
   */
  async waitForOAuthCompletion(options = {}) {
    const {
      timeout = 30000,
      expectedUrlPattern
    } = options;

    console.log('⏳ 等待 OAuth 授权完成...');

    try {
      // 等待 URL 变化(不再是授权页面)
      await this.page.waitForURL(
        url => !this.isAuthorizationPage(url),
        { timeout }
      );

      const finalUrl = this.page.url();
      console.log(`✅ OAuth 授权完成,当前 URL: ${finalUrl}`);

      // 如果提供了预期 URL 模式,验证是否匹配
      if (expectedUrlPattern) {
        const pattern = new RegExp(expectedUrlPattern);
        if (!pattern.test(finalUrl)) {
          console.warn(`⚠️ 最终 URL 不符合预期模式: ${expectedUrlPattern}`);
          return false;
        }
      }

      return true;
    } catch (error) {
      throw new Error(`OAuth 授权超时(${timeout}ms): ${error.message}`);
    }
  }

  /**
   * ✅ 新增: 验证最终页面状态
   * @param {Object} conditions - 验证条件
   * @param {RegExp[]} conditions.notUrlPatterns - 不应包含的 URL 模式
   * @param {string} conditions.expectedUrl - 预期的完整 URL
   * @param {RegExp} conditions.expectedUrlPattern - 预期的 URL 模式
   * @param {string[]} conditions.expectedElements - 预期存在的元素选择器
   * @returns {Promise<boolean>}
   */
  async verifyFinalPage(conditions = {}) {
    const {
      notUrlPatterns = [/\/login/i, /\/auth/i, /\/oauth/i, /\/signin/i],
      expectedUrl,
      expectedUrlPattern,
      expectedElements = []
    } = conditions;

    const actualUrl = this.page.url();

    // 1. 检查不在"错误页面"
    for (const pattern of notUrlPatterns) {
      if (pattern.test(actualUrl)) {
        throw new Error(`❌ 登录后仍在错误页面: ${actualUrl} (匹配模式: ${pattern})`);
      }
    }

    // 2. 检查完整 URL 是否匹配(如果提供)
    if (expectedUrl && actualUrl !== expectedUrl) {
      console.warn(`⚠️ URL 不匹配: 预期 ${expectedUrl}, 实际 ${actualUrl}`);
      // 注意: 这里不抛出错误,只是警告,因为可能有查询参数差异
    }

    // 3. 检查 URL 模式是否匹配
    if (expectedUrlPattern) {
      const pattern = expectedUrlPattern instanceof RegExp
        ? expectedUrlPattern
        : new RegExp(expectedUrlPattern);
      if (!pattern.test(actualUrl)) {
        throw new Error(`❌ URL 不符合预期模式: ${actualUrl} 不匹配 ${expectedUrlPattern}`);
      }
    }

    // 4. 检查页面元素是否存在
    if (expectedElements.length > 0) {
      for (const selector of expectedElements) {
        const count = await this.page.locator(selector).count();
        if (count === 0) {
          throw new Error(`❌ 页面缺少预期元素: ${selector}`);
        }
      }
    }

    console.log(`✅ 最终页面验证通过: ${actualUrl}`);
    return true;
  }

  /**
   * ✅ 新增: 暂停测试等待手动登录
   * @param {Object} options - 选项
   * @param {number} options.timeout - 超时时间(毫秒),默认 60000 (1分钟)
   * @param {boolean} options.showPrompt - 是否显示提示信息
   * @returns {Promise<Object>} - 登录结果
   */
  async pauseForManualLogin(options = {}) {
    const {
      timeout = 60000,
      showPrompt = true
    } = options;

    if (showPrompt) {
      console.log('');
      console.log('╔═══════════════════════════════════════════════════════╗');
      console.log('⏸️  自动认证失败,等待手动登录...');
      console.log(`💡 请在 ${timeout / 1000} 秒内完成登录操作`);
      console.log('╚═══════════════════════════════════════════════════════╝');
      console.log('');
    }

    const startTime = Date.now();
    let lastCheckedUrl = this.page.url();

    // 每秒检查一次登录状态
    while (Date.now() - startTime < timeout) {
      // 检查是否已登录
      if (await this.isLoggedIn()) {
        console.log('✅ 检测到手动登录成功');
        return {
          success: true,
          method: 'manual',
          duration: Date.now() - startTime
        };
      }

      // 检测 URL 变化(可能表示登录过程在进行)
      const currentUrl = this.page.url();
      if (currentUrl !== lastCheckedUrl) {
        console.log(`🔄 页面跳转: ${currentUrl}`);
        lastCheckedUrl = currentUrl;
      }

      await this.page.waitForTimeout(1000);
    }

    // 超时
    console.error('❌ 手动登录超时');
    return {
      success: false,
      method: 'manual',
      error: '等待超时',
      duration: timeout
    };
  }

  /**
   * ✅ 新增: 智能认证(降级策略)
   * 依次尝试多种认证方式,直到成功或耗尽所有选项
   * @param {Object} options - 认证选项
   * @returns {Promise<Object>} - 认证结果
   */
  async ensureAuthenticated(options = {}) {
    const {
      authFile = 'auth.json',
      autoLoginFunction = null,
      allowManualLogin = true,
      manualLoginTimeout = 60000,
      skipIfAllFail = true
    } = options;

    const attempts = [];
    let finalResult = null;

    console.log('🔐 开始智能认证流程...');
    console.log(`   策略: 认证文件 → 自动登录 → 手动登录 → ${skipIfAllFail ? '跳过测试' : '抛出错误'}`);

    // 方案1: 尝试使用认证文件
    console.log('\n📁 方案 1/3: 尝试使用认证文件...');
    const fileResult = await this.tryAuthFile(authFile);
    attempts.push({ method: 'auth-file', ...fileResult });

    if (fileResult.success) {
      console.log('✅ 认证文件登录成功');
      return {
        success: true,
        method: 'auth-file',
        attempts
      };
    }

    // 方案2: 尝试自动登录
    console.log('\n🤖 方案 2/3: 尝试自动登录...');
    const autoResult = await this.tryAutoLogin(autoLoginFunction);
    attempts.push({ method: 'auto-login', ...autoResult });

    if (autoResult.success) {
      console.log('✅ 自动登录成功');
      return {
        success: true,
        method: 'auto-login',
        attempts
      };
    }

    // 方案3: 手动登录
    if (allowManualLogin) {
      console.log('\n👤 方案 3/3: 等待手动登录...');
      const manualResult = await this.pauseForManualLogin(manualLoginTimeout);
      attempts.push({ method: 'manual', ...manualResult });

      if (manualResult.success) {
        console.log('✅ 手动登录成功');
        return {
          success: true,
          method: 'manual',
          attempts
        };
      }
    }

    // 所有方案都失败
    console.error('\n❌ 所有认证方式均失败');
    finalResult = {
      success: false,
      error: '无法完成认证',
      attempts
    };

    if (skipIfAllFail) {
      console.log('⏭️  跳过测试(使用 test.skip(true, message))');
      finalResult.action = 'skip';
    } else {
      finalResult.action = 'fail';
    }

    return finalResult;
  }

  /**
   * 内部方法: 尝试使用认证文件
   * @private
   */
  async tryAuthFile(authFilePath) {
    try {
      const success = await this.loginWithSavedState(authFilePath);
      return {
        success,
        message: success ? '认证文件有效' : '认证文件无效或已过期'
      };
    } catch (error) {
      return {
        success: false,
        message: `认证文件加载失败: ${error.message}`
      };
    }
  }

  /**
   * 内部方法: 尝试自动登录
   * @private
   */
  async tryAutoLogin(loginFunction = null) {
    // 如果提供了登录函数,使用它
    if (typeof loginFunction === 'function') {
      try {
        await loginFunction(this.page);
        const isLoggedIn = await this.isLoggedIn();
        return {
          success: isLoggedIn,
          message: isLoggedIn ? '自动登录成功' : '自动登录后验证失败'
        };
      } catch (error) {
        return {
          success: false,
          message: `自动登录失败: ${error.message}`
        };
      }
    }

    // 否则尝试从环境变量读取凭据
    const credentials = this.getCredentialsFromEnv();
    if (!credentials) {
      return {
        success: false,
        message: '未提供登录函数且未设置环境变量凭据'
      };
    }

    // 这里可以集成 LoginPage 的自动登录
    // 但为了避免循环依赖,暂时返回 false
    return {
      success: false,
      message: '需要手动实现自动登录逻辑或提供登录函数'
    };
  }

  /**
   * 内部方法: 从环境变量读取登录凭据
   * @private
   */
  getCredentialsFromEnv() {
    const credentials = {};

    // 检查手机号登录
    if (process.env.AUTH_PHONE && process.env.AUTH_CODE) {
      credentials.phone = process.env.AUTH_PHONE;
      credentials.code = process.env.AUTH_CODE;
    }

    // 检查用户名密码登录
    if (process.env.AUTH_USERNAME && process.env.AUTH_PASSWORD) {
      credentials.username = process.env.AUTH_USERNAME;
      credentials.password = process.env.AUTH_PASSWORD;
    }

    return Object.keys(credentials).length > 0 ? credentials : null;
  }
}

module.exports = AuthHelper;
