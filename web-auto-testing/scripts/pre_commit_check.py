#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
预提交检查脚本
集成静态验证、选择器质量检查、smoke 测试

Usage:
    # 检查当前目录的 tests 文件夹
    python scripts/pre_commit_check.py

    # 指定测试目录
    python scripts/pre_commit_check.py path/to/tests

    # 仅运行静态验证
    python scripts/pre_commit_check.py --static-only

Exit Codes:
    0 - 所有检查通过
    1 - 有错误阻止提交
    2 - 有警告但可以提交
"""

import argparse
import glob
import os
import subprocess
import sys
from pathlib import Path
from typing import List, Tuple

# Windows UTF-8 兼容
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


class Colors:
    """终端颜色"""
    RED = '\033[31m'
    GREEN = '\033[32m'
    YELLOW = '\033[33m'
    CYAN = '\033[36m'
    RESET = '\033[0m'


def print_header(text: str):
    """打印标题"""
    print(f"\n{Colors.CYAN}{text}{Colors.RESET}")


def print_success(text: str):
    """打印成功消息"""
    print(f"  {Colors.GREEN}✅ {text}{Colors.RESET}")


def print_warning(text: str):
    """打印警告消息"""
    print(f"  {Colors.YELLOW}⚠️  {text}{Colors.RESET}")


def print_error(text: str):
    """打印错误消息"""
    print(f"  {Colors.RED}❌ {text}{Colors.RESET}")


def run_check(name: str, command: List[str], allow_failure: bool = False) -> Tuple[int, str]:
    """运行检查命令"""
    print_header(f"[{name}]")
    print(f"运行: {' '.join(command)}")

    try:
        result = subprocess.run(
            command,
            capture_output=True,
            text=True,
            timeout=60
        )
        return result.returncode, result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        return 1, "命令超时"
    except FileNotFoundError:
        return 1, "命令未找到"


def static_validation(test_dir: str) -> Tuple[bool, bool]:
    """静态验证检查
    返回: (has_errors, has_warnings)
    """
    print_header("[1/3] 静态验证检查")

    script_path = Path(__file__).parent / "verify_selectors.py"
    test_files = glob.glob(os.path.join(test_dir, "*.spec.js"))

    if not test_files:
        print_warning("未找到测试文件 (*.spec.js)")
        return False, False

    has_errors = False
    has_warnings = False

    for test_file in test_files:
        code, output = run_check(
            "验证",
            [sys.executable, str(script_path), test_file]
        )

        # 分析输出
        error_count = output.count('[ERROR]') if output else 0
        warning_count = output.count('[WARNING]') if output else 0

        if error_count > 0:
            print_error(f"✗ {os.path.basename(test_file)} - {error_count} 个错误")
            for line in output.split('\n'):
                if '[ERROR]' in line:
                    print(f"      {line.strip()}")
            has_errors = True
        elif warning_count > 0:
            print_warning(f"⚠ {os.path.basename(test_file)} - {warning_count} 个警告")
            has_warnings = True
        else:
            print_success(f"✓ {os.path.basename(test_file)}")

    return has_errors, has_warnings


def quality_check(test_dir: str) -> bool:
    """选择器质量检查（警告不禁止）"""
    print_header("[2/3] 选择器质量检查")

    script_path = Path(__file__).parent / "analyze_selector_quality.py"
    test_files = glob.glob(os.path.join(test_dir, "*.spec.js"))

    if not test_files:
        print_warning("未找到测试文件 (*.spec.js)")
        return True

    has_warning = False
    for test_file in test_files:
        code, output = run_check(
            "质量分析",
            [sys.executable, str(script_path), test_file]
        )

        # 提取平均分数
        avg_score = 0
        for line in output.split('\n'):
            if '平均分数:' in line:
                try:
                    avg_score = float(line.split(':')[1].split('/')[0].strip())
                except:
                    pass

        if avg_score >= 6:
            print_success(f"✓ {os.path.basename(test_file)} ({avg_score}/10)")
        else:
            print_warning(f"⚠ {os.path.basename(test_file)} ({avg_score}/10)")
            has_warning = True

    return not has_warning


def smoke_test(test_dir: str) -> bool:
    """快速 Smoke 测试"""
    print_header("[3/3] 快速 Smoke 测试")

    # 检查 Playwright 是否安装
    try:
        subprocess.run(
            ["npx", "--version"],
            capture_output=True,
            check=True,
            timeout=10
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print_warning("未找到 Playwright，跳过测试")
        return True

    # 运行 smoke 测试
    code, output = run_check(
        "Smoke 测试",
        ["npx", "playwright", "test", "--grep", "@smoke", "--reporter=line"],
        allow_failure=False
    )

    if code == 0:
        print_success("Smoke 测试通过")
        return True
    else:
        print_error("Smoke 测试失败")
        print("    运行以下命令查看详情:")
        print("      npx playwright test --grep @smoke")
        return False


def main():
    parser = argparse.ArgumentParser(
        description='预提交检查 - 验证代码质量后再提交'
    )
    parser.add_argument(
        'test_dir',
        nargs='?',
        default='tests',
        help='测试目录路径（默认: tests）'
    )
    parser.add_argument(
        '--static-only',
        action='store_true',
        help='仅运行静态验证'
    )

    args = parser.parse_args()

    # 检查测试目录
    test_dir = args.test_dir
    if not os.path.exists(test_dir):
        print_error(f"测试目录不存在: {test_dir}")
        return 1

    print()
    print("=" * 60)
    print(" 🔍 预提交检查")
    print("=" * 60)
    print(f" 📁 测试目录: {test_dir}")
    print()

    # 运行检查
    errors = []
    warnings = []

    # 检查 1: 静态验证
    has_errors, has_warnings = static_validation(test_dir)
    if has_errors:
        errors.append("静态验证失败")
    if has_warnings:
        warnings.append("静态验证发现问题")

    # 检查 2: 选择器质量
    if not args.static_only:
        if not quality_check(test_dir):
            warnings.append("选择器质量不达标（平均分 < 6）")

        # 检查 3: Smoke 测试
        if not smoke_test(test_dir):
            errors.append("Smoke 测试失败")

    # 总结
    print()
    print("=" * 60)
    print(" 📊 检查总结")
    print("=" * 60)

    if errors:
        print_error("发现错误，请修复后重试:")
        for error in errors:
            print(f"   - {error}")
        print()
        print("=" * 60)
        return 1

    if warnings:
        print_warning("有警告，但可以提交:")
        for warning in warnings:
            print(f"   - {warning}")
        print()
        print("=" * 60)
        return 2

    print_success("所有检查通过，可以提交！")
    print()
    print("=" * 60)
    return 0


if __name__ == '__main__':
    sys.exit(main())
