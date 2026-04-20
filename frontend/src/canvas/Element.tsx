import React, { useRef, useCallback } from 'react';
import { useEditorStore } from '../store/editorStore';
import type { Element as ElementType } from '../types';

interface ElementProps {
  element: ElementType;
  children?: React.ReactNode;
  isRoot?: boolean;
}

// Resize handle positions
type Handle = 'nw' | 'n' | 'ne' | 'e' | 'se' | 's' | 'sw' | 'w';

const HANDLES: Handle[] = ['nw', 'n', 'ne', 'e', 'se', 's', 'sw', 'w'];

const HANDLE_STYLE: Record<Handle, React.CSSProperties> = {
  nw: { top: -4, left: -4, cursor: 'nw-resize' },
  n: { top: -4, left: '50%', transform: 'translateX(-50%)', cursor: 'n-resize' },
  ne: { top: -4, right: -4, cursor: 'ne-resize' },
  e: { top: '50%', right: -4, transform: 'translateY(-50%)', cursor: 'e-resize' },
  se: { bottom: -4, right: -4, cursor: 'se-resize' },
  s: { bottom: -4, left: '50%', transform: 'translateX(-50%)', cursor: 's-resize' },
  sw: { bottom: -4, left: -4, cursor: 'sw-resize' },
  w: { top: '50%', left: -4, transform: 'translateY(-50%)', cursor: 'w-resize' },
};

export const Element = React.memo(function Element({ element, children, isRoot }: ElementProps) {
  const elementRef = useRef<HTMLElement>(null);

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

  const hasText = element.text !== undefined && element.text !== null && element.text !== '';
  // Needs a stacking context if: frame, AI explicitly absolute, or has text (block element)
  const isPositioned = isFrame || origPos === 'absolute' || origPos === 'fixed' || hasExplicitAbsolute || hasText;

  const handleClick = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    const { setSelection, expandToNode } = useEditorStore.getState();
    setSelection({
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

  const resizingRef = useRef<{
    handle: Handle;
    startMX: number; startMY: number;
    startW: number; startH: number;
    startElX: number; startElY: number;
  } | null>(null);

  const handleResizeMouseDown = useCallback((e: React.MouseEvent, handle: Handle) => {
    e.stopPropagation();
    e.preventDefault();
    resizingRef.current = {
      handle,
      startMX: e.clientX,
      startMY: e.clientY,
      startW: parseFloat(element.style.width || '100'),
      startH: parseFloat(element.style.height || '100'),
      startElX: parseFloat(styleLeft || '0'),
      startElY: parseFloat(styleTop || '0'),
    };
    window.addEventListener('mousemove', handleResizeMove);
    window.addEventListener('mouseup', handleResizeEnd);
  }, [element.style.width, element.style.height]);

  const handleResizeMove = useCallback((e: MouseEvent) => {
    const r = resizingRef.current;
    if (!r || !elementRef.current) return;
    const scale = useEditorStore.getState().transform.scale;
    const dx = (e.clientX - r.startMX) / scale;
    const dy = (e.clientY - r.startMY) / scale;

    let newW = r.startW, newH = r.startH, newX = r.startElX, newY = r.startElY;
    if (r.handle.includes('e')) newW = Math.max(20, r.startW + dx);
    if (r.handle.includes('s')) newH = Math.max(20, r.startH + dy);
    if (r.handle.includes('w')) { newW = Math.max(20, r.startW - dx); newX = r.startElX + r.startW - newW; }
    if (r.handle.includes('n')) { newH = Math.max(20, r.startH - dy); newY = r.startElY + r.startH - newH; }

    // Update DOM directly — no store, no disk write during drag
    elementRef.current!.style.width = `${newW}px`;
    elementRef.current!.style.height = `${newH}px`;
    elementRef.current!.style.left = `${newX}px`;
    elementRef.current!.style.top = `${newY}px`;
  }, []);

  const handleResizeEnd = useCallback((e: MouseEvent) => {
    const r = resizingRef.current;
    resizingRef.current = null;
    window.removeEventListener('mousemove', handleResizeMove);
    window.removeEventListener('mouseup', handleResizeEnd);
    if (!r) return;

    const scale = useEditorStore.getState().transform.scale;
    const dx = (e.clientX - r.startMX) / scale;
    const dy = (e.clientY - r.startMY) / scale;

    let newW = r.startW, newH = r.startH, newX = r.startElX, newY = r.startElY;
    if (r.handle.includes('e')) newW = Math.max(20, r.startW + dx);
    if (r.handle.includes('s')) newH = Math.max(20, r.startH + dy);
    if (r.handle.includes('w')) { newW = Math.max(20, r.startW - dx); newX = r.startElX + r.startW - newW; }
    if (r.handle.includes('n')) { newH = Math.max(20, r.startH - dy); newY = r.startElY + r.startH - newH; }

    // Sync to store + backend once on mouseup (with pause/resume)
    useEditorStore.getState().updateElement(element.id, {
      style: { ...element.style, width: `${newW}px`, height: `${newH}px`, left: `${newX}px`, top: `${newY}px` },
    });
  }, [element.id, element.style]);

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
  Object.assign(svgElStyle, { cursor: 'move', userSelect: 'none' });

  // Non-SVG (div/span) CSS style: ALL of element.style + positioning
  const divStyle: React.CSSProperties = {
    ...element.style,
    cursor: 'move',
    userSelect: 'none',
    ...(isRoot
      ? { position: 'relative' as const, width: '100%' }
      : hasExplicitAbsolute
      ? { position: 'absolute' as const }
      : isFrame
      ? { position: 'relative' as const }
      : {}),
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
      ref={elementRef as React.RefObject<HTMLDivElement>}
      data-paper-node={element.id}
      data-paper-name={element.name}
      style={divStyle}
      onClick={handleClick}
      onDoubleClick={handleDoubleClick}
    >
      {element.text !== undefined && element.text !== null && element.text !== '' && (
        <span style={{ display: 'block', whiteSpace: 'pre-wrap' }}>{element.text}</span>
      )}

      {selection && isPositioned && (
        <>
          <div style={{
            position: 'absolute', inset: 0, border: '1.5px solid #0066ff',
            pointerEvents: 'none', zIndex: 10,
          }} />
          {HANDLES.map((h) => (
            <div
              key={h}
              onMouseDown={(e) => handleResizeMouseDown(e, h)}
              style={{
                position: 'absolute', width: 8, height: 8,
                background: '#fff', border: '1px solid #0066ff', borderRadius: 1,
                zIndex: 11, ...HANDLE_STYLE[h],
              }}
            />
          ))}
        </>
      )}

      {children}
    </div>
  );
});
