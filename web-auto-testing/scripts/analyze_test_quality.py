#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
测试代码质量分析器
分析测试代码的复杂度、行数、重复度等

参考业界标准：
- Airbnb: 测试代码重复度 < 30%
- Google: 单个测试文件 < 300 行
- Microsoft: 圈复杂度 < 10

Usage:
    # 分析测试目录
    python scripts/analyze_test_quality.py tests/

    # 输出 JSON 报告
    python scripts/analyze_test_quality.py tests/ --json report.json

    # 设置阈值
    python scripts/analyze_test_quality.py tests/ --max-lines 300 --max-complexity 10
"""

import argparse
import ast
import json
import os
import re
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Tuple
from collections import defaultdict

# Windows UTF-8 兼容
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# ============================================================================
# 代码复杂度分析器
# ============================================================================

class CodeComplexityAnalyzer(ast.NodeVisitor):
    """分析代码复杂度"""

    def __init__(self):
        self.complexity = 0
        self.functions = []
        self.function_lines = []
        self.imports = []
        self.test_cases = 0
        self.describe_blocks = 0

    def analyze(self, code: str) -> Dict:
        """分析代码"""
        try:
            tree = ast.parse(code)
        except SyntaxError as e:
            return {
                'error': f'语法错误: {e}',
                'complexity': 999,
                'functions': 0,
                'test_cases': 0
            }

        self.complexity = 0
        self.visit(tree)

        return {
            'complexity': self.complexity,
            'functions': len(self.functions),
            'test_cases': self.test_cases,
            'describe_blocks': self.describe_blocks,
            'imports': len(self.imports)
        }

    def visit_FunctionDef(self, node):
        """访问函数定义"""
        self.complexity += 1
        self.functions.append(node.name)

        # 计算函数行数
        if hasattr(node, 'body') and node.body:
            start = node.lineno
            end = node.body[-1].lineno if hasattr(node.body[-1], 'lineno') else start
            self.function_lines.append(end - start + 1)

        # 分析函数体内的复杂度
        for child in ast.walk(node):
            if isinstance(child, (ast.If, ast.While, ast.For, ast.ExceptHandler)):
                self.complexity += 1

        self.generic_visit(node)

    def visit_Call(self, node):
        """访问函数调用"""
        # 检测 test() 调用
        if isinstance(node.func, ast.Name) and node.func.id == 'test':
            self.test_cases += 1

        # 检测 test.describe() 调用
        if isinstance(node.func, ast.Attribute) and node.func.attr == 'describe':
            self.describe_blocks += 1

        self.generic_visit(node)

    def visit_Import(self, node):
        """访问 import 语句"""
        for alias in node.names:
            self.imports.append(alias.name)
        self.generic_visit(node)

    def visit_ImportFrom(self, node):
        """访问 from ... import 语句"""
        self.imports.append(node.module)
        self.generic_visit(node)


# ============================================================================
# 重复度分析器
# ============================================================================

class DuplicationAnalyzer:
    """分析代码重复度"""

    def __init__(self):
        self.lines = []
        self.normalized_lines = []

    def analyze(self, code: str) -> Dict:
        """分析代码重复度"""
        lines = code.split('\n')
        self.lines = lines

        # 标准化行（移除空格、注释）
        normalized = []
        for line in lines:
            # 移除注释
            line = re.sub(r'//.*$', '', line)
            # 移除前后空格
            line = line.strip()
            # 跳过空行
            if line:
                normalized.append(line)

        self.normalized_lines = normalized

        # 计算重复行
        line_counts = defaultdict(int)
        for line in normalized:
            line_counts[line] += 1

        # 重复行数（出现 >1 次）
        duplicate_lines = sum(count - 1 for count in line_counts.values() if count > 1)
        total_lines = len(normalized)

        if total_lines == 0:
            duplication_rate = 0
        else:
            duplication_rate = duplicate_lines / total_lines

        return {
            'total_lines': total_lines,
            'duplicate_lines': duplicate_lines,
            'duplication_rate': round(duplication_rate * 100, 2),
            'most_common': self._get_most_common(line_counts, 5)
        }

    def _get_most_common(self, line_counts: Dict, top_n: int) -> List[Tuple[str, int]]:
        """获取最常见的行"""
        sorted_lines = sorted(line_counts.items(), key=lambda x: x[1], reverse=True)
        return sorted_lines[:top_n]


# ============================================================================
# 文件分析器
# ============================================================================

class FileAnalyzer:
    """分析单个测试文件"""

    def __init__(self, file_path: str, thresholds: Dict):
        self.file_path = file_path
        self.thresholds = thresholds
        self.issues = []

    def analyze(self) -> Dict:
        """执行分析"""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            code = f.read()

        # 基本信息
        lines = code.split('\n')
        total_lines = len(lines)
        code_lines = len([l for l in lines if l.strip() and not l.strip().startswith('//')])
        empty_lines = len([l for l in lines if not l.strip()])
        comment_lines = len([l for l in lines if l.strip().startswith('//')])

        # 复杂度分析
        complexity_analyzer = CodeComplexityAnalyzer()
        complexity_info = complexity_analyzer.analyze(code)

        # 重复度分析
        duplication_analyzer = DuplicationAnalyzer()
        duplication_info = duplication_analyzer.analyze(code)

        # 检查阈值
        self._check_thresholds(total_lines, complexity_info, duplication_info)

        return {
            'file': str(self.file_path),
            'total_lines': total_lines,
            'code_lines': code_lines,
            'empty_lines': empty_lines,
            'comment_lines': comment_lines,
            'complexity': complexity_info.get('complexity', 0),
            'functions': complexity_info.get('functions', 0),
            'test_cases': complexity_info.get('test_cases', 0),
            'describe_blocks': complexity_info.get('describe_blocks', 0),
            'duplication_rate': duplication_info['duplication_rate'],
            'issues': self.issues,
            'status': 'pass' if not self.issues else 'fail'
        }

    def _check_thresholds(self, lines: int, complexity: Dict, duplication: Dict):
        """检查阈值"""
        # 检查行数
        max_lines = self.thresholds.get('max_lines', 300)
        if lines > max_lines:
            self.issues.append({
                'type': 'too_long',
                'severity': 'warning',
                'message': f'文件过长 ({lines} > {max_lines} 行)',
                'suggestion': '建议拆分为多个文件或使用页面对象模式'
            })

        # 检查复杂度
        max_complexity = self.thresholds.get('max_complexity', 10)
        complexity_value = complexity.get('complexity', 0)
        if complexity_value > max_complexity:
            self.issues.append({
                'type': 'too_complex',
                'severity': 'warning',
                'message': f'复杂度过高 ({complexity_value} > {max_complexity})',
                'suggestion': '建议简化逻辑或拆分函数'
            })

        # 检查重复度
        max_duplication = self.thresholds.get('max_duplication', 30)
        duplication_rate = duplication.get('duplication_rate', 0)
        if duplication_rate > max_duplication:
            self.issues.append({
                'type': 'too_much_duplication',
                'severity': 'info',
                'message': f'重复度偏高 ({duplication_rate}% > {max_duplication}%)',
                'suggestion': '考虑提取公共函数或使用页面对象模式'
            })

        # 检查测试用例数量
        test_cases = complexity.get('test_cases', 0)
        if test_cases == 0:
            self.issues.append({
                'type': 'no_tests',
                'severity': 'error',
                'message': '未发现测试用例',
                'suggestion': '确保文件包含 test() 调用'
            })


# ============================================================================
# 目录分析器
# ============================================================================

class DirectoryAnalyzer:
    """分析整个测试目录"""

    def __init__(self, directory: str, thresholds: Dict):
        self.directory = directory
        self.thresholds = thresholds
        self.files = []

    def analyze(self) -> Dict:
        """执行分析"""
        # 查找所有测试文件
        test_files = list(Path(self.directory).glob('*.spec.js'))

        if not test_files:
            return {
                'error': f'未找到测试文件 (*.spec.js) 在 {self.directory}'
            }

        # 分析每个文件
        results = []
        total_issues = 0

        for file_path in test_files:
            analyzer = FileAnalyzer(str(file_path), self.thresholds)
            result = analyzer.analyze()
            results.append(result)
            total_issues += len(result['issues'])

        # 汇总统计
        total_lines = sum(r['total_lines'] for r in results)
        total_tests = sum(r['test_cases'] for r in results)
        avg_complexity = sum(r['complexity'] for r in results) / len(results) if results else 0
        avg_duplication = sum(r['duplication_rate'] for r in results) / len(results) if results else 0

        return {
            'directory': str(self.directory),
            'files_count': len(results),
            'total_lines': total_lines,
            'total_test_cases': total_tests,
            'average_complexity': round(avg_complexity, 2),
            'average_duplication_rate': round(avg_duplication, 2),
            'files': results,
            'total_issues': total_issues
        }

    def print_report(self):
        """打印分析报告"""
        result = self.analyze()

        if 'error' in result:
            print(f"[ERROR] {result['error']}")
            return

        print("\n" + "=" * 60)
        print("📊 测试代码质量分析报告")
        print("=" * 60)
        print(f"目录: {result['directory']}")
        print(f"文件数: {result['files_count']}")
        print(f"总行数: {result['total_lines']}")
        print(f"测试用例: {result['total_test_cases']}")
        print(f"平均复杂度: {result['average_complexity']}")
        print(f"平均重复度: {result['average_duplication_rate']}%")
        print()

        # 文件详情
        print("📋 文件详情:")
        print("-" * 60)

        for file_result in result['files']:
            status_icon = '✅' if file_result['status'] == 'pass' else '⚠️ '
            print(f"{status_icon} {Path(file_result['file']).name}")
            print(f"   行数: {file_result['total_lines']} (代码: {file_result['code_lines']})")
            print(f"   复杂度: {file_result['complexity']} | 测试: {file_result['test_cases']} | 重复: {file_result['duplication_rate']}%")

            if file_result['issues']:
                for issue in file_result['issues']:
                    icon = '[ERROR]' if issue['severity'] == 'error' else '[WARNING]'
                    print(f"   {icon} {issue['message']}")
                    print(f"       建议: {issue['suggestion']}")

            print()

        # 总结
        print("=" * 60)
        if result['total_issues'] == 0:
            print("✅ 所有文件质量良好，无需改进")
        else:
            print(f"⚠️  发现 {result['total_issues']} 个问题，请查看详情")
        print("=" * 60)

        return result


# ============================================================================
# 主程序
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='测试代码质量分析器',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument(
        'directory',
        help='测试目录路径'
    )
    parser.add_argument(
        '--max-lines',
        type=int,
        default=300,
        help='最大文件行数（默认: 300）'
    )
    parser.add_argument(
        '--max-complexity',
        type=int,
        default=10,
        help='最大复杂度（默认: 10）'
    )
    parser.add_argument(
        '--max-duplication',
        type=float,
        default=30.0,
        help='最大重复度百分比（默认: 30%%）'
    )
    parser.add_argument(
        '--json',
        help='输出 JSON 报告到文件'
    )

    args = parser.parse_args()

    # 检查目录存在
    if not Path(args.directory).exists():
        print(f"[ERROR] 目录不存在: {args.directory}")
        return 1

    # 配置阈值
    thresholds = {
        'max_lines': args.max_lines,
        'max_complexity': args.max_complexity,
        'max_duplication': args.max_duplication
    }

    # 执行分析
    analyzer = DirectoryAnalyzer(args.directory, thresholds)
    report = analyzer.print_report()

    # 输出 JSON
    if args.json:
        with open(args.json, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"\n[INFO] JSON 报告已保存: {args.json}")

    # 返回退出码
    return 1 if report.get('total_issues', 0) > 0 else 0


if __name__ == '__main__':
    sys.exit(main())
