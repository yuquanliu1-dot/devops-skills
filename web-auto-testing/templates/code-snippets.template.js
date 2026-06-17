// Playwright 代码片段模板
// 常用代码模板，帮助快速编写稳定的测试代码

// 元素等待模板
async function waitForElement(page, selector, options = {}) {
  const {
    timeout = 10000,
    waitAfter = 300,
    checkVisibility = false
  } = options;

  await expect(selector).toBeAttached({ timeout });
  await page.waitForTimeout(waitAfter);

  if (checkVisibility && !process.env.CI) {
    await expect(selector).toBeVisible();
  }

  return selector;
}

// 安全点击模板
async function safeClick(page, selector, options = {}) {
  const {
    retries = 3,
    waitBefore = 0,
    waitAfter = 300
  } = options;

  if (waitBefore > 0) {
    await page.waitForTimeout(waitBefore);
  }

  for (let i = 0; i < retries; i++) {
    try {
      await selector.click({ timeout: 5000 });
      await page.waitForTimeout(waitAfter);
      return;
    } catch (error) {
      if (i === retries - 1) throw error;
      console.log(`点击失败，重试 ${i + 1}/${retries}`);
      await page.waitForTimeout(500);
    }
  }
}

// Element UI 下拉框操作模板
async function selectElementUIDropdown(page, dropdownIndex, optionText) {
  const iframe = page.frameLocator('#content-frame');
  const dropdown = iframe.locator('.el-select').nth(dropdownIndex);

  await dropdown.click();
  await page.waitForTimeout(300);

  await iframe.getByText(optionText).first().click();
  await page.waitForTimeout(300);

  await expect(iframe.getByText(optionText).first()).toBeAttached();
}

// Ant Design 下拉框操作模板
async function selectAntDesignDropdown(page, dropdownIndex, optionText) {
  const dropdown = page.locator('.ant-select').nth(dropdownIndex);

  await dropdown.click();
  await page.waitForTimeout(300);

  await page.locator('.ant-select-item-option').filter({ hasText: optionText }).click();
  await page.waitForTimeout(300);

  await expect(page.getByText(optionText).first()).toBeAttached();
}

// 组合等待策略模板
async function robustClick(page, selector) {
  // 1. 等待元素存在
  await expect(selector).toBeAttached({ timeout: 10000 });

  // 2. 点击
  await selector.click();

  // 3. 等待Vue/React渲染
  await page.waitForTimeout(300);

  // 4. 验证结果
  await expect(page.getByText('成功')).toBeAttached();
}

// CI 环境感知断言模板
async function assertVisibility(page, selector, isCI = process.env.CI === 'true') {
  if (isCI) {
    await expect(selector).toBeAttached();
  } else {
    await expect(selector).toBeVisible();
  }
}

// 原生 HTML 下拉框操作模板
async function selectNativeDropdown(page, selectId, optionText) {
  // 使用 id 定位原生 select 元素
  const select = page.locator(`#${selectId}`);

  // 使用 selectOption 方法（原生 HTML 专用）
  await select.selectOption(optionText);
  await page.waitForTimeout(300);

  // 验证选择成功
  const selectedValue = await select.inputValue();
  expect(selectedValue).toBe(optionText);
}

// iframe 内原生下拉框操作模板
async function selectNativeDropdownInIframe(page, iframeId, selectId, optionText) {
  const iframe = page.frameLocator(`#${iframeId}`);
  const select = iframe.locator(`#${selectId}`);

  await select.selectOption(optionText);
  await page.waitForTimeout(300);

  // 验证结果文本
  await expect(iframe.getByText(optionText)).toBeAttached();
}

// 前端筛选等待模板
async function waitForFrontendFilter(page, resultText) {
  // 等待 DOM 更新（不是网络请求）
  await page.waitForLoadState('domcontentloaded');

  // 验证筛选结果文本出现
  await expect(page.getByText(resultText)).toBeAttached();
}

// 分页操作模板
async function navigateToPage(page, pageNumber) {
  // 点击下一页直到到达目标页
  for (let i = 1; i < pageNumber; i++) {
    const nextButton = page.getByRole('button', { name: '下一页' });

    // 检查是否已禁用
    const isDisabled = await nextButton.isDisabled();
    if (isDisabled) {
      throw new Error(`无法到达第 ${pageNumber} 页，已在最后一页`);
    }

    await nextButton.click();
    await page.waitForTimeout(300);
  }

  // 验证到达目标页
  await expect(page.getByText(`第 ${pageNumber} 页`)).toBeVisible();
}

// 分页断言模板
async function assertPagination(page, currentPage, totalPages) {
  // 验证分页信息
  await expect(page.getByText(`第 ${currentPage} 页，共 ${totalPages} 页`)).toBeVisible();

  // 验证按钮状态
  const prevButton = page.getByRole('button', { name: '上一页' });
  const nextButton = page.getByRole('button', { name: '下一页' });

  // 第一页时，上一页应禁用
  if (currentPage === 1) {
    await expect(prevButton).toBeDisabled();
  } else {
    await expect(prevButton).not.toBeDisabled();
  }

  // 最后一页时，下一页应禁用
  if (currentPage === totalPages) {
    await expect(nextButton).toBeDisabled();
  } else {
    await expect(nextButton).not.toBeDisabled();
  }
}

// 查找 iframe id 的实用工具
async function findIframeIds(page) {
  const iframeIds = await page.locator('iframe').evaluateAll(
    iframe => iframe.id || 'no-id'
  );
  return iframeIds;
}
