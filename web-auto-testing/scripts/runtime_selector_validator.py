#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
运行时选择器验证器
实际访问页面并验证选择器是否能正确匹配元素

Features:
    1. 解析测试文件中的选择器
    2. 启动浏览器访问目标页面
    3. 逐个验证选择器（存在性、唯一性、可见性）
    4. 检测 Strict Mode Violation（多元素匹配）
    5. 验证 iframe 中的选择器
    6. 生成详细报告

Usage:
    # 验证测试文件（自动提取 URL 和选择器）
    python runtime_selector_validator.py tests/tool-download.spec.js

    # 指定 URL 和测试文件
    python runtime_selector_validator.py tests/tool-download.spec.js --url http://example.com

    # 仅验证特定选择器类型
    python runtime_selector_validator.py tests/tool-download.spec.js --types getByRole,getByLabel

    # 输出 JSON 报告
    python runtime_selector_validator.py tests/tool-download.spec.js --json report.json

Reference:
    - Playwright Best Practices: https://playwright.dev/docs/best-practices
    - Selector Best Practices: https://playwright.dev/docs/selectors
"""

import argparse
import ast
import json
import re
import sys
import asyncio
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
from collections import defaultdict

# Playwright API
try:
    from playwright.async_api import async_playwright, Browser, Page, Locator, BrowserContext
except ImportError:
    print("[ERROR] 需要安装 Playwright: pip install playwright")
    print("       然后运行: playwright install")
    sys.exit(1)

# Windows UTF-8 兼容
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# ============================================================================
# 选择器解析器
# ============================================================================

class SelectorExtractor(ast.NodeVisitor):
    """从 JavaScript 测试代码中提取选择器"""

    def __init__(self):
        self.selectors = []
        self.base_url = None
        self.current_line = 0

    def extract(self, code: str) -> List[Dict]:
        """提取所有选择器"""
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            print(f"[WARNING] 无法解析代码: {e}")
            return []

        self.selectors = []
        self.visit(tree)
        return self.selectors

    def visit_Call(self, node):
        # 记录行号
        self.current_line = node.lineno

        # 提取 page.goto() 中的 URL
        if isinstance(node.func, ast.Attribute):
            if (hasattr(node.func.value, 'id') and
                node.func.value.id == 'page' and
                node.func.attr == 'goto'):
                if node.args and isinstance(node.args[0], ast.Constant):
                    self.base_url = node.args[0].value

        # 提取选择器调用
        selector = self._extract_selector_from_call(node)
        if selector:
            self.selectors.append(selector)

        self.generic_visit(node)

    def _extract_selector_from_call(self, node) -> Optional[Dict]:
        """从函数调用中提取选择器"""
        if not isinstance(node.func, ast.Attribute):
            return None

        # getByRole, getByLabel, getByText, locator 等
        method = node.func.attr

        # 检查是否是选择器方法
        selector_methods = {
            'getByRole', 'getByLabel', 'getByPlaceholder', 'getByText',
            'getByTestId', 'getByTitle', 'locator', 'frameLocator'
        }

        if method not in selector_methods:
            return None

        # 提取选择器参数
        selector_info = {
            'method': method,
            'line': self.current_line,
            'args': [],
            'is_frame': method == 'frameLocator'
        }

        # 获取调用链（如 page.getByRole 或 iframe.locator）
        if hasattr(node.func.value, 'id'):
            selector_info['caller'] = node.func.value.id
        elif hasattr(node.func.value, 'attr'):
            selector_info['caller'] = node.func.value.attr

        # 解析参数
        for arg in node.args:
            if isinstance(arg, ast.Constant):
                selector_info['args'].append({
                    'type': 'string',
                    'value': arg.value
                })
            elif isinstance(arg, (ast.Dict, ast.Call)):
                selector_info['args'].append({
                    'type': 'object',
                    'value': '<options>'
                })

        return selector_info


# ============================================================================
# 运行时验证器
# ============================================================================

class RuntimeValidator:
    """运行时选择器验证器"""

    def __init__(self, base_url: str, headless: bool = True):
        self.base_url = base_url
        self.headless = headless
        self.results = []
        self.stats = defaultdict(int)

    async def validate_all(self, selectors: List[Dict]) -> List[Dict]:
        """验证所有选择器"""
        async with async_playwright() as p:
            browser = await p.chromium.launch(headless=self.headless)
            context = await browser.new_context(viewport={'width': 1280, 'height': 720})
            page = await context.new_page()

            try:
                # 访问页面
                print(f"[INFO] 正在访问: {self.base_url}")
                await page.goto(self.base_url, wait_until='domcontentloaded', timeout=30000)

                # ✅ 等待页面稳定（优于固定延迟）
                try:
                    await page.wait_for_load_state('networkidle', timeout=5000)
                except Exception:
                    # 如果 networkidle 超时，至少等待 DOM 加载完成
                    await page.wait_for_load_state('domcontentloaded')

                # 逐个验证选择器
                for selector in selectors:
                    result = await self._validate_selector(page, selector)
                    self.results.append(result)
                    self._print_result(result)

            finally:
                await context.close()
                await browser.close()

        return self.results

    async def _validate_selector(self, page: Page, selector: Dict) -> Dict:
        """验证单个选择器"""
        method = selector['method']
        args = selector['args']
        line = selector['line']

        result = {
            'method': method,
            'args': args,
            'line': line,
            'status': 'unknown',
            'count': 0,
            'visible': 0,
            'message': '',
            'suggestion': ''
        }

        try:
            # 构建选择器
            locator = self._build_locator(page, selector)

            if locator is None:
                result['status'] = 'skip'
                result['message'] = '无法构建选择器（参数复杂）'
                self.stats['skip'] += 1
                return result

            # 检查元素数量
            count = await locator.count()
            result['count'] = count

            if count == 0:
                result['status'] = 'error'
                result['message'] = '未找到匹配元素'
                result['suggestion'] = '检查选择器是否正确，或使用 browserSnapshot 查看实际结构'
                self.stats['error'] += 1

            elif count == 1:
                # 唯一匹配 - 检查可见性
                is_visible = await locator.is_visible()
                result['visible'] = int(is_visible)

                if is_visible:
                    result['status'] = 'pass'
                    result['message'] = '找到 1 个可见元素'
                    self.stats['pass'] += 1
                else:
                    result['status'] = 'warning'
                    result['message'] = '找到 1 个元素但不可见'
                    result['suggestion'] = '元素可能被隐藏或等待加载'
                    self.stats['warning'] += 1

            else:
                # 多元素匹配 - Strict Mode Violation
                result['status'] = 'error'
                result['message'] = f'Strict Mode Violation: 找到 {count} 个元素'
                result['suggestion'] = '使用 .first()、.last() 或 .nth() 指定具体元素，或使用更精确的选择器'
                self.stats['strict_violation'] += 1

        except Exception as e:
            result['status'] = 'error'
            result['message'] = f'验证失败: {str(e)}'
            result['suggestion'] = '检查页面是否已加载，或选择器语法是否正确'
            self.stats['exception'] += 1

        return result

    def _build_locator(self, page: Page, selector: Dict) -> Optional[Locator]:
        """构建 Locator 对象"""
        method = selector['method']
        args = selector['args']

        if not args or args[0]['type'] != 'string':
            return None

        first_arg = args[0]['value']

        try:
            if method == 'getByRole':
                # getByRole('button', { name: 'xxx' })
                if len(args) >= 2:
                    return page.get_by_role(first_arg, name=args[1].get('value', ''))
                return page.get_by_role(first_arg)

            elif method == 'getByLabel':
                return page.get_by_label(first_arg)

            elif method == 'getByPlaceholder':
                return page.get_by_placeholder(first_arg)

            elif method == 'getByText':
                return page.get_by_text(first_arg)

            elif method == 'getByTestId':
                return page.get_by_test_id(first_arg)

            elif method == 'getByTitle':
                return page.get_by_title(first_arg)

            elif method == 'locator':
                return page.locator(first_arg)

            elif method == 'frameLocator':
                # frameLocator 需要特殊处理
                return page.frame_locator(first_arg)

        except Exception:
            return None

        return None

    def _print_result(self, result: Dict):
        """打印验证结果"""
        status_icons = {
            'pass': '✅',
            'warning': '⚠️ ',
            'error': '❌',
            'skip': '⏭️ '
        }

        icon = status_icons.get(result['status'], '•')
        args_str = ', '.join([a.get('value', str(a)) for a in result['args'][:2]])

        print(f"{icon} 第{result['line']}行: {result['method']}({args_str})")
        print(f"   状态: {result['message']}")

        if result['suggestion']:
            print(f"   建议: {result['suggestion']}")
        print()

    def print_summary(self):
        """打印验证摘要"""
        total = len(self.results)
        passed = self.stats.get('pass', 0)
        errors = self.stats.get('error', 0) + self.stats.get('strict_violation', 0)
        warnings = self.stats.get('warning', 0)

        print("\n" + "=" * 60)
        print("📊 验证摘要")
        print("=" * 60)
        print(f"总计:     {total} 个选择器")
        print(f"✅ 通过:   {passed} 个")
        print(f"⚠️  警告:   {warnings} 个")
        print(f"❌ 错误:   {errors} 个")
        print("=" * 60)

        # 问题详情
        if self.stats.get('strict_violation', 0) > 0:
            print(f"\n[注意] 发现 {self.stats['strict_violation']} 个 Strict Mode Violation")
            print("       这些选择器匹配多个元素，运行测试时会失败")
            print("       解决方案: 使用 .first() 或更精确的选择器")

    def get_json_report(self) -> Dict:
        """生成 JSON 报告"""
        return {
            'timestamp': datetime.now().isoformat(),
            'base_url': self.base_url,
            'summary': dict(self.stats),
            'results': self.results
        }


# ============================================================================
# 主程序
# ============================================================================

def extract_from_test_file(file_path: str) -> tuple:
    """从测试文件中提取 URL 和选择器"""
    with open(file_path, 'r', encoding='utf-8') as f:
        code = f.read()

    extractor = SelectorExtractor()
    selectors = extractor.extract(code)

    # 提取 BASE_URL（从常量定义中）
    url_match = re.search(r"const BASE_URL = ['\"]([^'\"]+)['\"]", code)
    base_url = url_match.group(1) if url_match else None

    return base_url, selectors


async def main():
    parser = argparse.ArgumentParser(
        description='运行时选择器验证器 - 实际访问页面验证选择器',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
    # 验证测试文件
    python runtime_selector_validator.py tests/tool-download.spec.js

    # 指定 URL
    python runtime_selector_validator.py tests/tool-download.spec.js --url http://example.com

    # 有头模式运行（可以看到浏览器）
    python runtime_selector_validator.py tests/tool-download.spec.js --headed

    # 输出 JSON 报告
    python runtime_selector_validator.py tests/tool-download.spec.js --json report.json

    # 仅验证特定类型
    python runtime_selector_validator.py tests/tool-download.spec.js --types getByRole,getByLabel
        """
    )

    parser.add_argument('file', help='Playwright 测试文件路径')
    parser.add_argument('--url', help='覆盖测试文件中的 URL')
    parser.add_argument('--headed', action='store_true', help='有头模式运行（显示浏览器）')
    parser.add_argument('--json', help='输出 JSON 报告到文件')
    parser.add_argument('--types', help='仅验证指定类型（逗号分隔）: getByRole,getByLabel等')

    args = parser.parse_args()

    # 检查文件存在
    if not Path(args.file).exists():
        print(f"[ERROR] 文件不存在: {args.file}")
        return 1

    print("=" * 60)
    print("🔍 运行时选择器验证器")
    print("=" * 60)
    print(f"测试文件: {args.file}")
    print(f"有头模式: {'是' if args.headed else '否'}")
    print()

    # 提取 URL 和选择器
    base_url, selectors = extract_from_test_file(args.file)

    # 使用命令行 URL 或从文件中提取
    target_url = args.url or base_url
    if not target_url:
        print("[ERROR] 未找到 URL，请使用 --url 指定")
        return 1

    # 过滤选择器类型
    if args.types:
        filter_types = set(args.types.split(','))
        selectors = [s for s in selectors if s['method'] in filter_types]

    if not selectors:
        print("[WARNING] 未找到可验证的选择器")
        return 0

    print(f"[INFO] 目标 URL: {target_url}")
    print(f"[INFO] 找到 {len(selectors)} 个选择器")
    print()

    # 执行验证
    validator = RuntimeValidator(target_url, headless=not args.headed)
    await validator.validate_all(selectors)

    # 打印摘要
    validator.print_summary()

    # 输出 JSON
    if args.json:
        with open(args.json, 'w', encoding='utf-8') as f:
            json.dump(validator.get_json_report(), f, indent=2, ensure_ascii=False)
        print(f"\n[INFO] JSON 报告已保存: {args.json}")

    # 返回退出码
    errors = validator.stats.get('error', 0) + validator.stats.get('strict_violation', 0)
    return 1 if errors > 0 else 0


if __name__ == '__main__':
    sys.exit(asyncio.run(main()))
