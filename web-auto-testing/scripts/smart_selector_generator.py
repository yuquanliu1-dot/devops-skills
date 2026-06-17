#!/usr/bin/env python3
"""
智能选择器生成器

功能：
1. 检测页面使用的UI框架
2. 为元素生成多层次选择器（遵循 Playwright 官方优先级）
3. 按优先级排序选择器
4. 生成符合业界最佳实践的测试代码

选择器优先级（参考 Playwright Official Best Practices）：
1. getByRole - 最稳定（推荐）
2. getByLabel - 表单专用
3. getByTestId - 测试专用
4. getByText - 需要修饰符（.first() 或 exact）
5. locator - 最后选择

使用：
    python scripts/smart_selector_generator.py --url http://example.com
    python scripts/smart_selector_generator.py --html file.html
"""

import argparse
import sys
from typing import List, Dict, Any

# 依赖检查
try:
    from bs4 import BeautifulSoup
except ImportError:
    print("错误: 需要安装 beautifulsoup4")
    print("请运行: pip install beautifulsoup4")
    sys.exit(1)


class UIFrameworkDetector:
    """UI框架检测器"""

    FRAMEWORKS = {
        'Element UI': [
            '.el-select',
            '.el-input',
            '.el-button',
            '.el-table'
        ],
        'Ant Design': [
            '.ant-select',
            '.ant-input',
            '.ant-btn',
            '.ant-table'
        ],
        'Vuetify': [
            '.v-select',
            '.v-input',
            '.v-btn',
            '.v-data-table'
        ],
        'Bootstrap': [
            '.form-select',
            '.form-control',
            '.btn',
            '.table'
        ]
    }

    @classmethod
    def detect_from_html(cls, html_content: str) -> str:
        """从HTML内容检测UI框架"""
        soup = BeautifulSoup(html_content, 'html.parser')

        scores = {}
        for framework, selectors in cls.FRAMEWORKS.items():
            score = 0
            for selector in selectors:
                # 移除点号，用于搜索class
                class_name = selector[1:]
                elements = soup.find_all(class_=class_name)
                score += len(elements)
            scores[framework] = score

        # 返回得分最高的框架
        if max(scores.values()) == 0:
            return 'Vanilla'

        return max(scores, key=scores.get)


class SelectorGenerator:
    """选择器生成器 - 遵循 Playwright 官方最佳实践"""

    # 选择器优先级（参考 Playwright Official Documentation）
    # Priority 1 (Best): getByRole, getByLabel, getByTestId
    # Priority 2 (Good): getByPlaceholder, getByText (with modifiers)
    # Priority 3 (Avoid): CSS selectors, XPath

    def __init__(self, framework: str = 'Vanilla'):
        self.framework = framework
        self.framework_patterns = self._get_framework_patterns(framework)

    def _get_framework_patterns(self, framework: str) -> Dict[str, str]:
        """获取框架特定的选择器模式"""
        patterns = {
            'Element UI': {
                'dropdown': '.el-select',
                'input': '.el-input__inner',
                'button': '.el-button',
                'table': '.el-table',
                'checkbox': '.el-checkbox',
                'radio': '.el-radio'
            },
            'Ant Design': {
                'dropdown': '.ant-select',
                'input': '.ant-input',
                'button': '.ant-btn',
                'table': '.ant-table',
                'checkbox': '.ant-checkbox',
                'radio': '.ant-radio'
            }
        }
        return patterns.get(framework, {})

    def generate_selectors(self, element_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """为元素生成多层次选择器（按优先级排序）"""

        selectors = []

        # ========== 优先级 1: getByRole（最稳定，强烈推荐）==========
        role = element_data.get('role')
        name = element_data.get('name') or element_data.get('aria_label')
        if role:
            if name:
                selectors.append({
                    'type': 'role',
                    'value': f'{role}[name="{name}"]',
                    'priority': 1,
                    'code': f"page.getByRole('{role}', {{ name: '{name}' }})",
                    'description': '✅ 推荐：语义化角色选择器'
                })
            else:
                selectors.append({
                    'type': 'role',
                    'value': role,
                    'priority': 1,
                    'code': f"page.getByRole('{role}')",
                    'description': '✅ 推荐：语义化角色选择器'
                })

        # ========== 优先级 1: getByLabel（表单专用）==========
        label = element_data.get('label')
        if label:
            selectors.append({
                'type': 'label',
                'value': label,
                'priority': 1,
                'code': f"page.getByLabel('{label}')",
                'description': '✅ 推荐：表单标签选择器'
            })

        # ========== 优先级 1: getByTestId（测试专用）==========
        test_id = element_data.get('test_id')
        if test_id:
            selectors.append({
                'type': 'testId',
                'value': test_id,
                'priority': 1,
                'code': f"page.getByTestId('{test_id}')",
                'description': '✅ 推荐：data-testid 选择器'
            })

        # ========== 优先级 2: getByPlaceholder（输入框）==========
        placeholder = element_data.get('placeholder')
        if placeholder:
            selectors.append({
                'type': 'placeholder',
                'value': placeholder,
                'priority': 2,
                'code': f"page.getByPlaceholder('{placeholder}')",
                'description': '✅ 可用：占位符选择器'
            })

        # ========== 优先级 2: getByText（需要修饰符）==========
        text = element_data.get('text')
        if text and len(text) < 50:  # 避免过长的文本
            # 使用 .first() 处理可能的多元素匹配
            selectors.append({
                'type': 'text',
                'value': text,
                'priority': 2,
                'code': f"page.getByText('{text}', {{ exact: true }}).first()",
                'description': '⚠️ 谨慎：文本选择器（已添加 .first() 防护）'
            })

        # ========== 优先级 3: locator（最后选择）==========
        # 仅当没有更好的选择器时才使用 CSS
        if not selectors:
            element_type = element_data.get('type')
            if element_type in self.framework_patterns:
                framework_class = self.framework_patterns[element_type]
                # 组件库选择器也需要 .first() 防护
                selectors.append({
                    'type': 'framework',
                    'value': framework_class,
                    'priority': 3,
                    'code': f"page.locator('{framework_class}').first()",
                    'description': '⚠️ 最后选择：框架组件选择器（已添加 .first()）'
                })

            css_selector = element_data.get('css_selector')
            if css_selector:
                selectors.append({
                    'type': 'css',
                    'value': css_selector,
                    'priority': 3,
                    'code': f"page.locator('{css_selector}').first()",
                    'description': '⚠️ 最后选择：CSS 选择器（已添加 .first()）'
                })

        return selectors

    def get_best_selector(self, element_data: Dict[str, Any]) -> Dict[str, Any]:
        """获取最佳选择器（按优先级返回）"""
        selectors = self.generate_selectors(element_data)

        if not selectors:
            raise ValueError(f"无法为元素生成选择器: {element_data}")

        # 返回优先级最高的选择器（priority 数值最小）
        return min(selectors, key=lambda x: x['priority'])


class TestCodeGenerator:
    """测试代码生成器 - 遵循业界最佳实践"""

    def __init__(self, framework: str = 'Vanilla', ci_mode: bool = True):
        self.framework = framework
        self.ci_mode = ci_mode
        self.selector_generator = SelectorGenerator(framework)

    def generate_click_code(
        self,
        element_data: Dict[str, Any],
        description: str = ""
    ) -> str:
        """生成点击操作的代码（使用明确等待）"""

        selector = self.selector_generator.get_best_selector(element_data)

        code = []
        code.append(f"  // {description or '点击元素'}")
        code.append(f"  await {selector['code']}.click();")

        # ✅ 使用明确的等待条件，而非固定延迟
        # 点击后等待页面稳定（可根据实际情况调整）
        code.append("  // 等待页面响应")
        code.append("  await page.waitForLoadState('domcontentloaded');")

        return "\n".join(code)

    def generate_fill_code(
        self,
        element_data: Dict[str, Any],
        value: str,
        description: str = ""
    ) -> str:
        """生成填表操作的代码"""

        selector = self.selector_generator.get_best_selector(element_data)

        code = []
        code.append(f"  // {description or '填写表单'}")
        code.append(f"  await {selector['code']}.fill('{value}');")

        # ✅ 填表后无需额外等待，下一步操作会自动等待

        return "\n".join(code)

    def generate_assertion_code(
        self,
        element_data: Dict[str, Any],
        assertion_type: str = 'attached',
        description: str = ""
    ) -> str:
        """生成断言代码"""

        selector = self.selector_generator.get_best_selector(element_data)

        code = []
        code.append(f"  // {description or '验证元素'}")

        # CI环境使用toBeAttached，本地使用toBeVisible
        if assertion_type == 'visible':
            if self.ci_mode:
                code.append(f"  await expect({selector['code']}).toBeAttached();")
            else:
                code.append(f"  await expect({selector['code']}).toBeVisible();")
        else:
            code.append(f"  await expect({selector['code']}).toBeAttached();")

        return "\n".join(code)

    def generate_full_test(
        self,
        actions: List[Dict[str, Any]],
        test_name: str = "generated test"
    ) -> str:
        """生成完整的测试代码（遵循最佳实践）"""

        code = []
        code.append("const { test, expect } = require('@playwright/test');")
        code.append("")
        code.append(f"test('{test_name}', async ({ page }) => {{")
        code.append("  await page.goto('YOUR_URL_HERE');")
        code.append("")
        code.append("  // ✅ 等待页面稳定（优于固定延迟）")
        code.append("  await page.waitForLoadState('networkidle');")
        code.append("")

        # 生成每个操作的代码
        for action in actions:
            action_type = action['type']
            element_data = action['element']

            if action_type == 'click':
                code.append(self.generate_click_code(
                    element_data,
                    action.get('description')
                ))
            elif action_type == 'fill':
                code.append(self.generate_fill_code(
                    element_data,
                    action['value'],
                    action.get('description')
                ))
            elif action_type == 'assert':
                code.append(self.generate_assertion_code(
                    element_data,
                    action.get('assertion_type', 'attached'),
                    action.get('description')
                ))

            code.append("")

        code.append("});")

        return "\n".join(code)


def main():
    parser = argparse.ArgumentParser(
        description='智能选择器生成器 - 遵循 Playwright 最佳实践'
    )
    parser.add_argument('--url', help='要分析的URL')
    parser.add_argument('--html', help='HTML文件路径')
    parser.add_argument('--framework', help='指定UI框架 (Element UI, Ant Design, Vuetify, Vanilla)')
    parser.add_argument('--ci', action='store_true', help='CI模式（使用toBeAttached）')
    parser.add_argument('--output', help='输出文件路径')

    args = parser.parse_args()

    if not args.url and not args.html:
        print("错误: 必须提供 --url 或 --html 参数")
        sys.exit(1)

    # 检测UI框架
    framework = args.framework
    if not framework and args.html:
        with open(args.html, 'r', encoding='utf-8') as f:
            html_content = f.read()
        framework = UIFrameworkDetector.detect_from_html(html_content)
        print(f"检测到UI框架: {framework}")

    if not framework:
        framework = 'Vanilla'

    # 示例：生成测试代码
    generator = TestCodeGenerator(framework=framework, ci_mode=args.ci)

    # 示例操作（使用语义化选择器）
    sample_actions = [
        {
            'type': 'click',
            'element': {
                'role': 'combobox',
                'name': '研发类型',  # 使用 name 属性而非 text
                'type': 'dropdown'
            },
            'description': '点击研发类型下拉框'
        },
        {
            'type': 'click',
            'element': {
                'role': 'option',
                'name': '零低代码开发'  # 使用 role + name 组合
            },
            'description': '选择选项'
        }
    ]

    test_code = generator.generate_full_test(sample_actions)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(test_code)
        print(f"测试代码已保存到: {args.output}")
        print("\n注意：生成的代码遵循以下最佳实践：")
        print("  ✅ 优先使用 getByRole() 语义化选择器")
        print("  ✅ 对可能多元素匹配的选择器自动添加 .first()")
        print("  ✅ 使用明确的等待条件而非固定延迟")
        print("  ✅ 选择器优先级：getByRole > getByLabel > getByTestId > getByText > locator")
    else:
        print(test_code)


if __name__ == '__main__':
    main()
