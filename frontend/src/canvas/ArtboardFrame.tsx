import React, { useRef, useState, useCallback, useEffect } from 'react';
import { useEditorStore } from '../store/editorStore';
import { Element } from './Element';
import type { Element as ElementType, Page } from '../types';

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

interface DragState {
  startMX: number;
  startMY: number;
  origX: number;
  origY: number;
}

export function ArtboardFrame({ page, elementsMap }: { page: Page; elementsMap: Map<string, ElementType> }) {
  const { selectedArtboardId, selectArtboard, updateArtboard } = useEditorStore();
  const isSelected = selectedArtboardId === page.id;
  const frameRef = useRef<HTMLDivElement>(null);
  const dragRef = useRef<DragState | null>(null);

  // Resize state
  const [resizing, setResizing] = useState<{
    handle: Handle;
    startMX: number; startMY: number;
    startW: number; startH: number;
    startX: number; startY: number;
  } | null>(null);

  // Click to select artboard
  const handleSelect = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    selectArtboard(page.id);
  }, [page.id, selectArtboard]);

  // Drag by header
  const handleDragStart = useCallback((e: React.MouseEvent) => {
    if (e.button !== 0) return;
    e.stopPropagation();
    selectArtboard(page.id);
    dragRef.current = { startMX: e.clientX, startMY: e.clientY, origX: page.x, origY: page.y };
    window.addEventListener('mousemove', handleDragMove);
    window.addEventListener('mouseup', handleDragEnd);
  }, [page.id, page.x, page.y, selectArtboard]);

  const handleDragMove = useCallback((e: MouseEvent) => {
    if (!dragRef.current) return;
    const dx = e.clientX - dragRef.current.startMX;
    const dy = e.clientY - dragRef.current.startMY;
    const scale = useEditorStore.getState().transform.scale;
    const newX = Math.round(dragRef.current.origX + dx / scale);
    const newY = Math.round(dragRef.current.origY + dy / scale);
    if (frameRef.current) {
      frameRef.current.style.left = `${newX}px`;
      frameRef.current.style.top = `${newY}px`;
    }
  }, []);

  const handleDragEnd = useCallback((e: MouseEvent) => {
    if (!dragRef.current) return;
    const dx = e.clientX - dragRef.current.startMX;
    const dy = e.clientY - dragRef.current.startMY;
    const scale = useEditorStore.getState().transform.scale;
    const newX = Math.round(dragRef.current.origX + dx / scale);
    const newY = Math.round(dragRef.current.origY + dy / scale);
    updateArtboard(page.id, { x: newX, y: newY });
    dragRef.current = null;
    window.removeEventListener('mousemove', handleDragMove);
    window.removeEventListener('mouseup', handleDragEnd);
  }, [page.id, handleDragMove, updateArtboard]);

  // Resize handles
  const handleResizeStart = useCallback((e: React.MouseEvent, handle: Handle) => {
    e.stopPropagation();
    e.preventDefault();
    setResizing({
      handle,
      startMX: e.clientX,
      startMY: e.clientY,
      startW: page.width,
      startH: page.height,
      startX: page.x,
      startY: page.y,
    });
  }, [page.width, page.height, page.x, page.y]);

  useEffect(() => {
    if (!resizing) return;

    const handleMove = (e: MouseEvent) => {
      const dx = e.clientX - resizing.startMX;
      const dy = e.clientY - resizing.startMY;
      const scale = useEditorStore.getState().transform.scale;
      const adx = dx / scale;
      const ady = dy / scale;
      const h = resizing.handle;

      let newW = resizing.startW, newH = resizing.startH, newX = resizing.startX, newY = resizing.startY;
      if (h.includes('e')) newW = Math.max(50, resizing.startW + adx);
      if (h.includes('s')) newH = Math.max(50, resizing.startH + ady);
      if (h.includes('w')) { newW = Math.max(50, resizing.startW - adx); newX = resizing.startX + resizing.startW - newW; }
      if (h.includes('n')) { newH = Math.max(50, resizing.startH - ady); newY = resizing.startY + resizing.startH - newH; }

      if (frameRef.current) {
        frameRef.current.style.width = `${newW}px`;
        frameRef.current.style.height = `${newH}px`;
        frameRef.current.style.left = `${newX}px`;
        frameRef.current.style.top = `${newY}px`;
      }
    };

    const handleUp = (e: MouseEvent) => {
      const dx = e.clientX - resizing.startMX;
      const dy = e.clientY - resizing.startMY;
      const scale = useEditorStore.getState().transform.scale;
      const adx = dx / scale;
      const ady = dy / scale;
      const h = resizing.handle;

      let newW = resizing.startW, newH = resizing.startH, newX = resizing.startX, newY = resizing.startY;
      if (h.includes('e')) newW = Math.max(50, resizing.startW + adx);
      if (h.includes('s')) newH = Math.max(50, resizing.startH + ady);
      if (h.includes('w')) { newW = Math.max(50, resizing.startW - adx); newX = resizing.startX + resizing.startW - newW; }
      if (h.includes('n')) { newH = Math.max(50, resizing.startH - ady); newY = resizing.startY + resizing.startH - newH; }

      updateArtboard(page.id, { x: Math.round(newX), y: Math.round(newY), width: Math.round(newW), height: Math.round(newH) });
      setResizing(null);
      window.removeEventListener('mousemove', handleMove);
      window.removeEventListener('mouseup', handleUp);
    };

    window.addEventListener('mousemove', handleMove);
    window.addEventListener('mouseup', handleUp);
    return () => {
      window.removeEventListener('mousemove', handleMove);
      window.removeEventListener('mouseup', handleUp);
    };
  }, [resizing, page.id, updateArtboard]);

  const roots = page.elements.filter((el) => !el.parentId);

  return (
    // Outer wrapper: positions the artboard on the canvas (frameRef tracks this for drag/resize)
    <div
      ref={frameRef}
      style={{
        position: 'absolute',
        left: page.x,
        top: page.y,
        width: page.width,
        height: page.height,
      }}
    >
      {/* Inner frame: acts as positioning context for absolute-positioned children */}
      <div
        onClick={handleSelect}
        style={{
          position: 'relative',
          width: '100%',
          height: '100%',
          background: page.backgroundColor || '#ffffff',
          boxShadow: isSelected
            ? '0 0 0 2px #0066ff, 0 4px 24px rgba(0,0,0,0.4)'
            : '0 4px 24px rgba(0,0,0,0.3)',
          overflow: 'visible',
        }}
      >
      {/* Header - drag handle */}
      <div
        onMouseDown={handleDragStart}
        style={{
          position: 'absolute',
          top: -28,
          left: 0,
          right: 0,
          height: 24,
          background: isSelected ? '#0066ff' : '#444',
          borderRadius: '4px 4px 0 0',
          display: 'flex',
          alignItems: 'center',
          paddingLeft: 8,
          paddingRight: 4,
          cursor: 'move',
          fontSize: 10,
          color: '#fff',
          fontFamily: 'system-ui, sans-serif',
          userSelect: 'none',
          zIndex: 20,
        }}
      >
        <span style={{ flex: 1, overflow: 'hidden', textOverflow: 'ellipsis', whiteSpace: 'nowrap' }}>
          {page.name} · {page.width}×{page.height}
        </span>
        <span
          onClick={(e) => { e.stopPropagation(); selectArtboard(null); }}
          style={{ cursor: 'pointer', opacity: 0.7, flexShrink: 0 }}
        >✕</span>
      </div>

      {/* Artboard elements */}
      {roots.map((el) => (
        <ElementNode key={el.id} element={el} elementsMap={elementsMap} isRoot />
      ))}

      {/* Selection border */}
      {isSelected && (
        <div style={{
          position: 'absolute', inset: 0,
          border: '2px solid #0066ff',
          pointerEvents: 'none', zIndex: 10,
        }} />
      )}

      {/* Resize handles */}
      {isSelected && HANDLES.map((h) => (
        <div
          key={h}
          onMouseDown={(e) => handleResizeStart(e, h)}
          style={{
            position: 'absolute', width: 8, height: 8,
            background: '#fff', border: '2px solid #0066ff',
            borderRadius: 1, zIndex: 15, ...HANDLE_STYLE[h],
          }}
        />
      ))}
    </div>
    {/* Close outer wrapper */}
    </div>
  );
}

function getChildIds(elementId: string, elementsMap: Map<string, ElementType>): ElementType[] {
  const children: ElementType[] = [];
  for (const el of elementsMap.values()) {
    if (el.parentId === elementId) children.push(el);
  }
  return children;
}

function ElementNode({ element, elementsMap, inSvg = false }: { element: ElementType; elementsMap: Map<string, ElementType>; isRoot?: boolean; inSvg?: boolean }) {
  const children = getChildIds(element.id, elementsMap);

  // Elements with text always go to positionedChildren (they need to render as block
  // divs to show their style — inline spans strip border-radius, padding, etc.)
  // Elements with children also go to positionedChildren (render their own sub-tree).
  // Flex/grid layout children without text/children: render as empty placeholder spans.
  const inlineTexts: string[] = [];
  const positionedChildren: ElementType[] = [];

  // If this element is inside an SVG (passed down from parent), or IS an SVG itself,
  // ALL children must go to positionedChildren — they need to render as <circle>/<path>,
  // not as inline <span> (SVG rejects <span>).
  const insideSvg = inSvg || element.tag === 'svg';

  for (const child of children) {
    const hasLayout = !!(child.style?.width || child.style?.height ||
      child.style?.position === 'absolute' || child.style?.position === 'relative');
    const hasText = child.text !== undefined && child.text !== null && child.text !== '';
    const childChildren = getChildIds(child.id, elementsMap);
    if (!hasLayout && !hasText && childChildren.length === 0 && !insideSvg) {
      // Truly inline placeholder: no layout, no text, no children, and not inside SVG
      inlineTexts.push('');
    } else {
      positionedChildren.push(child);
    }
  }

  // SVG container tags that must pass inSvg=true to their children.
  // All SVG child elements (stop, circle inside defs, etc.) need to render as
  // SVG elements, not as inline <span> placeholders.
  const svgContainerTags = new Set([
    'svg', 'g', 'defs', 'lineargradient', 'radialgradient',
    'clippath', 'mask', 'pattern', 'symbol',
  ]);

  // SVG parent: children must be direct (no wrapper div) so they render as <circle>/<path> inside <svg>
  const isSvgContainer = svgContainerTags.has(element.tag);
  const renderedChildren = positionedChildren.map((child) =>
    isSvgContainer ? (
      // Pass inSvg=true so stop/circle/path inside defs/gradient/etc. render as SVG elements
      <ElementNode key={child.id} element={child} elementsMap={elementsMap} inSvg={true} />
    ) : (
      // Wrap in a div with stopPropagation — prevents clicks on this child
      // from bubbling up to the parent Element's onClick handler
      <div key={child.id} onClick={(e) => e.stopPropagation()}>
        <ElementNode element={child} elementsMap={elementsMap} />
      </div>
    )
  );

  return (
    <Element key={element.id} element={element}>
      {renderedChildren}
      {/* Inline text children rendered as inline spans to preserve per-element styling */}
      {inlineTexts.map((t, i) => (
        <span key={`text-${i}`}>{t}</span>
      ))}
    </Element>
  );
}
