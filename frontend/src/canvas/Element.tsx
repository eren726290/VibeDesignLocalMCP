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
  const elementRef = useRef<HTMLDivElement>(null);

  const selection = useEditorStore((s) => s.selection?.nodeId === element.id);
  const isFrame = element.type === 'frame';

  const styleLeft = element.style.left;
  const styleTop = element.style.top;
  // Non-zero position: left/top are explicitly set to non-zero values
  const hasNonZeroPos = (styleLeft !== undefined && styleLeft !== '0px' && styleLeft !== '0') ||
                         (styleTop !== undefined && styleTop !== '0px' && styleTop !== '0');
  const origPos = element.style.position;
  // Root elements always need position:absolute (coordinate system relative to artboard).
  // Elements with text need to be block elements (to show the text with its style).
  // Non-root flex/grid children use their parent's layout context.
  // position:relative is also considered "positioned" so it participates in normal flow.
  const hasText = element.text !== undefined && element.text !== null && element.text !== '';
  const isPositioned = isFrame || isRoot || origPos === 'absolute' || origPos === 'fixed' || origPos === 'relative' || hasNonZeroPos || hasText;

  const handleClick = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    // Read visual position from DOM — works for both absolute and flex/grid elements
    const rect = elementRef.current?.getBoundingClientRect();
    const canvas = document.getElementById('paper-canvas');
    const canvasRect = canvas?.getBoundingClientRect();
    const x = rect && canvasRect ? rect.left - canvasRect.left : parseFloat(styleLeft || '0');
    const y = rect && canvasRect ? rect.top - canvasRect.top : parseFloat(styleTop || '0');
    useEditorStore.getState().setSelection({
      nodeId: element.id,
      x,
      y,
      width: parseFloat(element.style.width || '100'),
      height: parseFloat(element.style.height || '100'),
    });
  }, [element.id, element.style.width, element.style.height]);

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

  const style: React.CSSProperties = {
    ...element.style,
    ...(isRoot
      ? { position: 'absolute' as const, top: 0, left: 0, width: '100%', height: '100%' }  // fills artboard
      : isFrame
      ? { position: 'relative' as const }
      : hasNonZeroPos
      ? { position: 'absolute' as const }
      : {}),
    cursor: 'move',
    userSelect: 'none',
  };

  return (
    <div
      ref={elementRef}
      data-paper-node={element.id}
      data-paper-name={element.name}
      style={style}
      onClick={handleClick}
      onDoubleClick={handleDoubleClick}
    >
      {element.text !== undefined && (
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
