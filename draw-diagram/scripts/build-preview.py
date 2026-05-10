#!/usr/bin/env python3
"""
Build an interactive HTML preview from an SVG file.

Usage:
  python3 build-preview.py <input.svg> [output.html]

Reads the SVG, annotates nodes/arrows with data-* attributes for JS interactivity,
wraps in a self-contained HTML file with toolbar + interactive JS.
"""

import math
import os
import re
import sys


SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))


def _nearest_node(point, node_boxes, max_dist_factor=2.0):
    """Find the closest node to *point* that is within its own size threshold.

    *node_boxes* maps nid -> (cx, cy, half_diag) where half_diag is
    ``hypot(width/2, height/2)``.  A match is accepted when the distance
    from *point* to the node center is within ``max_dist_factor * half_diag``.

    Returns the node id of the closest qualifying node, or None.
    """
    px, py = point
    best_nid = None
    best_dist = float("inf")
    for nid, (cx, cy, hd) in node_boxes.items():
        d = math.hypot(px - cx, py - cy)
        if d < best_dist and d <= hd * max_dist_factor:
            best_dist = d
            best_nid = nid
    return best_nid


def read_js():
    js_path = os.path.join(SCRIPT_DIR, "interactive-preview.js")
    with open(js_path, "r", encoding="utf-8") as f:
        return f.read()


def _path_bounds_from_d(d: str):
    """Extract approximate bounding box from an SVG path data string."""
    nums = [float(n) for n in re.findall(r'[-\d.]+', d)]
    if len(nums) < 4:
        return None
    xs = nums[0::2]
    ys = nums[1::2]
    return (min(xs), min(ys), max(xs), max(ys))


def annotate_svg(svg_content):
    """Add data-* attributes to nodes and arrows for JS interactivity."""
    arrow_counter = [0]
    lines = svg_content.split('\n')

    # --- Phase 1: Identify node shapes (rects and paths) ---
    # A "node shape" is a colored/filled <rect> or <path> (not background, not arrow).
    # Section containers have stroke-dasharray or very large width (>500).
    # Background rect has width >= 900.
    node_shape_lines = {}  # line_index -> (left, top, right, bottom)
    for idx, line in enumerate(lines):
        s = line.strip()
        if s.startswith('<rect'):
            # Skip background
            w_match = re.search(r'width="([0-9.]+)"', s)
            if w_match and float(w_match.group(1)) >= 900:
                continue
            # Skip section containers
            if 'stroke-dasharray' in s:
                continue
            w_match = re.search(r'width="([0-9.]+)"', s)
            if w_match and float(w_match.group(1)) > 500:
                continue
            fill_match = re.search(r'fill="([^"]+)"', s)
            if not fill_match or fill_match.group(1) == 'none':
                continue
            # Exclude terminal header bars and arrow label badges
            h_match = re.search(r'height="([0-9.]+)"', s)
            if h_match and float(h_match.group(1)) <= 20:
                continue
            x_match = re.search(r'x="([^"]+)"', s)
            y_match = re.search(r'y="([^"]+)"', s)
            w_match = re.search(r'width="([0-9.]+)"', s)
            h_match = re.search(r'height="([0-9.]+)"', s)
            x = float(x_match.group(1)) if x_match else 0
            y = float(y_match.group(1)) if y_match else 0
            w = float(w_match.group(1)) if w_match else 200
            h = float(h_match.group(1)) if h_match else 60
            node_shape_lines[idx] = (x, y, x + w, y + h)
        elif s.startswith('<path') and 'fill="none"' not in s and 'marker-end' not in s and 'stroke-dasharray' not in s:
            # Node paths: hexagon, document, folder, speech
            d_match = re.search(r'd="([^"]+)"', s)
            if d_match:
                bounds = _path_bounds_from_d(d_match.group(1))
                if bounds:
                    node_shape_lines[idx] = bounds

    # --- Phase 2: Identify arrow lines/paths ---
    arrow_lines = {}  # line_index -> flow_color
    flow_colors = {
        "#7c3aed": "control", "#10b981": "write", "#2563eb": "read",
        "#f97316": "data", "#a855f7": "control", "#22c55e": "write",
        "#38bdf8": "read", "#fb7185": "data", "#c084fc": "async",
        "#3b82f6": "control", "#34d399": "write", "#60a5fa": "read",
        "#d97757": "control", "#7b8b5c": "write", "#8c6f5a": "read",
        "#10a37f": "control", "#0f766e": "write", "#0891b2": "read",
        "#67e8f9": "control", "#22d3ee": "write",
        "#16a34a": "write", "#059669": "write",
        "#ea580c": "data", "#6b7280": "async",
    }
    for idx, line in enumerate(lines):
        s = line.strip()
        is_arrow = False
        flow = "control"
        # Match <line> with marker-end (most common in hand-written SVG)
        if s.startswith('<line') and 'marker-end' in s:
            is_arrow = True
            stroke_match = re.search(r'stroke="([^"]+)"', s)
            if stroke_match:
                flow = flow_colors.get(stroke_match.group(1), "control")
        # Match <path> with marker-end (template-generated SVG)
        elif s.startswith('<path') and 'marker-end' in s:
            is_arrow = True
            stroke_match = re.search(r'stroke="([^"]+)"', s)
            if stroke_match:
                flow = flow_colors.get(stroke_match.group(1), "control")
        if is_arrow:
            arrow_lines[idx] = flow

    # --- Phase 3: Annotate arrows ---
    for idx in list(arrow_lines.keys()):
        arrow_counter[0] += 1
        aid = f"arrow-{arrow_counter[0]}"
        flow = arrow_lines[idx]
        lines[idx] = lines[idx].replace('<line ', f'<line data-arrow-id="{aid}" data-flow="{flow}" ', 1)
        lines[idx] = lines[idx].replace('<path ', f'<path data-arrow-id="{aid}" data-flow="{flow}" ', 1)

    # --- Phase 4: Group node shapes with their associated text into <g> wrappers ---
    # For each node shape, find nearby text and child shapes (within next ~20 lines) and wrap them.
    # Also collect node bounding boxes for Phase 5 arrow↔node matching.
    final_lines = []
    wrapped = set()
    nc = 0
    node_boxes = {}  # nid -> (cx, cy, half_diag)

    for idx, line in enumerate(lines):
        if idx in wrapped:
            continue
        if idx in node_shape_lines:
            nc += 1
            nid = f"node-{nc}"
            final_lines.append(f'  <g data-node-id="{nid}">')
            final_lines.append(line)
            wrapped.add(idx)

            left, top, right, bottom = node_shape_lines[idx]
            node_boxes[nid] = ((left + right) / 2, (top + bottom) / 2, math.hypot((right - left) / 2, (bottom - top) / 2))

            for fwd in range(idx + 1, min(idx + 35, len(lines))):
                if fwd in wrapped or fwd in node_shape_lines or fwd in arrow_lines:
                    break
                fwd_s = lines[fwd].strip()
                if not fwd_s:
                    continue
                # Include text elements within the node's bounding area
                if fwd_s.startswith('<text'):
                    tx_match = re.search(r'x="([^"]+)"', fwd_s)
                    ty_match = re.search(r'y="([^"]+)"', fwd_s)
                    if tx_match and ty_match:
                        tx = float(tx_match.group(1))
                        ty = float(ty_match.group(1))
                        if left - 20 <= tx <= right + 20 and top - 5 <= ty <= bottom + 20:
                            final_lines.append(lines[fwd])
                            wrapped.add(fwd)
                        else:
                            break
                    else:
                        final_lines.append(lines[fwd])
                        wrapped.add(fwd)
                # Include child shapes (terminal dots, cylinder caps, header bars, etc.)
                elif fwd_s.startswith(('<rect', '<circle', '<ellipse', '<path', '<line', '<polygon')):
                    final_lines.append(lines[fwd])
                    wrapped.add(fwd)
                # Include clipPath and clip-path groups (cylinder text wrapping)
                elif fwd_s.startswith('<clipPath') or fwd_s.startswith('<g clip-path') or fwd_s.startswith('</g') or fwd_s.startswith('</clipPath'):
                    final_lines.append(lines[fwd])
                    wrapped.add(fwd)
                elif fwd_s.startswith('<g>') or fwd_s.startswith('<g '):
                    # Include plain <g> wrappers used for text clipping
                    final_lines.append(lines[fwd])
                    wrapped.add(fwd)
                else:
                    break
            final_lines.append('  </g>')
        else:
            final_lines.append(line)

    # --- Phase 5: Inject data-source/data-target on arrows via geometry matching ---
    # For each annotated arrow, parse its start/end coordinates and find the nearest
    # node whose center is closest to each endpoint.
    if node_boxes:
        for i, line in enumerate(final_lines):
            s = line.strip()
            if 'data-arrow-id="' not in s:
                continue
            start = end = None
            # Parse <path d="M x,y L ... x,y">  (last L segment is the endpoint)
            if '<path' in s:
                d_match = re.search(r'd="M\s*([-\d.]+),([-\d.]+)\s+L\s+(.*?)"', s)
                if d_match:
                    start = (float(d_match.group(1)), float(d_match.group(2)))
                    segments = d_match.group(3).split()
                    last_xy = segments[-1]
                    parts = last_xy.split(',')
                    end = (float(parts[0]), float(parts[1]))
            # Parse <line x1="..." y1="..." x2="..." y2="...">
            elif '<line' in s:
                x1 = re.search(r'x1="([-\d.]+)"', s)
                y1 = re.search(r'y1="([-\d.]+)"', s)
                x2 = re.search(r'x2="([-\d.]+)"', s)
                y2 = re.search(r'y2="([-\d.]+)"', s)
                if x1 and y1 and x2 and y2:
                    start = (float(x1.group(1)), float(y1.group(1)))
                    end = (float(x2.group(1)), float(y2.group(1)))
            if not start or not end:
                continue

            source_nid = _nearest_node(start, node_boxes, max_dist_factor=1.5)
            target_nid = _nearest_node(end, node_boxes, max_dist_factor=1.5)

            if source_nid:
                final_lines[i] = final_lines[i].replace('data-arrow-id=', f'data-source="{source_nid}" data-arrow-id=', 1)
            if target_nid:
                final_lines[i] = final_lines[i].replace('data-arrow-id=', f'data-target="{target_nid}" data-arrow-id=', 1)

    return '\n'.join(final_lines)


def get_css():
    return """
    * { margin: 0; padding: 0; box-sizing: border-box; }
    html, body { height: 100%; overflow: hidden; font-family: system-ui, -apple-system, BlinkMacSystemFont, sans-serif; background: #f5f5f7; color: #1d1d1f; display: flex; flex-direction: column; line-height: 1.5; }
    #toolbar {
      background: #ffffff;
      padding: 0.5rem 1.5rem;
      display: flex;
      align-items: center;
      gap: 8px;
      border-bottom: 1px solid #d1d1d6;
      flex-shrink: 0;
      flex-wrap: wrap;
    }
    #toolbar .btn-group { display: flex; gap: 4px; }
    .style-btn {
      padding: 6px 14px;
      border: 2px solid #d1d1d6;
      border-radius: 12px;
      background: #ffffff;
      color: #86868b;
      cursor: pointer;
      font-size: 12px;
      font-weight: 500;
      transition: all 0.15s ease;
    }
    .style-btn:hover { border-color: #0071e3; color: #1d1d1f; }
    .style-btn.active { background: #0071e3; color: #fff; border-color: #0071e3; }
    .action-btn {
      padding: 6px 16px;
      border: none;
      border-radius: 12px;
      cursor: pointer;
      font-size: 12px;
      font-weight: 600;
      transition: all 0.15s ease;
    }
    .export-svg { background: #34c759; color: #fff; }
    .export-svg:hover { background: #30b350; }
    .export-png { background: #0071e3; color: #fff; }
    .export-png:hover { background: #0077ed; }
    .separator { width: 1px; height: 24px; background: #d1d1d6; margin: 0 8px; }
    #canvas {
      flex: 1;
      overflow: auto;
      display: flex;
      align-items: center;
      justify-content: center;
      padding: 2rem;
    }
    #canvas svg { max-width: 100%; max-height: 100%; cursor: default; }
    [data-node-id] { cursor: grab; }
    [data-node-id]:active { cursor: grabbing; }
    #hint {
      background: #ffffff;
      border-top: 1px solid #d1d1d6;
      padding: 0.5rem 1.5rem;
      flex-shrink: 0;
      text-align: center;
      font-size: 0.75rem;
      color: #86868b;
    }
    """


def build_html(svg_content, output_path):
    annotated = annotate_svg(svg_content)
    js_code = read_js()
    css = get_css()

    svg_source_js = annotated.replace('\\', '\\\\').replace('`', '\\`').replace('${', '\\${')
    html = '<!DOCTYPE html>\n<html lang="zh-CN">\n<head>\n<meta charset="UTF-8">\n<meta name="viewport" content="width=device-width, initial-scale=1.0">\n<title>Diagram Preview</title>\n<style>' + css + '</style>\n</head>\n<body>\n' + '<div id="toolbar">\n  <div class="btn-group">\n    <button class="style-btn" data-style="1" onclick="switchStyle(1)">Flat</button>\n    <button class="style-btn" data-style="2" onclick="switchStyle(2)">Notion</button>\n    <button class="style-btn" data-style="3" onclick="switchStyle(3)">Claude</button>\n    <button class="style-btn" data-style="4" onclick="switchStyle(4)">OpenAI</button>\n    <button class="style-btn" data-style="5" onclick="switchStyle(5)">Enterprise</button>\n  </div>\n  <div class="separator"></div>\n  <button class="action-btn export-svg" onclick="exportSVG()">导出 SVG</button>\n  <button class="action-btn export-png" onclick="exportPNG()">导出 PNG</button>\n</div>\n' + '<div id="canvas">\n' + annotated + '\n</div>\n' + '<div id="hint">拖拽节点调整位置 | 双击文字编辑标签 | 点击按钮切换风格</div>\n' + '<script>window._originalSVG = `' + svg_source_js + '`;</script>\n' + '<script>\n' + js_code + '\n</script>\n</body>\n</html>'

    with open(output_path, "w", encoding="utf-8") as f:
        f.write(html)
    print(f"Preview HTML generated: {output_path}")


def main():
    if len(sys.argv) < 2:
        print("Usage: python3 build-preview.py <input.svg> [output.html]")
        sys.exit(1)

    svg_path = sys.argv[1]
    output_path = sys.argv[2] if len(sys.argv) > 2 else svg_path.replace('.svg', '-preview.html')

    with open(svg_path, "r", encoding="utf-8") as f:
        svg_content = f.read()

    build_html(svg_content, output_path)


if __name__ == "__main__":
    main()
