import React, { useCallback } from 'react';
import { useEditorStore } from '../store/editorStore';
import type { Element as ElementType } from '../types';

interface ElementProps {
  element: ElementType;
  children?: React.ReactNode;
  isRoot?: boolean;
}

export const Element = React.memo(function Element({ element, children, isRoot }: ElementProps) {
  const selection = useEditorStore((s) => s.selection?.nodeId === element.id);
  const isFrame = element.type === 'frame';
  const isSvg = [
    'svg', 'path', 'circle', 'rect', 'line', 'polyline', 'polygon', 'ellipse',
    'text', 'tspan', 'g', 'defs', 'stop', 'lineargradient', 'radialgradient',
    'clippath', 'mask', 'pattern', 'use', 'image', 'symbol',
  ].includes(element.tag);

  const styleLeft = element.style.left;
  const styleTop = element.style.top;
  const origPos = element.style.position;

  // Only force position:absolute when AI explicitly wrote it (left/top or position:absolute).
  // Everything else flows naturally — just like writing an HTML file.
  const hasExplicitAbsolute =
    origPos === 'absolute' ||
    origPos === 'fixed' ||
    (origPos !== 'relative' &&
     ((styleLeft !== undefined && styleLeft !== '0px' && styleLeft !== '0') ||
      (styleTop !== undefined && styleTop !== '0px' && styleTop !== '0')));

  // True when the element has no usable CSS positioning context and would be static flow.
  // In that case we inject position:relative at render time so the selection outline
  // (position:absolute; inset:0) stays contained inside this element.
  // This is a render-only change — it is never written to the store or backend.
  const needsSelectionPositionContext =
    !isSvg &&
    (!origPos || origPos === 'static') &&
    !hasExplicitAbsolute &&
    !isFrame &&
    !isRoot;

  const handleClick = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    const { selectElement, expandToNode } = useEditorStore.getState();
    selectElement({
      nodeId: element.id,
      x: parseFloat(element.style.left || '0'),
      y: parseFloat(element.style.top || '0'),
      width: parseFloat(element.style.width || '100'),
      height: parseFloat(element.style.height || '100'),
    });
    // Expand all ancestors in the layer tree so this element becomes visible
    expandToNode(element.id);
  }, [element.id, element.style.left, element.style.top, element.style.width, element.style.height]);

  const handleDoubleClick = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    if (element.text !== undefined) {
      const newText = prompt('Edit text:', element.text);
      if (newText !== null) {
        useEditorStore.getState().updateElement(element.id, { text: newText });
      }
    }
  }, [element.id, element.text]);

  // SVG attributes live in element.style (stored by parse_html.py _collect_attrs).
  // For SVG elements, they must be passed as DOM attributes — not CSS style —
  // otherwise they get ignored (r, cx on <circle>) or overridden (strokeWidth in style).
  // For non-SVG elements, everything stays in CSS style (width, height, background, etc.).
  const svgAttrKeys = new Set([
    'fill', 'fillRule', 'fillOpacity', 'floodOpacity',
    'stroke', 'strokeWidth', 'strokeLinecap', 'strokeLinejoin',
    'strokeDasharray', 'strokeOpacity', 'strokeMiterlimit',
    'opacity', 'clipPath', 'clipRule',
    'r', 'rx', 'ry', 'cx', 'cy', 'x', 'y', 'x1', 'y1', 'x2', 'y2',
    'd', 'points', 'pathLength',
    'viewBox', 'preserveAspectRatio',
    'fontFamily', 'fontSize', 'fontWeight', 'fontStyle', 'fontVariant',
    'textAnchor', 'dominantBaseline', 'letterSpacing', 'textDecoration',
    'transform', 'gradientTransform',
    'offset', 'stopColor', 'stopOpacity',
    'href', 'xmlns',
    'gradientUnits', 'spreadMethod',
    'patternUnits', 'patternContentUnits',
    'clipPathUnits',
    'maskUnits', 'maskContentUnits',
  ]);

  const svgAttrs: Record<string, string> = {};
  for (const key of svgAttrKeys) {
    const val = element.style[key as keyof typeof element.style];
    if (val !== undefined) svgAttrs[key] = val as string;
  }

  // SVG element CSS style: everything NOT an SVG attr (for the SVG's style= attribute)
  const svgElStyle: React.CSSProperties = {};
  for (const key of Object.keys(element.style)) {
    if (!svgAttrKeys.has(key)) {
      (svgElStyle as Record<string, unknown>)[key] = element.style[key as keyof typeof element.style];
    }
  }
  Object.assign(svgElStyle, { cursor: 'default', userSelect: 'none' });

  // Non-SVG (div/span) CSS style: ALL of element.style + positioning
  // Priority (last wins):
  //   1. element.style — AI-authored CSS
  //   2. cursor/userSelect overrides
  //   3. Known positioning contexts (root, explicit absolute, frame)
  //   4. Render-only position:relative for selection overlay — only fills the
  //      static/unpositioned case; never overrides explicit absolute/fixed/relative.
  const divStyle: React.CSSProperties = {
    ...element.style,
    cursor: 'default',
    userSelect: 'none',
    ...(isRoot
      ? { position: 'relative' as const, width: '100%' }
      : hasExplicitAbsolute
      ? { position: 'absolute' as const }
      : isFrame
      ? { position: 'relative' as const }
      : {}),
    // Render-only: inject positioning context for selection outline if element is static.
    // Must come last so it does not override explicit absolute/fixed/relative from above.
    ...(needsSelectionPositionContext && selection ? { position: 'relative' as const } : {}),
  };

  // ── Render SVG elements ──────────────────────────────────────────────────────
  if (isSvg) {
    const baseProps = {
      'data-paper-node': element.id,
      'data-paper-name': element.name,
      ...svgAttrs,
      style: svgElStyle,
      onClick: handleClick,
      onDoubleClick: handleDoubleClick,
    };

    if (element.tag === 'svg') {
      return (
        <svg
          {...baseProps}
          xmlns="http://www.w3.org/2000/svg"
          viewBox={svgAttrs.viewBox}
          width={svgAttrs.width}
          height={svgAttrs.height}
        >
          {element.text !== undefined && element.text !== null && element.text !== '' && (
            <span style={{ display: 'block', whiteSpace: 'pre-wrap' }}>{element.text}</span>
          )}
          {children}
        </svg>
      );
    }
    if (element.tag === 'circle') {
      return <circle {...baseProps} r={svgAttrs.r || '0'} cx={svgAttrs.cx || '0'} cy={svgAttrs.cy || '0'} />;
    }
    if (element.tag === 'ellipse') {
      return <ellipse {...baseProps} rx={svgAttrs.rx || '0'} ry={svgAttrs.ry || '0'} cx={svgAttrs.cx || '0'} cy={svgAttrs.cy || '0'} />;
    }
    if (element.tag === 'rect') {
      return <rect {...baseProps} rx={svgAttrs.rx || '0'} />;
    }
    if (element.tag === 'path') {
      return <path {...baseProps} d={svgAttrs.d || ''} />;
    }
    if (element.tag === 'line') {
      return <line {...baseProps} x1={svgAttrs.x1 || '0'} y1={svgAttrs.y1 || '0'} x2={svgAttrs.x2 || '0'} y2={svgAttrs.y2 || '0'} />;
    }
    if (element.tag === 'polyline') {
      return <polyline {...baseProps} points={svgAttrs.points || ''} />;
    }
    if (element.tag === 'polygon') {
      return <polygon {...baseProps} points={svgAttrs.points || ''} />;
    }
    if (element.tag === 'text') {
      return (
        <text {...baseProps}>
          {element.text}
          {children}
        </text>
      );
    }
    if (element.tag === 'tspan') {
      return <tspan {...baseProps}>{element.text}{children}</tspan>;
    }
    if (element.tag === 'g') {
      return (
        <g {...baseProps}>
          {children}
        </g>
      );
    }
    if (element.tag === 'defs') {
      return <defs {...baseProps}>{children}</defs>;
    }
    if (element.tag === 'stop') {
      return <stop {...baseProps} />;
    }
    if (element.tag === 'lineargradient') {
      return <linearGradient {...baseProps}>{children}</linearGradient>;
    }
    if (element.tag === 'radialgradient') {
      return <radialGradient {...baseProps}>{children}</radialGradient>;
    }
    if (element.tag === 'clippath') {
      return <clipPath {...baseProps}>{children}</clipPath>;
    }
    if (element.tag === 'mask') {
      return <mask {...baseProps}>{children}</mask>;
    }
    if (element.tag === 'pattern') {
      return <pattern {...baseProps}>{children}</pattern>;
    }
    if (element.tag === 'use') {
      return <use {...baseProps} href={svgAttrs.href || svgAttrs['xlink:href'] || ''} />;
    }
    if (element.tag === 'image') {
      return <image {...baseProps} href={svgAttrs.href || ''} />;
    }
    if (element.tag === 'symbol') {
      return <symbol {...baseProps}>{children}</symbol>;
    }
    // Fallback for unknown SVG tags — render as native SVG element
    return (
      <svg {...baseProps}>
        {children}
      </svg>
    );
  }

  return (
    <div
      data-paper-node={element.id}
      data-paper-name={element.name}
      style={divStyle}
      onClick={handleClick}
      onDoubleClick={handleDoubleClick}
    >
      {element.text !== undefined && element.text !== null && element.text !== '' && (
        <span style={{ display: 'block', whiteSpace: 'pre-wrap' }}>{element.text}</span>
      )}

      {/* Selection outline — visible for all selected non-SVG elements.
          For elements that are static/unpositioned, divStyle already injected
          position:relative above so this absolute overlay stays contained. */}
      {selection && (
        <div
          data-paper-ui
          style={{
            position: 'absolute', inset: 0,
            border: '1.5px solid #0066ff',
            pointerEvents: 'none', zIndex: 10,
          }}
        />
      )}

      {children}
    </div>
  );
});
