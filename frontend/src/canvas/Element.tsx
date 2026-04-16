import React, { useRef, useCallback, useState, useEffect } from 'react';
import { useEditorStore } from '../store/editorStore';
import type { Element as ElementType } from '../types';

interface ElementProps {
  element: ElementType;
  children?: React.ReactNode;
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

export const Element = React.memo(function Element({ element, children }: ElementProps) {
  const elementRef = useRef<HTMLDivElement>(null);
  // Visual offset applied directly to DOM during drag (avoids store updates)
  const visualOffsetRef = useRef({ left: 0, top: 0 });
  const [resizing, setResizing] = useState<{
    handle: Handle; startX: number; startY: number;
    startW: number; startH: number; startElX: number; startElY: number;
  } | null>(null);

  const selection = useEditorStore((s) => s.selection?.nodeId === element.id);
  const isFrame = element.type === 'frame';

  const styleLeft = element.style.left || '0';
  const styleTop = element.style.top || '0';

  const handleClick = useCallback((e: React.MouseEvent) => {
    e.stopPropagation();
    useEditorStore.getState().setSelection({
      nodeId: element.id,
      x: parseFloat(styleLeft),
      y: parseFloat(styleTop),
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

  const handleResizeMouseDown = useCallback((e: React.MouseEvent, handle: Handle) => {
    e.stopPropagation();
    e.preventDefault();
    setResizing({
      handle,
      startX: e.clientX,
      startY: e.clientY,
      startW: parseFloat(element.style.width || '100'),
      startH: parseFloat(element.style.height || '100'),
      startElX: parseFloat(styleLeft),
      startElY: parseFloat(styleTop),
    });
  }, [element.style.width, element.style.height, styleLeft, styleTop]);

  useEffect(() => {
    if (!resizing) return;

    const handleMouseMove = (e: MouseEvent) => {
      const state = useEditorStore.getState();
      const currentEl = state.document?.pages[state.document.current_page].elements.find((el) => el.id === element.id);
      if (!currentEl) return;
      const dx = e.clientX - resizing.startX;
      const dy = e.clientY - resizing.startY;
      const h = resizing.handle;

      let newW = resizing.startW, newH = resizing.startH, newX = resizing.startElX, newY = resizing.startElY;
      if (h.includes('e')) newW = Math.max(20, resizing.startW + dx);
      if (h.includes('s')) newH = Math.max(20, resizing.startH + dy);
      if (h.includes('w')) { newW = Math.max(20, resizing.startW - dx); newX = resizing.startElX + resizing.startW - newW; }
      if (h.includes('n')) { newH = Math.max(20, resizing.startH - dy); newY = resizing.startElY + resizing.startH - newH; }

      state.updateElement(element.id, {
        style: { ...currentEl.style, width: `${newW}px`, height: `${newH}px`, left: `${newX}px`, top: `${newY}px` },
      });
    };

    const handleMouseUp = () => setResizing(null);
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    return () => {
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
    };
  }, [resizing, element.id]);

  // Apply visual offset during drag (direct DOM update, no store)
  const left = parseFloat(styleLeft) + visualOffsetRef.current.left;
  const top = parseFloat(styleTop) + visualOffsetRef.current.top;

  const style: React.CSSProperties = {
    position: isFrame ? 'relative' : 'absolute',
    ...element.style,
    left: `${left}px`,
    top: `${top}px`,
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

      {selection && (
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
