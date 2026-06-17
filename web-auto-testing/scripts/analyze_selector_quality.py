#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
选择器质量评分器
根据 Playwright 官方最佳实践对选择器进行评分

参考：
- Playwright Selectors: https://playwright.dev/docs/selectors
- Best Practices: https://playwright.dev/docs/best-practices

评分标准：
    10分: getByRole() - 最稳定的语义化选择器
    9分:  getByLabel() - 表单元素专用
    8分:  getByPlaceholder() - 输入框专用
    7分:  getByTestId() - 测试专用属性
    6分:  getByText() - 文本匹配（需用修饰符）
    5分:  locator(selector) - CSS选择器
    3分:  CSS类选择器（.class）
    1分:  XPath选择器
    0分:  [ref="..."] - MCP快照专用（不可用）

Usage:
    # 分析测试文件
    python scripts/analyze_selector_quality.py tests/test.spec.js

    # 输出 JSON 报告
    python scripts/analyze_selector_quality.py tests/test.spec.js --json report.json
"""

import argparse
import json
import re
import sys
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any
from collections import defaultdict

# Windows UTF-8 兼容
if sys.platform == 'win32':
    import io
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8', errors='replace')


# ============================================================================
# 选择器评分规则
# ============================================================================

SELECTOR_SCORES = {
    # 语义化选择器（最推荐）
    'getByRole': {
        'score': 10,
        'category': 'semantic',
        'description': '最稳定的语义化选择器',
        'best': True
    },
    'getByLabel': {
        'score': 9,
        'category': 'semantic',
        'description': '表单元素专用选择器',
        'best': True
    },
    'getByPlaceholder': {
        'score': 8,
        'category': 'semantic',
        'description': '输入框专用选择器',
        'best': True
    },
    'getByTestId': {
        'score': 7,
        'category': 'test',
        'description': '测试专用属性选择器',
        'best': True
    },
    'getByText': {
        'score': 6,
        'category': 'text',
        'description': '文本匹配',
        'best': False,
        'warning': '可能匹配多个元素，建议使用 .first()'
    },
    'getByTitle': {
        'score': 6,
        'category': 'attribute',
        'description': '标题属性选择器',
        'best': False
    },
    'getByAltText': {
        'score': 6,
        'category': 'attribute',
        'description': '图片 alt 文本选择器',
        'best': False
    },
    # CSS 选择器
    'locator': {
        'score': 5,
        'category': 'css',
        'description': '通用 CSS 选择器',
        'best': False,
        'warning': '优先使用语义化选择器'
    },
    # 低质量选择器
    'css_class': {
        'score': 3,
        'category': 'css',
        'description': 'CSS 类选择器（不稳定）',
        'best': False,
        'warning': '类名经常变化，不推荐'
    },
    'css_id': {
        'score': 4,
        'category': 'css',
        'description': 'ID 选择器',
        'best': False
    },
    # 不推荐的选择器
    'xpath': {
        'score': 1,
        'category': 'xpath',
        'description': 'XPath 选择器（脆弱）',
        'best': False,
        'warning': 'XPath 非常脆弱，强烈不推荐'
    },
    'ref_attribute': {
        'score': 0,
        'category': 'invalid',
        'description': 'MCP 快照专用（实际不可用）',
        'best': False,
        'error': '错误：ref 属性只在 MCP 快照中存在'
    }
}


# ============================================================================
# 选择器提取器（使用正则表达式）
# ============================================================================

class SelectorExtractor:
    """使用正则表达式提取选择器"""

    # 匹配模式
    PATTERNS = [
        # getByRole('button', { name: 'xxx' })
        r'(getByRole|getByLabel|getByPlaceholder|getByTestId|getByText|getByTitle|getByAltText)\s*\(',
        # locator('.class') or locator('#id')
        r'\.locator\s*\(\s*["\']([#\.][^"\']+)["\']',
        # page.locator or直接 locator
        r'(page\s*\.\s*locator|iframe\s*\.\s*locator|frameLocator)\s*\(',
        # ref 属性
        r'\[ref\s*=\s*["\']e\d+["\']\]',
    ]

    def extract(self, code: str) -> List[Dict]:
        """提取所有选择器"""
        selectors = []
        lines = code.split('\n')

        for line_num, line in enumerate(lines, 1):
            # 跳过注释
            stripped = line.strip()
            if stripped.startswith('//') or stripped.startswith('/*'):
                continue

            # 尝试匹配各种模式
            selector = self._match_get_by(line, line_num)
            if selector:
                selectors.append(selector)
                continue

            selector = self._match_locator(line, line_num)
            if selector:
                selectors.append(selector)
                continue

            selector = self._match_ref(line, line_num)
            if selector:
                selectors.append(selector)

        return selectors

    def _match_get_by(self, line: str, line_num: int) -> Optional[Dict]:
        """匹配 getByXxx 调用"""
        # 匹配 getByRole('xxx') 或 getByRole("xxx")
        match = re.search(r'(getBy\w+)\s*\(\s*["\']([^"\']+)["\']', line)
        if match:
            method = match.group(1)
            if method in SELECTOR_SCORES:
                return {
                    'method': method,
                    'line': line_num,
                    'args': [match.group(2)],
                    'raw': line.strip(),
                    **SELECTOR_SCORES[method]
                }
        return None

    def _match_locator(self, line: str, line_num: int) -> Optional[Dict]:
        """匹配 locator 调用"""
        # 匹配 locator('.xxx') 或 locator("#xxx")
        match = re.search(r'\.locator\s*\(\s*["\']([#\.][^"\']+)["\']', line)
        if match:
            selector = match.group(1)

            if selector.startswith('.'):
                method = 'css_class'
            elif selector.startswith('#'):
                method = 'css_id'
            else:
                method = 'locator'

            return {
                'method': method,
                'line': line_num,
                'args': [selector],
                'raw': line.strip(),
                **SELECTOR_SCORES[method]
            }

        # 匹配 XPath
        match = re.search(r'\.locator\s*\(\s*["\']//', line)
        if match:
            return {
                'method': 'xpath',
                'line': line_num,
                'args': ['<xpath>'],
                'raw': line.strip(),
                **SELECTOR_SCORES['xpath']
            }

        return None

    def _match_ref(self, line: str, line_num: int) -> Optional[Dict]:
        """匹配 ref 属性"""
        match = re.search(r'\[ref\s*=\s*["\']e\d+["\']\]', line)
        if match:
            return {
                'method': 'ref_attribute',
                'line': line_num,
                'args': [match.group()],
                'raw': line.strip(),
                **SELECTOR_SCORES['ref_attribute']
            }
        return None


# ============================================================================
# 质量分析器
# ============================================================================

class QualityAnalyzer:
    """选择器质量分析器"""

    def __init__(self, file_path: str):
        self.file_path = file_path
        self.selectors = []
        self.stats = defaultdict(int)

    def analyze(self) -> Dict:
        """执行分析"""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            code = f.read()

        extractor = SelectorExtractor()
        self.selectors = extractor.extract(code)

        # 计算统计
        self._calculate_stats()

        # 生成报告
        return {
            'file': str(self.file_path),
            'timestamp': datetime.now().isoformat(),
            'total_selectors': len(self.selectors),
            'average_score': self._calculate_average_score(),
            'grade': self._calculate_grade(),
            'selectors': self.selectors,
            'statistics': dict(self.stats),
            'recommendations': self._generate_recommendations()
        }

    def _calculate_stats(self):
        """计算统计信息"""
        for selector in self.selectors:
            category = selector.get('category', 'unknown')
            self.stats[f'category_{category}'] += 1

            if selector.get('best', False):
                self.stats['best_practice'] += 1
            else:
                self.stats['not_best'] += 1

            if selector.get('warning'):
                self.stats['has_warning'] += 1

    def _calculate_average_score(self) -> float:
        """计算平均分数"""
        if not self.selectors:
            return 0
        total = sum(s.get('score', 0) for s in self.selectors)
        return round(total / len(self.selectors), 2)

    def _calculate_grade(self) -> str:
        """计算评级"""
        avg = self._calculate_average_score()
        if avg >= 9:
            return 'A (优秀)'
        elif avg >= 8:
            return 'B (良好)'
        elif avg >= 7:
            return 'C (中等)'
        elif avg >= 6:
            return 'D (及格)'
        else:
            return 'F (需改进)'

    def _generate_recommendations(self) -> List[str]:
        """生成改进建议"""
        recommendations = []

        # 检查是否使用了低质量选择器
        low_quality = [s for s in self.selectors if s.get('score', 0) <= 3]
        if low_quality:
            recommendations.append(
                f"发现 {len(low_quality)} 个低质量选择器（CSS类、XPath等），"
                f"建议替换为语义化选择器（getByRole、getByLabel 等）"
            )

        # 检查是否有警告
        has_warnings = [s for s in self.selectors if s.get('warning')]
        if has_warnings:
            recommendations.append(
                f"发现 {len(has_warnings)} 个选择器有潜在问题，请查看详细报告"
            )

        # 检查最佳实践比例
        if self.selectors:
            best_ratio = self.stats.get('best_practice', 0) / len(self.selectors)
            if best_ratio < 0.5:
                recommendations.append(
                    f"仅 {best_ratio*100:.0f}% 的选择器符合最佳实践（建议 > 50%）"
                )

        if not recommendations:
            recommendations.append("选择器质量良好，无需改进")

        return recommendations

    def print_report(self):
        """打印分析报告"""
        print("\n" + "=" * 60)
        print("📊 选择器质量分析报告")
        print("=" * 60)
        print(f"文件: {self.file_path}")
        print(f"选择器总数: {len(self.selectors)}")
        print(f"平均分数: {self._calculate_average_score()}/10")
        print(f"评级: {self._calculate_grade()}")
        print()

        # 按类别统计
        print("📈 分类统计:")
        for key, value in sorted(self.stats.items()):
            if key.startswith('category_') and value > 0:
                category = key.replace('category_', '').upper()
                print(f"  {category}: {value} 个")
        print()

        # 最佳实践统计
        best = self.stats.get('best_practice', 0)
        not_best = self.stats.get('not_best', 0)
        print(f"✅ 符合最佳实践: {best} 个")
        print(f"⚠️  不符合最佳实践: {not_best} 个")
        print()

        # 详细选择器列表
        if self.selectors:
            print("📋 选择器详情:")
            print("-" * 60)

            for i, selector in enumerate(sorted(self.selectors, key=lambda x: x['score']), 1):
                score = selector.get('score', 0)
                icon = '✅' if score >= 7 else '⚠️ ' if score >= 5 else '❌'

                args_str = ', '.join([str(a) for a in selector.get('args', [])[:2]])

                print(f"{icon} #{i} 第{selector['line']}行: {selector['method']}({args_str})")
                print(f"   分数: {score}/10 - {selector.get('description', '')}")

                if selector.get('warning'):
                    print(f"   ⚠️  {selector['warning']}")

                if selector.get('error'):
                    print(f"   ❌ {selector['error']}")

                if i < len(self.selectors):  # 不是最后一个
                    print()

        # 建议
        print("💡 改进建议:")
        print("-" * 60)
        for i, rec in enumerate(self._generate_recommendations(), 1):
            print(f"{i}. {rec}")
        print()

        print("=" * 60)


# ============================================================================
# 主程序
# ============================================================================

def main():
    parser = argparse.ArgumentParser(
        description='选择器质量评分器 - 根据 Playwright 最佳实践评分',
        formatter_class=argparse.RawDescriptionHelpFormatter
    )

    parser.add_argument('file', help='Playwright 测试文件路径')
    parser.add_argument('--json', help='输出 JSON 报告到文件')
    parser.add_argument('--verbose', '-v', action='store_true', help='显示详细信息')

    args = parser.parse_args()

    # 检查文件存在
    if not Path(args.file).exists():
        print(f"[ERROR] 文件不存在: {args.file}")
        return 1

    # 执行分析
    analyzer = QualityAnalyzer(args.file)
    report = analyzer.analyze()

    # 打印报告
    analyzer.print_report()

    # 输出 JSON
    if args.json:
        with open(args.json, 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        print(f"[INFO] JSON 报告已保存: {args.json}")

    # 返回退出码（分数低于6分返回1）
    return 1 if report['average_score'] < 6 else 0


if __name__ == '__main__':
    sys.exit(main())
