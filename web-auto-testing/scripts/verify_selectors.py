#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
验证 Playwright 测试文件中的选择器正确性
检查是否使用了 ref 属性、多元素匹配等问题

Usage:
    # 验证测试文件
    python scripts/verify_selectors.py tests/search.spec.js

    # 验证单个选择器
    python scripts/verify_selectors.py --selector 'input[placeholder*="姓名"]' --url http://localhost:3000

    # 自动修复建议
    python scripts/verify_selectors.py tests/search.spec.js --fix
"""

import argparse
import sys
import re
import io

# 设置标准输出编码为 UTF-8（兼容 Windows）
if sys.platform == 'win32':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# 问题模式
ISSUES = {
    'ref_attribute': {
        'pattern': r'\[ref="e\d+"\]',
        'severity': 'ERROR',
        'message': '使用了 ref 属性（只在 MCP 快照中存在）',
        'fix': '转换为标准选择器：getByRole(), locator(selector)'
    },
    'text_selector_vague': {
        'pattern': r'\.locator\([\'"]text=',
        'severity': 'WARNING',
        'message': '文本选择器可能匹配多个元素',
        'fix': '使用 .first() 或更具体的选择器'
    },
    'wait_for_timeout': {
        'pattern': r'\.waitForTimeout\(\s*\d{4,}',
        'severity': 'WARNING',
        'message': '使用了长时间固定延迟（>1秒）',
        'fix': '使用明确的等待条件：waitForSelector(), expect().toBeVisible()'
    },
    'no_networkidle': {
        'pattern': r'await page\.goto\([^)]+\)[\s\n]*(?!.*waitForLoadState)',
        'severity': 'INFO',
        'message': '动态页面建议等待 networkidle',
        'fix': '添加: await page.waitForLoadState("networkidle")'
    },
    # ===== 新增：API 误用检测 =====
    'frame_locator_wait_for_load_state': {
        'pattern': r'frameLocator\([^)]+\)\.waitForLoadState\(',
        'severity': 'ERROR',
        'message': 'FrameLocator 不支持 waitForLoadState() 方法',
        'fix': '获取 Frame 对象后调用：const frame = page.frame(selector); await frame.waitForLoadState()'
    },
    'frame_locator_wait_for_timeout': {
        'pattern': r'frameLocator\([^)]+\)\.waitForTimeout\(',
        'severity': 'ERROR',
        'message': 'FrameLocator 不支持 waitForTimeout() 方法',
        'fix': '使用 page.waitForTimeout() 代替：await page.waitForTimeout(500)'
    },
    'frame_locator_wait_for_selector': {
        'pattern': r'frameLocator\([^)]+\)\.waitForSelector\(',
        'severity': 'ERROR',
        'message': 'FrameLocator 不支持 waitForSelector() 方法',
        'fix': '使用 page.waitForSelector() 或获取 Frame 对象后调用'
    },
    'frame_locator_wait_for': {
        'pattern': r'frameLocator\([^)]+\)\.waitFor\(',
        'severity': 'ERROR',
        'message': 'FrameLocator 不支持 waitFor() 方法',
        'fix': '使用 expect().toBeVisible() 等断言方法'
    },
    # 检测：frameLocator() 返回值（通常命名为 iframe）后跟不支持的 API
    'frame_locator_variable_misuse': {
        'pattern': r'(iframe|frameLocator)\.(waitFor|expect)',
        'severity': 'ERROR',
        'message': 'FrameLocator 变量不支持 waitFor/expect 方法',
        'fix': 'FrameLocator 只用于定位元素，使用 page.waitForXxx() 或 expect(iframe.locator()).xxx()'
    },
    # 检测：直接 chain 调用 frameLocator().waitForXxx()
    'frame_locator_chain_misuse': {
        'pattern': r'page\.frameLocator\([^)]+\)\.waitFor',
        'severity': 'ERROR',
        'message': 'frameLocator() 返回 FrameLocator，不支持 waitForXxx() 方法',
        'fix': '正确写法：const frame = page.frame(selector); await frame.waitForLoadState()'
    }
}


def check_file(file_path):
    """检查测试文件"""
    print(f"[CHECK] 正在检查文件: {file_path}\n")

    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
    except FileNotFoundError:
        print(f"[ERROR] 文件不存在: {file_path}")
        return []

    issues_found = []

    for issue_name, issue_info in ISSUES.items():
        matches = re.finditer(issue_info['pattern'], content, re.MULTILINE)
        for match in matches:
            # 获取匹配行的上下文
            lines = content[:match.start()].split('\n')
            line_num = len(lines)
            line_content = lines[-1] if lines else ''

            issues_found.append({
                'type': issue_name,
                'severity': issue_info['severity'],
                'message': issue_info['message'],
                'fix': issue_info['fix'],
                'line': line_num,
                'context': line_content.strip(),
                'match': match.group()
            })

    return issues_found


def print_issues(issues):
    """打印发现的问题"""
    if not issues:
        print("[OK] 未发现问题")
        return

    print(f"[WARNING] 发现 {len(issues)} 个问题:\n")

    for i, issue in enumerate(issues, 1):
        icon = {
            'ERROR': '[ERROR]',
            'WARNING': '[WARNING]',
            'INFO': '[INFO]'
        }.get(issue['severity'], '•')

        print(f"{icon} 问题 {i}: {issue['message']}")
        print(f"   位置: 第 {issue['line']} 行")
        print(f"   代码: {issue['context']}")
        print(f"   匹配: {issue['match']}")
        print(f"   修复: {issue['fix']}")
        print()


def generate_fix_suggestions(issues):
    """生成修复建议"""
    suggestions = []

    for issue in issues:
        if issue['type'] == 'ref_attribute':
            suggestions.append({
                'line': issue['line'],
                'original': issue['match'],
                'suggested': '使用标准选择器替代',
                'example': "page.getByRole('textbox', { name: /姓名/ })"
            })

    return suggestions


def main():
    parser = argparse.ArgumentParser(description='验证 Playwright 测试选择器')
    parser.add_argument('file', nargs='?', help='测试文件路径')
    parser.add_argument('--selector', help='验证单个选择器')
    parser.add_argument('--url', help='页面 URL（用于验证单个选择器）')
    parser.add_argument('--fix', action='store_true', help='显示修复建议')

    args = parser.parse_args()

    if args.selector:
        print(f"[CHECK] 验证选择器: {args.selector}")
        if '[ref="' in args.selector:
            print("[ERROR] 错误: 选择器包含 ref 属性")
            print("   ref 属性只在 MCP 快照中存在，实际测试中不可用")
            print("   建议: 使用标准 HTML 属性")
            return 1
        else:
            print("[OK] 选择器格式正确")
            if args.url:
                print(f"   提示: 使用 npx playwright codegen {args.url} 验证")
            return 0

    if not args.file:
        parser.print_help()
        return 1

    issues = check_file(args.file)
    print_issues(issues)

    if args.fix and issues:
        print("\n🔧 修复建议:")
        print("=" * 60)
        suggestions = generate_fix_suggestions(issues)
        for suggestion in suggestions:
            print(f"第 {suggestion['line']} 行:")
            print(f"  原代码: {suggestion['original']}")
            print(f"  建议: {suggestion['suggested']}")
            print(f"  示例: {suggestion['example']}")
            print()

    # 返回退出码
    error_count = sum(1 for i in issues if i['severity'] == 'ERROR')
    return 1 if error_count > 0 else 0


if __name__ == '__main__':
    sys.exit(main())
