#!/usr/bin/env python3
"""
元素发现工具

用途：扫描页面并生成推荐的选择器
遵循 Playwright 最佳实践

最佳实践参考：
- Playwright Official: https://playwright.dev/docs/best-practices
- Airbnb Testing Guide: https://github.com/airbnb/enzyme

Usage:
    python scripts/element_discovery.py --url http://example.com
    python scripts/element_discovery.py --url http://example.com --output elements.json
"""

import argparse
import io
import json
import sys
from typing import List, Dict, Any
from playwright.sync_api import sync_playwright

# Windows UTF-8 兼容
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')


class ElementDiscoverer:
    """元素发现器 - 生成符合最佳实践的选择器"""

    def __init__(self, page):
        self.page = page

    def discover_buttons(self) -> List[Dict[str, Any]]:
        """发现所有按钮并生成推荐选择器"""
        elements = []

        # ✅ 使用语义化选择器（优先级最高）
        buttons = self.page.get_by_role('button').all()
        print(f"Found {len(buttons)} buttons:")

        for i, button in enumerate(buttons):
            try:
                text = button.inner_text() if button.is_visible() else "[hidden]"
                name_attr = button.get_attribute('name')
                aria_label = button.get_attribute('aria-label')

                # 生成推荐选择器（按优先级）
                selectors = []

                # 优先级1: getByRole + name
                if text and len(text) < 50:
                    selectors.append({
                        'type': 'role',
                        'code': f"page.getByRole('button', {{ name: '{text}' }})",
                        'priority': 1,
                        'recommended': True
                    })

                # 优先级2: getByLabel
                if aria_label:
                    selectors.append({
                        'type': 'label',
                        'code': f"page.getByLabel('{aria_label}')",
                        'priority': 2,
                        'recommended': True
                    })

                elements.append({
                    'index': i,
                    'text': text,
                    'visible': button.is_visible(),
                    'selectors': selectors
                })

                print(f"  [{i}] {text}")
                for sel in selectors:
                    if sel.get('recommended'):
                        print(f"      ✅ 推荐: {sel['code']}")
            except Exception as e:
                print(f"  [{i}] Error: {e}")

        return elements

    def discover_links(self) -> List[Dict[str, Any]]:
        """发现所有链接"""
        elements = []

        # ✅ 使用语义化选择器
        links = self.page.get_by_role('link').all()
        print(f"\nFound {len(links)} links:")

        for i, link in enumerate(links[:10]):  # 只显示前10个
            try:
                text = link.inner_text().strip() if link.is_visible() else "[hidden]"
                href = link.get_attribute('href')

                selectors = []

                # 优先级1: getByRole + name
                if text:
                    selectors.append({
                        'type': 'role',
                        'code': f"page.getByRole('link', {{ name: '{text}' }})",
                        'priority': 1,
                        'recommended': True
                    })

                elements.append({
                    'index': i,
                    'text': text,
                    'href': href,
                    'selectors': selectors
                })

                print(f"  - {text} -> {href}")
                if selectors and selectors[0].get('recommended'):
                    print(f"      ✅ {selectors[0]['code']}")
            except Exception as e:
                print(f"  Error: {e}")

        return elements

    def discover_inputs(self) -> List[Dict[str, Any]]:
        """发现所有输入框"""
        elements = []

        # ✅ 使用语义化选择器
        textboxes = self.page.get_by_role('textbox').all()
        print(f"\nFound {len(textboxes)} input fields:")

        for i, textbox in enumerate(textboxes):
            try:
                name = textbox.get_attribute('name')
                placeholder = textbox.get_attribute('placeholder')
                aria_label = textbox.get_attribute('aria-label')
                input_id = textbox.get_attribute('id')

                selectors = []

                # 优先级1: getByLabel
                if aria_label:
                    selectors.append({
                        'type': 'label',
                        'code': f"page.getByLabel('{aria_label}')",
                        'priority': 1,
                        'recommended': True
                    })

                # 优先级2: getByPlaceholder
                if placeholder:
                    selectors.append({
                        'type': 'placeholder',
                        'code': f"page.getByPlaceholder('{placeholder}')",
                        'priority': 2,
                        'recommended': True
                    })

                elements.append({
                    'index': i,
                    'name': name or input_id or "[unnamed]",
                    'placeholder': placeholder,
                    'selectors': selectors
                })

                print(f"  - {name or placeholder or input_id}")
                for sel in selectors:
                    if sel.get('recommended'):
                        print(f"      ✅ {sel['code']}")
            except Exception as e:
                print(f"  Error: {e}")

        return elements


def main():
    parser = argparse.ArgumentParser(
        description='元素发现工具 - 生成符合最佳实践的选择器'
    )
    parser.add_argument('--url', default='http://localhost:5173', help='要扫描的URL (默认: http://localhost:5173)')
    parser.add_argument('--output', help='输出JSON文件路径')
    parser.add_argument('--screenshot', help='截图保存路径')

    args = parser.parse_args()

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        page = browser.new_page()

        print(f"正在扫描: {args.url}")
        page.goto(args.url)

        # ✅ 等待页面稳定
        page.wait_for_load_state('networkidle')

        discoverer = ElementDiscoverer(page)

        results = {
            'url': args.url,
            'buttons': discoverer.discover_buttons(),
            'links': discoverer.discover_links(),
            'inputs': discoverer.discover_inputs()
        }

        # 保存截图
        if args.screenshot:
            page.screenshot(path=args.screenshot, full_page=True)
            print(f"\n截图已保存: {args.screenshot}")

        # 保存结果
        if args.output:
            with open(args.output, 'w', encoding='utf-8') as f:
                json.dump(results, f, indent=2, ensure_ascii=False)
            print(f"\n结果已保存: {args.output}")

        print("\n" + "="*50)
        print("✅ 扫描完成！")
        print("="*50)
        print("\n推荐选择器原则：")
        print("  1. 优先使用 getByRole() - 最稳定")
        print("  2. 表单元素使用 getByLabel()")
        print("  3. 测试专用使用 getByTestId()")
        print("  4. 文本选择器需要 .first() 或 exact: true")
        print("  5. CSS 选择器作为最后选择")

        browser.close()


if __name__ == '__main__':
    main()
