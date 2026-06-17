/**
 * 详情页面对象模板
 *
 * 用途：封装详情页面的所有元素和操作
 * 适用场景：商品详情、用户详情、文章详情等
 *
 * 使用方法：
 * 1. 复制此模板到 pages/DetailPage.js
 * 2. 根据实际页面修改选择器
 * 3. 在测试中导入并使用
 */

const { BasePage } = require('./BasePage');

class DetailPage extends BasePage {
  /**
   * 构造函数 - 定义详情页面的所有元素
   * @param {Page} page - Playwright Page 对象
   */
  constructor(page) {
    super(page);

    // 标题和基本信息
    this.title = page.locator('[data-testid="detail-title"]');
    this.subtitle = page.locator('[data-testid="detail-subtitle"]');
    this.description = page.locator('[data-testid="detail-description"]');
    this.badge = page.locator('[data-testid="detail-badge"]');

    // 图片和媒体
    this.mainImage = page.locator('[data-testid="main-image"]');
    this.imageGallery = page.locator('[data-testid="image-gallery"]');
    this.thumbnail = page.locator('[data-testid="thumbnail"]');

    // 操作按钮
    this.editButton = page.getByRole('button', { name: /编辑|edit/i });
    this.deleteButton = page.getByRole('button', { name: /删除|delete/i });
    this.backButton = page.getByRole('button', { name: /返回|back/i });
    this.shareButton = page.getByRole('button', { name: /分享|share/i });

    // 状态和标签
    this.statusBadge = page.locator('[data-testid="status-badge"]');
    this.tags = page.locator('[data-testid="tag"]');

    // 属性列表
    this.attributesSection = page.locator('[data-testid="attributes"]');
    this.attributeItem = page.locator('[data-testid="attribute-item"]');

    // 相关内容
    this.relatedSection = page.locator('[data-testid="related-content"]');
    this.relatedItems = page.locator('[data-testid="related-item"]');

    // 评论或反馈
    this.commentsSection = page.locator('[data-testid="comments"]');
    this.commentInput = page.locator('[data-testid="comment-input"]');
    this.submitCommentButton = page.getByRole('button', { name: /提交|submit/i });
  }

  /**
   * 导航到详情页
   * @param {string} id - 详情页 ID
   */
  async goto(id) {
    await super.goto(`/detail/${id}`);
    await this.waitForPageReady();
  }

  /**
   * 等待详情页加载完成
   */
  async waitForDetailLoaded() {
    await this.title.waitFor({ state: 'visible' });
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * 获取标题
   * @returns {Promise<string>} 标题文本
   */
  async getTitle() {
    await this.waitForDetailLoaded();
    return await this.getText(this.title);
  }

  /**
   * 获取副标题
   * @returns {Promise<string>} 副标题文本
   */
  async getSubtitle() {
    return await this.getText(this.subtitle);
  }

  /**
   * 获取描述
   * @returns {Promise<string>} 描述文本
   */
  async getDescription() {
    return await this.getText(this.description);
  }

  /**
   * 获取状态
   * @returns {Promise<string>} 状态文本
   */
  async getStatus() {
    return await this.getText(this.statusBadge);
  }

  /**
   * 获取所有标签
   * @returns {Promise<string[]>} 标签数组
   */
  async getTags() {
    const tags = [];
    const tagCount = await this.tags.count();
    for (let i = 0; i < tagCount; i++) {
      tags.push(await this.getText(this.tags.nth(i)));
    }
    return tags;
  }

  /**
   * 获取指定属性的值
   * @param {string} attributeName - 属性名称
   * @returns {Promise<string|null>} 属性值
   */
  async getAttribute(attributeName) {
    const attribute = this.attributeItem.filter({ hasText: attributeName });
    if (await attribute.count() > 0) {
      return await this.getText(attribute);
    }
    return null;
  }

  /**
   * 点击编辑按钮
   */
  async clickEdit() {
    await this.click(this.editButton);
  }

  /**
   * 点击删除按钮
   */
  async clickDelete() {
    await this.click(this.deleteButton);
  }

  /**
   * 点击返回按钮
   */
  async clickBack() {
    await this.click(this.backButton);
  }

  /**
   * 点击分享按钮
   */
  async clickShare() {
    await this.click(this.shareButton);
  }

  /**
   * 点击主图
   */
  async clickMainImage() {
    await this.click(this.mainImage);
  }

  /**
   * 点击缩略图
   * @param {number} index - 缩略图索引
   */
  async clickThumbnail(index) {
    await this.click(this.thumbnail.nth(index));
  }

  /**
   * 提交评论
   * @param {string} comment - 评论内容
   */
  async submitComment(comment) {
    await this.commentInput.fill(comment);
    await this.submitCommentButton.click();
    await this.page.waitForLoadState('networkidle');
  }

  /**
   * 获取相关内容项数量
   * @returns {Promise<number>} 相关项数量
   */
  async getRelatedItemsCount() {
    return await this.relatedItems.count();
  }

  /**
   * 点击相关内容项
   * @param {number} index - 相关项索引
   */
  async clickRelatedItem(index) {
    await this.click(this.relatedItems.nth(index));
  }

  /**
   * 检查页面是否包含指定文本
   * @param {string} text - 查找的文本
   * @returns {Promise<boolean>} 是否包含文本
   */
  async containsText(text) {
    return await this.page.getByText(text).count() > 0;
  }

  /**
   * 截取详情页面截图
   * @param {string} suffix - 文件名后缀
   */
  async captureScreenshot(suffix = 'detail-page') {
    await this.screenshot(`detail-${suffix}.png`);
  }

  /**
   * 滚动到评论区域
   */
  async scrollToComments() {
    await this.commentsSection.scrollIntoViewIfNeeded();
  }

  /**
   * 滚动到相关内容区域
   */
  async scrollToRelated() {
    await this.relatedSection.scrollIntoViewIfNeeded();
  }

  /**
   * 验证页面加载完成
   * @returns {Promise<boolean>} 是否加载完成
   */
  async isPageLoaded() {
    try {
      await this.title.waitFor({ state: 'visible', timeout: 5000 });
      return true;
    } catch {
      return false;
    }
  }

  /**
   * 等待图片加载完成
   */
  async waitForImagesLoaded() {
    await this.mainImage.waitFor({ state: 'attached' });
    // 等待图片自然宽度大于0（表示已加载）
    await this.page.waitForFunction(
      (selector) => {
        const img = document.querySelector(selector);
        return img && img.naturalWidth > 0;
      },
      {},
      '[data-testid="main-image"]'
    );
  }
}

module.exports = { DetailPage };
