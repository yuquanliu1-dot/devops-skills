// scripts/interactive-preview.js — Part 1: Style Profiles & Switching

const STYLE_PROFILES = {
  1: {
    name: "Flat Icon",
    font_family: "'Helvetica Neue', Helvetica, Arial, 'PingFang SC', 'Microsoft YaHei', sans-serif",
    background: "#ffffff",
    shadow: true,
    title_fill: "#111827",
    title_size: 30,
    subtitle_fill: "#6b7280",
    subtitle_size: 14,
    node_fill: "#ffffff",
    node_stroke: "#d1d5db",
    node_radius: 10,
    arrow_width: 2.4,
    arrow_colors: {
      control: "#7c3aed", write: "#10b981", read: "#2563eb",
      data: "#f97316", async: "#7c3aed", feedback: "#ef4444", neutral: "#6b7280"
    },
    arrow_label_bg: "#ffffff",
    arrow_label_opacity: 0.94,
    arrow_label_fill: "#6b7280",
    text_primary: "#111827",
    text_secondary: "#6b7280",
    text_muted: "#94a3b8",
    section_stroke: "#dbe5f1",
    section_dash: "6 5",
    section_label_fill: "#2563eb",
    legend_fill: "#6b7280"
  },
  2: {
    name: "Notion Clean",
    font_family: "-apple-system, BlinkMacSystemFont, 'Segoe UI', 'PingFang SC', 'Microsoft YaHei', sans-serif",
    background: "#ffffff",
    shadow: false,
    title_fill: "#111827",
    title_size: 18,
    subtitle_fill: "#9ca3af",
    subtitle_size: 13,
    node_fill: "#f9fafb",
    node_stroke: "#e5e7eb",
    node_radius: 4,
    arrow_width: 1.8,
    arrow_colors: {
      control: "#3b82f6", write: "#3b82f6", read: "#3b82f6",
      data: "#3b82f6", async: "#9ca3af", feedback: "#9ca3af", neutral: "#d1d5db"
    },
    arrow_label_bg: "#ffffff",
    arrow_label_opacity: 0.96,
    arrow_label_fill: "#6b7280",
    text_primary: "#111827",
    text_secondary: "#374151",
    text_muted: "#9ca3af",
    section_stroke: "#e5e7eb",
    section_dash: "",
    section_label_fill: "#9ca3af",
    legend_fill: "#6b7280"
  },
  3: {
    name: "Claude Official",
    font_family: "'Helvetica Neue', Helvetica, Arial, 'PingFang SC', 'Microsoft YaHei', sans-serif",
    background: "#f8f6f3",
    shadow: false,
    title_fill: "#141413",
    title_size: 24,
    subtitle_fill: "#8f8a80",
    subtitle_size: 13,
    node_fill: "#fffcf7",
    node_stroke: "#d9d0c3",
    node_radius: 10,
    arrow_width: 2.0,
    arrow_colors: {
      control: "#d97757", write: "#7b8b5c", read: "#8c6f5a",
      data: "#b45309", async: "#9a6fb0", feedback: "#d97757", neutral: "#8f8a80"
    },
    arrow_label_bg: "#f8f6f3",
    arrow_label_opacity: 0.96,
    arrow_label_fill: "#6b6257",
    text_primary: "#141413",
    text_secondary: "#6b6257",
    text_muted: "#a29a8f",
    section_stroke: "#ded8cf",
    section_dash: "5 4",
    section_label_fill: "#8b7355",
    legend_fill: "#6b6257"
  },
  4: {
    name: "OpenAI",
    font_family: "'Helvetica Neue', Helvetica, Arial, 'PingFang SC', 'Microsoft YaHei', sans-serif",
    background: "#ffffff",
    shadow: false,
    title_fill: "#0f172a",
    title_size: 24,
    subtitle_fill: "#64748b",
    subtitle_size: 13,
    node_fill: "#ffffff",
    node_stroke: "#dce5e3",
    node_radius: 14,
    arrow_width: 2.0,
    arrow_colors: {
      control: "#10a37f", write: "#0f766e", read: "#0891b2",
      data: "#f59e0b", async: "#64748b", feedback: "#10a37f", neutral: "#94a3b8"
    },
    arrow_label_bg: "#ffffff",
    arrow_label_opacity: 0.96,
    arrow_label_fill: "#475569",
    text_primary: "#0f172a",
    text_secondary: "#475569",
    text_muted: "#94a3b8",
    section_stroke: "#e2e8f0",
    section_dash: "5 4",
    section_label_fill: "#10a37f",
    legend_fill: "#475569"
  },
  5: {
    name: "Enterprise",
    font_family: "'Helvetica Neue', Helvetica, Arial, 'PingFang SC', 'Microsoft YaHei', sans-serif",
    background: "#ffffff",
    shadow: false,
    title_fill: "#0a0a0a",
    title_size: 22,
    subtitle_fill: "#666666",
    subtitle_size: 12,
    node_fill: "#ffffff",
    node_stroke: "#1a1a1a",
    node_radius: 2,
    arrow_width: 1.5,
    arrow_colors: {
      control: "#333333", write: "#555555", read: "#555555",
      data: "#333333", async: "#999999", feedback: "#666666", neutral: "#bbbbbb"
    },
    arrow_label_bg: "#ffffff",
    arrow_label_opacity: 0.95,
    arrow_label_fill: "#4a4a4a",
    text_primary: "#0a0a0a",
    text_secondary: "#4a4a4a",
    text_muted: "#888888",
    section_stroke: "#1a1a1a",
    section_dash: "4 3",
    section_label_fill: "#4a4a4a",
    legend_fill: "#4a4a4a"
  }
};

let currentStyleIndex = 5;

function switchStyle(index) {
  const p = STYLE_PROFILES[index];
  if (!p) return;
  currentStyleIndex = index;

  const svg = document.querySelector('#canvas svg');
  if (!svg) return;

  // Update background
  const bgRect = svg.querySelector('rect:first-of-type');
  if (bgRect) {
    bgRect.setAttribute('fill', p.background);
  }

  // Update style element in defs
  const styleEl = svg.querySelector('defs style');
  if (styleEl) {
    styleEl.textContent = [
      `text { font-family: ${p.font_family}; }`,
      `.title { font-size: ${p.title_size}px; font-weight: 700; fill: ${p.title_fill}; }`,
      `.subtitle { font-size: ${p.subtitle_size}px; font-weight: 500; fill: ${p.subtitle_fill}; }`,
      `.node-title { font-size: 18px; font-weight: 700; fill: ${p.text_primary}; }`,
      `.node-sub { font-size: 12px; font-weight: 500; fill: ${p.text_secondary}; }`,
      `.arrow-label { font-size: 12px; font-weight: 600; fill: ${p.arrow_label_fill}; }`,
      `.legend { font-size: 12px; font-weight: 500; fill: ${p.legend_fill}; }`,
    ].join('\n    ');
  }

  // Update nodes
  const isEnterprise = p.name === 'Enterprise';
  svg.querySelectorAll('[data-node-id]').forEach(group => {
    group.querySelectorAll('rect').forEach(rect => {
      const isAccent = rect.getAttribute('fill') && !['none', p.node_fill, '#ffffff', '#f9fafb'].includes(rect.getAttribute('fill'));
      if (!isAccent) rect.setAttribute('fill', p.node_fill);
      rect.setAttribute('stroke', p.node_stroke);
      rect.setAttribute('rx', p.node_radius);
    });
    // Handle ellipses (cylinder top/bottom, bot head)
    group.querySelectorAll('ellipse').forEach(el => {
      const fill = el.getAttribute('fill');
      if (fill && fill !== 'none' && !fill.startsWith('url')) {
        if (isEnterprise) {
          el.setAttribute('fill', p.node_fill);
          el.setAttribute('stroke', p.node_stroke);
        } else {
          el.setAttribute('fill', p.node_fill);
          el.setAttribute('stroke', p.node_stroke);
        }
      }
    });
    // Handle circles (bot eyes, terminal dots, antenna)
    group.querySelectorAll('circle').forEach(c => {
      const fill = c.getAttribute('fill');
      if (fill && fill !== 'none') {
        if (isEnterprise) {
          const r = parseFloat(c.getAttribute('r') || 4);
          if (r <= 6) {
            c.setAttribute('fill', '#888888');
          } else {
            c.setAttribute('fill', '#333333');
          }
        }
      }
    });
    // Handle lines inside nodes (document lines, bot antenna)
    group.querySelectorAll('line').forEach(l => {
      if (isEnterprise) {
        l.setAttribute('stroke', '#1a1a1a');
        l.setAttribute('stroke-opacity', '0.35');
      }
    });
  });

  // Update arrows
  svg.querySelectorAll('[data-arrow-id]').forEach(path => {
    const flow = path.getAttribute('data-flow') || 'control';
    const color = p.arrow_colors[flow] || p.arrow_colors.control;
    path.setAttribute('stroke', color);
    path.setAttribute('stroke-width', p.arrow_width);
  });

  // Update arrow label backgrounds
  svg.querySelectorAll('.arrow-label-badge').forEach(rect => {
    rect.setAttribute('fill', p.arrow_label_bg);
    rect.setAttribute('opacity', p.arrow_label_opacity);
  });

  // Update section containers
  svg.querySelectorAll('rect[stroke-dasharray]').forEach(rect => {
    const w = parseFloat(rect.getAttribute('width') || 0);
    if (w > 500) {
      rect.setAttribute('stroke', p.section_stroke);
      if (p.section_dash) rect.setAttribute('stroke-dasharray', p.section_dash);
      else rect.removeAttribute('stroke-dasharray');
    }
  });

  // Update marker arrowhead colors
  const markerMap = {control:'arrowA',write:'arrowB',read:'arrowC',data:'arrowE',async:'arrowF',feedback:'arrowG',neutral:'arrowH'};
  for (const [flow, mid] of Object.entries(markerMap)) {
    const marker = svg.querySelector(`marker[id="${mid}"] polygon`);
    if (marker) marker.setAttribute('fill', p.arrow_colors[flow] || p.arrow_colors.control);
  }

  // Highlight active button
  document.querySelectorAll('.style-btn').forEach(btn => {
    btn.classList.toggle('active', parseInt(btn.dataset.style) === index);
  });
}

// --- Drag Handler ---

let dragState = null;

function initDrag() {
  const canvas = document.getElementById('canvas');
  const svg = canvas ? canvas.querySelector('svg') : null;
  if (!svg) return;

  const viewBox = svg.viewBox.baseVal;

  canvas.addEventListener('mousedown', (e) => {
    const group = e.target.closest('[data-node-id]');
    if (!group) return;
    e.preventDefault();

    const svgPoint = svgPointFromEvent(e, svg);
    const transform = group.getAttribute('transform') || '';
    const match = transform.match(/translate\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)/);
    const tx = match ? parseFloat(match[1]) : 0;
    const ty = match ? parseFloat(match[2]) : 0;

    dragState = { group, startSvgX: svgPoint.x, startSvgY: svgPoint.y, startTx: tx, startTy: ty, svg, viewBox };
    group.style.cursor = 'grabbing';
  });

  canvas.addEventListener('mousemove', (e) => {
    if (!dragState) return;
    e.preventDefault();
    const svgPoint = svgPointFromEvent(e, dragState.svg);
    const dx = svgPoint.x - dragState.startSvgX;
    const dy = svgPoint.y - dragState.startSvgY;
    let newTx = dragState.startTx + dx;
    let newTy = dragState.startTy + dy;

    // Constrain to viewBox
    const nodeRect = dragState.group.querySelector('rect, path');
    if (nodeRect) {
      const bbox = nodeRect.getBBox();
      const minX = -bbox.x + 4;
      const minY = -bbox.y + 4;
      const maxX = dragState.viewBox.width - bbox.x - bbox.width - 4;
      const maxY = dragState.viewBox.height - bbox.y - bbox.height - 4;
      newTx = Math.max(minX, Math.min(maxX, newTx));
      newTy = Math.max(minY, Math.min(maxY, newTy));
    }

    dragState.group.setAttribute('transform', `translate(${newTx}, ${newTy})`);
    dragState.currentTx = newTx;
    dragState.currentTy = newTy;
    updateConnectedArrows(dragState.group, dragState.svg);
  });

  const endDrag = () => {
    if (!dragState) return;
    dragState.group.style.cursor = '';
    updateConnectedArrows(dragState.group, dragState.svg);
    dragState = null;
  };

  canvas.addEventListener('mouseup', endDrag);
  canvas.addEventListener('mouseleave', endDrag);
}

function svgPointFromEvent(e, svg) {
  const pt = svg.createSVGPoint();
  pt.x = e.clientX;
  pt.y = e.clientY;
  const ctm = svg.getScreenCTM();
  if (!ctm) return { x: 0, y: 0 };
  return pt.matrixTransform(ctm.inverse());
}

function updateConnectedArrows(nodeGroup, svg) {
  const nodeId = nodeGroup.getAttribute('data-node-id');
  if (!nodeId) return;

  svg.querySelectorAll('[data-arrow-id]').forEach(arrowPath => {
    const source = arrowPath.getAttribute('data-source');
    const target = arrowPath.getAttribute('data-target');
    if (source !== nodeId && target !== nodeId) return;

    const sourceGroup = svg.querySelector(`[data-node-id="${source}"]`);
    const targetGroup = svg.querySelector(`[data-node-id="${target}"]`);
    if (!sourceGroup || !targetGroup) return;

    const sourceRect = sourceGroup.querySelector('rect, path');
    const targetRect = targetGroup.querySelector('rect, path');
    if (!sourceRect || !targetRect) return;

    const sourceBBox = getTransformedBBox(sourceGroup, sourceRect);
    const targetBBox = getTransformedBBox(targetGroup, targetRect);

    const start = edgePoint(sourceBBox, targetBBox.cx, targetBBox.cy);
    const end = edgePoint(targetBBox, sourceBBox.cx, sourceBBox.cy);

    // Preserve orthogonal routing so arrows don't collapse into straight lines that cut through nodes
    const dx = Math.abs(end.x - start.x);
    const dy = Math.abs(end.y - start.y);
    let newD;
    if (dx > dy * 1.2) {
      // Source and target are mostly side-by-side: horizontal corridor first
      const midX = (start.x + end.x) / 2;
      newD = `M ${start.x},${start.y} L ${midX},${start.y} L ${midX},${end.y} L ${end.x},${end.y}`;
    } else if (dy > dx * 1.2) {
      // Mostly above/below: vertical corridor first
      const midY = (start.y + end.y) / 2;
      newD = `M ${start.x},${start.y} L ${start.x},${midY} L ${end.x},${midY} L ${end.x},${end.y}`;
    } else {
      // Diagonal: two-segment elbow, preferring the longer axis first
      if (dx > dy) {
        newD = `M ${start.x},${start.y} L ${end.x},${start.y} L ${end.x},${end.y}`;
      } else {
        newD = `M ${start.x},${start.y} L ${start.x},${end.y} L ${end.x},${end.y}`;
      }
    }
    arrowPath.setAttribute('d', newD);
  });
}

function getTransformedBBox(group, shape) {
  const bbox = shape.getBBox();
  const transform = group.getAttribute('transform') || '';
  const match = transform.match(/translate\(\s*([-\d.]+)\s*,\s*([-\d.]+)\s*\)/);
  const tx = match ? parseFloat(match[1]) : 0;
  const ty = match ? parseFloat(match[2]) : 0;
  return {
    x: bbox.x + tx, y: bbox.y + ty,
    width: bbox.width, height: bbox.height,
    cx: bbox.x + tx + bbox.width / 2, cy: bbox.y + ty + bbox.height / 2
  };
}

function edgePoint(bbox, towardX, towardY) {
  const cx = bbox.cx, cy = bbox.cy;
  const dx = towardX - cx, dy = towardY - cy;
  const hw = bbox.width / 2, hh = bbox.height / 2;
  if (Math.abs(dx) * hh >= Math.abs(dy) * hw) {
    return { x: dx >= 0 ? bbox.x + bbox.width : bbox.x, y: cy };
  }
  return { x: cx, y: dy >= 0 ? bbox.y + bbox.height : bbox.y };
}

// --- Text Editing ---

function initTextEdit() {
  const canvas = document.getElementById('canvas');
  if (!canvas) return;

  canvas.addEventListener('dblclick', (e) => {
    const textEl = e.target.closest('text');
    if (!textEl) return;

    // Only edit text inside nodes
    const isNodeText = textEl.closest('[data-node-id]');
    if (!isNodeText) return;

    // Don't edit very small text (like type labels)
    const fontSize = parseFloat(getComputedStyle(textEl).fontSize);
    if (fontSize < 10) return;

    const svg = canvas.querySelector('svg');
    if (!svg) return;

    const bbox = textEl.getBBox();
    const ctm = svg.getScreenCTM();
    if (!ctm) return;

    const screenPt = svg.createSVGPoint();
    screenPt.x = bbox.x;
    screenPt.y = bbox.y;
    const screen = screenPt.matrixTransform(ctm);

    const input = document.createElement('input');
    input.type = 'text';
    input.value = textEl.textContent;
    input.style.cssText = `
      position: fixed;
      left: ${screen.x}px;
      top: ${screen.y - 4}px;
      width: ${Math.max(80, bbox.width + 20)}px;
      height: ${bbox.height + 8}px;
      font-size: ${fontSize}px;
      font-family: inherit;
      border: 2px solid #2563eb;
      border-radius: 4px;
      padding: 2px 4px;
      z-index: 10000;
      background: white;
      color: #111;
    `;
    document.body.appendChild(input);
    input.focus();
    input.select();

    const finish = () => {
      if (input.value.trim()) {
        textEl.textContent = input.value.trim();
      }
      input.remove();
    };

    input.addEventListener('blur', finish);
    input.addEventListener('keydown', (ke) => {
      if (ke.key === 'Enter') input.blur();
      if (ke.key === 'Escape') { input.value = textEl.textContent; input.blur(); }
    });
  });
}

// --- Export ---

function exportSVG() {
  const svg = document.querySelector('#canvas svg');
  if (!svg) return;
  const serializer = new XMLSerializer();
  let svgString = serializer.serializeToString(svg);
  svgString = '<?xml version="1.0" encoding="UTF-8"?>\n' + svgString;
  const blob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' });
  downloadBlob(blob, 'diagram.svg');
}

function exportPNG() {
  const svg = document.querySelector('#canvas svg');
  if (!svg) return;
  const serializer = new XMLSerializer();
  const svgString = serializer.serializeToString(svg);
  const viewBox = svg.viewBox.baseVal;
  const scale = 1920 / viewBox.width;
  const canvasEl = document.createElement('canvas');
  canvasEl.width = Math.round(viewBox.width * scale);
  canvasEl.height = Math.round(viewBox.height * scale);
  const ctx = canvasEl.getContext('2d');

  const blob = new Blob([svgString], { type: 'image/svg+xml;charset=utf-8' });
  const url = URL.createObjectURL(blob);
  const img = new Image();
  img.onload = () => {
    ctx.drawImage(img, 0, 0, canvasEl.width, canvasEl.height);
    URL.revokeObjectURL(url);
    canvasEl.toBlob((pngBlob) => {
      if (pngBlob) downloadBlob(pngBlob, 'diagram.png');
    }, 'image/png');
  };
  img.src = url;
}

function downloadBlob(blob, filename) {
  const url = URL.createObjectURL(blob);
  const a = document.createElement('a');
  a.href = url;
  a.download = filename;
  document.body.appendChild(a);
  a.click();
  document.body.removeChild(a);
  URL.revokeObjectURL(url);
}

// --- Init ---

function initPreview() {
  // Re-inject SVG BEFORE initializing handlers so they capture the correct reference
  const canvas = document.getElementById('canvas');
  const svg = canvas ? canvas.querySelector('svg') : null;
  if (svg && !document.querySelector('[data-node-id]')) {
    if (window._originalSVG) {
      canvas.innerHTML = window._originalSVG;
    }
  }

  initDrag();
  initTextEdit();

  // Apply default style on load
  switchStyle(currentStyleIndex);
}

document.addEventListener('DOMContentLoaded', initPreview);
