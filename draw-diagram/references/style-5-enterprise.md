# Style 5: Enterprise

Pure black-and-white industrial aesthetic. No colorful fills — monochrome, precise, print-ready.

## Color Palette

```
Background:     #ffffff  (pure white)
Primary text:   #0a0a0a  (near-black)
Secondary text: #4a4a4a  (dark gray)
Muted text:     #888888  (medium gray)
Border:         #1a1a1a  (near-black, strong)

Arrow colors (pure grayscale):
  Control:      #333333  (dark)
  Write/Read:   #555555  (medium-dark)
  Data:         #333333  (dark)
  Async:        #999999  (medium-light)
  Feedback:     #666666  (medium)
  Neutral:      #bbbbbb  (light)
```

## Typography

```
font-family: 'Helvetica Neue', Helvetica, Arial, 'PingFang SC', 'Microsoft YaHei', 'Microsoft JhengHei', 'SimHei', sans-serif
font-size:   18px node titles, 12px descriptions, 12px arrow labels
font-weight: 700 for titles, 500 for labels, 600 for arrow labels
```

System font stack for maximum compatibility. No custom fonts.

## Node Boxes

Sharp-cornered boxes with strong black borders:

```xml
<!-- Standard node -->
<rect x="100" y="100" width="180" height="76" rx="2" ry="2"
      fill="#ffffff" stroke="#1a1a1a" stroke-width="2"/>
```

**Key techniques:**
1. Pure white fill (`#ffffff`)
2. `rx="2"` — near-square corners, industrial/technical
3. `stroke-width: 2` — strong black borders
4. No shadows, no gradients, no decoration
5. No colorful fills — pure black-and-white

## Arrows

Thin, precise arrows in grayscale:

```xml
<defs>
  <marker id="arrowA" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
    <polygon points="0 0, 10 3.5, 0 7" fill="#333333"/>
  </marker>
</defs>

<!-- Control flow -->
<line x1="280" y1="140" x2="400" y2="140"
      stroke="#333333" stroke-width="1.5" marker-end="url(#arrowA)"/>
```

## Arrow Labels

Small, dark labels on white background:

```xml
<rect x="310" y="122" width="60" height="16" rx="2"
      fill="#ffffff" opacity="0.95"/>
<text x="340" y="133" text-anchor="middle" fill="#4a4a4a" font-size="12" font-weight="600">
  label
</text>
```

## Grouping Containers

Sharp dashed containers:

```xml
<rect x="80" y="80" width="400" height="200" rx="2" ry="2"
      fill="none" stroke="#1a1a1a" stroke-width="1.4" stroke-dasharray="4 3"/>
<text x="98" y="104" fill="#4a4a4a" font-size="13" font-weight="700">
  Section Label
</text>
```

## Layout Principles

**Industrial precision:**
- Left-aligned title with thin divider line
- Section labels in natural case
- Consistent spacing, generous whitespace
- All coordinates snap to clean values

**Enterprise professionalism:**
- Pure black-and-white — NO colorful fills
- Near-square corners (`rx=2`) — technical, industrial
- Thin strokes — print-friendly
- Minimal decoration — content-first design
- White background — suitable for documents and printing

## SVG Template

```xml
<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 960 600" width="960" height="600">
  <style>
    /* NO @import — rsvg-convert cannot fetch external URLs */
    text { font-family: 'Helvetica Neue', Helvetica, Arial, 'PingFang SC', 'Microsoft YaHei', 'Microsoft JhengHei', 'SimHei', sans-serif; }
  </style>
  <defs>
    <marker id="arrowA" markerWidth="10" markerHeight="7" refX="9" refY="3.5" orient="auto">
      <polygon points="0 0, 10 3.5, 0 7" fill="#333333"/>
    </marker>
  </defs>

  <!-- White background -->
  <rect width="960" height="600" fill="#ffffff"/>

  <!-- Left-aligned title -->
  <text x="48" y="48" text-anchor="start" fill="#0a0a0a"
        font-size="22" font-weight="700">Diagram Title</text>
  <text x="48" y="72" text-anchor="start" fill="#666666"
        font-size="12" font-weight="500">Subtitle description</text>
  <line x1="48" y1="82" x2="912" y2="82" stroke="#1a1a1a" stroke-width="1"/>

  <!-- Standard node -->
  <rect x="100" y="120" width="180" height="76" rx="2" ry="2"
        fill="#ffffff" stroke="#1a1a1a" stroke-width="2"/>
  <text x="190" y="158" text-anchor="middle" fill="#0a0a0a"
        font-size="18" font-weight="700">Component</text>

  <!-- Connection -->
  <line x1="280" y1="158" x2="400" y2="158"
        stroke="#333333" stroke-width="1.5" marker-end="url(#arrowA)"/>
</svg>
```

## Design Philosophy

Enterprise style emphasizes:
- **Industrial precision**: Pure black-and-white, no color
- **Print-readiness**: White background, thin strokes, no visual effects
- **Technical clarity**: Strong borders, sharp corners, clear hierarchy
- **Minimalism**: Content-first, zero decoration

Avoid:
- Any colorful fills or accents
- Rounded corners (>2px)
- Shadows and gradients
- Decorative elements
