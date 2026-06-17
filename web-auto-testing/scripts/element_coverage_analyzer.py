#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
元素覆盖率分析工具

计算测试用例对页面元素的覆盖率。

使用方法:
    python scripts/element_coverage_analyzer.py --elements elements.json --tested tested.json

输出格式:
    {
        "total_elements": 23,
        "tested_elements": 21,
        "coverage_rate": 91.3,
        "untested_elements": ["导出按钮", "刷新按钮"]
    }
"""

import sys
import json
import argparse
from typing import Dict, Set


# Windows UTF-8 兼容性处理
if sys.platform == 'win32':
    try:
        import io
        sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8', errors='replace')
    except (ImportError, AttributeError):
        pass


def load_json(file_path: str) -> Dict:
    """加载 JSON 文件"""
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except FileNotFoundError:
        raise argparse.ArgumentTypeError(f"文件不存在: {file_path}")
    except json.JSONDecodeError as e:
        raise argparse.ArgumentTypeError(f"JSON 格式错误: {e}")
    except PermissionError:
        raise argparse.ArgumentTypeError(f"没有文件读取权限: {file_path}")
    except Exception as e:
        raise argparse.ArgumentTypeError(f"读取文件失败: {e}")


def extract_elements(data: Dict) -> Set[str]:
    """从数据中提取元素集合"""
    elements = set()

    if 'elements' in data:
        for elem in data['elements']:
            if 'name' in elem:
                elements.add(elem['name'])
            elif 'text' in elem:
                elements.add(elem['text'])
            elif 'role' in elem:
                elements.add(f"{elem.get('role', '')}:{elem.get('name', elem.get('text', ''))}")

    return elements


def calculate_coverage(
    all_elements: Set[str],
    tested_elements: Set[str]
) -> Dict:
    """计算覆盖率"""
    total = len(all_elements)
    tested = len(tested_elements & all_elements)
    untested = all_elements - tested_elements

    coverage_rate = (tested / total * 100) if total > 0 else 0

    return {
        "total_elements": total,
        "tested_elements": tested,
        "coverage_rate": round(coverage_rate, 1),
        "untested_elements": sorted(list(untested))
    }


def main():
    parser = argparse.ArgumentParser(description='元素覆盖率分析工具')
    parser.add_argument('--elements', required=True, help='所有元素的 JSON 文件')
    parser.add_argument('--tested', required=True, help='已测试元素的 JSON 文件')
    parser.add_argument('--output', help='输出结果到文件')

    args = parser.parse_args()

    # 加载数据
    all_data = load_json(args.elements)
    tested_data = load_json(args.tested)

    # 提取元素
    all_elements = extract_elements(all_data)
    tested_elements = extract_elements(tested_data)

    # 计算覆盖率
    result = calculate_coverage(all_elements, tested_elements)

    # 输出结果
    output = json.dumps(result, ensure_ascii=False, indent=2)

    if args.output:
        with open(args.output, 'w', encoding='utf-8') as f:
            f.write(output)
        print(f"结果已保存到 {args.output}")
    else:
        print(output)


if __name__ == '__main__':
    main()
