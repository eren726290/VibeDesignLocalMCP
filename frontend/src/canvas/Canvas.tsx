import { useRef, useEffect, useState, useMemo, useCallback } from 'react';
import { useEditorStore } from '../store/editorStore';
import { bridge } from '../bridge/api';
import { ArtboardFrame } from './ArtboardFrame';
import type { Element as ElementType } from '../types';

// ─── Canvas ─────────────────────────────────────────────────────────────────────

export function Canvas() {
  const canvasRef = useRef<HTMLDivElement>(null);
  const [isPanning, setIsPanning] = useState(false);
  const [preview, setPreview] = useState<{
    x: number;
    y: number;
    w: number;
    h: number;
  } | null>(null);

  // All mutable state for event handlers — avoids stale closures
  const drawRef = useRef<{
    active: boolean;
    startX: number;
    startY: number;
  } | null>(null);
  const isPanningRef = useRef(false);
  const panStartRef = useRef({ x: 0, y: 0 });
  const dragRef = useRef<{
    nodeId: string;
    startX: number;
    startY: number;
    elX: number;
    elY: number;
    didDrag: boolean;
  } | null>(null);

  const spaceDown = useEditorStore((s) => s.spaceDown);
  const transform = useEditorStore((s) => s.transform);
  const activeTool = useEditorStore((s) => s.activeTool);
  const setTransform = useEditorStore((s) => s.setTransform);
  const doc = useEditorStore((s) => s.document);

  // Build elementsMap from ALL pages, roots per page
  const { elementsMap } = useMemo(() => {
    const map = new Map<string, ElementType>();
    if (!doc) return { elementsMap: map };

    for (const page of doc.pages) {
      for (const el of page.elements) {
        map.set(el.id, el);
      }
    }
    console.log('[Canvas elementsMap] built, size=', map.size, 'svg elements:', [...map.values()].filter(e => e.tag === 'svg').map(e => e.id));
    return { elementsMap: map };
  }, [doc]);

  // ── Canvas events — registered once at mount, no dependency array re-runs ──
  useEffect(() => {
    const canvas = canvasRef.current;
    if (!canvas) return;

    const getTransform = () => useEditorStore.getState().transform;

    const getCanvasCoords = (clientX: number, clientY: number) => {
      const rect = canvas.getBoundingClientRect();
      const { translateX, translateY, scale } = getTransform();
      return {
        x: (clientX - rect.left - translateX) / scale,
        y: (clientY - rect.top - translateY) / scale,
      };
    };

    const handleMouseDown = (e: MouseEvent) => {
      const { activeTool } = useEditorStore.getState();
      // Middle button or pan tool → start pan
      if (e.button === 1 || (e.button === 0 && activeTool === 'pan')) {
        isPanningRef.current = true;
        const { translateX, translateY } = getTransform();
        panStartRef.current = {
          x: e.clientX - translateX,
          y: e.clientY - translateY,
        };
        setIsPanning(true);
        return;
      }

      // Left click on element → prepare drag (thresholded in mousemove)
      if (e.button === 0 && activeTool === 'select') {
        const target = e.target as HTMLElement;
        const node = target.closest('[data-paper-node]') as HTMLElement | null;
        if (node) {
          const nodeId = node.getAttribute('data-paper-node');
          if (nodeId) {
            // Read current DOM position safely — node.style.left is empty for flow elements
            const rawLeft = node.style.left;
            const rawTop = node.style.top;
            dragRef.current = {
              nodeId,
              startX: e.clientX,
              startY: e.clientY,
              elX: parseFloat(rawLeft) || 0,
              elY: parseFloat(rawTop) || 0,
              didDrag: false,
            };
            return;
          }
        }
        // Left click on empty canvas → deselect
        useEditorStore.getState().setSelection(null);
        return;
      }

      // Left click with drawing tool → start draw
      if (e.button === 0 && activeTool !== 'select' && activeTool !== 'pan') {
        const { x, y } = getCanvasCoords(e.clientX, e.clientY);
        drawRef.current = { active: true, startX: x, startY: y };
        setPreview({ x, y, w: 0, h: 0 });
      }
    };

    const handleMouseMove = (e: MouseEvent) => {
      // Pan
      if (e.buttons === 1 && isPanningRef.current) {
        setTransform({
          translateX: e.clientX - panStartRef.current.x,
          translateY: e.clientY - panStartRef.current.y,
        });
        return;
      }

      // Drag element — threshold: only start DOM manipulation after 3px movement
      const DRAG_THRESHOLD = 3;
      if (e.buttons === 1 && dragRef.current) {
        const dx = e.clientX - dragRef.current.startX;
        const dy = e.clientY - dragRef.current.startY;
        // Activate drag only after threshold exceeded
        if (!dragRef.current.didDrag && (Math.abs(dx) > DRAG_THRESHOLD || Math.abs(dy) > DRAG_THRESHOLD)) {
          dragRef.current.didDrag = true;
        }
        if (dragRef.current.didDrag) {
          const { scale } = useEditorStore.getState().transform;
          const adx = dx / scale;
          const ady = dy / scale;
          const node = document.querySelector(`[data-paper-node="${dragRef.current.nodeId}"]`) as HTMLElement | null;
          if (node) {
            node.style.left = `${dragRef.current.elX + adx}px`;
            node.style.top = `${dragRef.current.elY + ady}px`;
          }
        }
        return;
      }

      // Draw preview
      if (drawRef.current?.active) {
        const { x, y } = getCanvasCoords(e.clientX, e.clientY);
        const sx = drawRef.current.startX;
        const sy = drawRef.current.startY;
        setPreview({
          x: Math.min(sx, x),
          y: Math.min(sy, y),
          w: Math.abs(x - sx),
          h: Math.abs(y - sy),
        });
      }
    };

    const handleMouseUp = (e: MouseEvent) => {
      // End pan
      if (isPanningRef.current) {
        isPanningRef.current = false;
        setIsPanning(false);
        return;
      }

      // End drag → write final position to store only if threshold was exceeded
      if (dragRef.current) {
        const didDrag = dragRef.current.didDrag;
        const nodeId = dragRef.current.nodeId;
        if (didDrag) {
          const { transform, document: doc, updateElement } = useEditorStore.getState();
          const scale = transform.scale;
          const dx = (e.clientX - dragRef.current.startX) / scale;
          const dy = (e.clientY - dragRef.current.startY) / scale;
          const finalX = isNaN(dragRef.current.elX) ? 0 : dragRef.current.elX + dx;
          const finalY = isNaN(dragRef.current.elY) ? 0 : dragRef.current.elY + dy;
          if (doc) {
            const el = doc.pages[doc.current_page].elements.find((el) => el.id === nodeId);
            if (el) {
              updateElement(nodeId, {
                style: { ...el.style, left: `${finalX}px`, top: `${finalY}px` },
              });
            }
          }
        }
        dragRef.current = null;
        return;
      }

      // End draw → create element
      if (drawRef.current?.active) {
        const { x, y } = getCanvasCoords(e.clientX, e.clientY);
        const sx = drawRef.current.startX;
        const sy = drawRef.current.startY;
        const ex = Math.min(sx, x);
        const ey = Math.min(sy, y);
        const ew = Math.abs(x - sx);
        const eh = Math.abs(y - sy);
        drawRef.current = null;
        setPreview(null);
        if (ew < 5 || eh < 5) return;

        const { activeTool, document: doc, addElement, addChild } =
          useEditorStore.getState();
        if (!doc) return;

        // Find parent frame — read visual position from DOM (not store, which may be stale after drag)
        let parentFrameId: string | null = null;
        const frames = doc.pages[doc.current_page].elements.filter(
          (el) => el.type === 'frame'
        );
        let smallestArea = Infinity;
        for (const frame of frames) {
          const frameNode = document.querySelector(`[data-paper-node="${frame.id}"]`) as HTMLElement | null;
          const fl = frameNode ? parseFloat(frameNode.style.left) || 0 : parseFloat(frame.style.left || '0');
          const ft = frameNode ? parseFloat(frameNode.style.top) || 0 : parseFloat(frame.style.top || '0');
          const fw = frameNode ? parseFloat(frameNode.style.width) || 0 : parseFloat(frame.style.width || '0');
          const fh = frameNode ? parseFloat(frameNode.style.height) || 0 : parseFloat(frame.style.height || '0');
          if (fl === 0 && ft === 0 && fw === 0 && fh === 0) continue;
          if (sx >= fl && sx <= fl + fw && sy >= ft && sy <= ft + fh) {
            const area = fw * fh;
            if (area < smallestArea) {
              smallestArea = area;
              parentFrameId = frame.id;
            }
          }
        }

        let newElement: ElementType | null = null;
        if (activeTool === 'frame') {
          newElement = {
            id: `n-${Date.now().toString(36)}`,
            name: 'Frame',
            tag: 'div',
            type: 'frame',
            style: {
              position: 'absolute',
              left: `${ex}px`,
              top: `${ey}px`,
              width: `${ew}px`,
              height: `${eh}px`,
              backgroundColor: '#ffffff',
            },
          };
        } else if (activeTool === 'rectangle') {
          newElement = {
            id: `n-${Date.now().toString(36)}`,
            name: 'Rectangle',
            tag: 'div',
            type: 'rectangle',
            style: {
              position: 'absolute',
              left: `${ex}px`,
              top: `${ey}px`,
              width: `${ew}px`,
              height: `${eh}px`,
              backgroundColor: '#ffffff',
            },
          };
        } else if (activeTool === 'text') {
          newElement = {
            id: `n-${Date.now().toString(36)}`,
            name: 'Text',
            tag: 'div',
            type: 'text',
            style: {
              position: 'absolute',
              left: `${ex}px`,
              top: `${ey}px`,
              width: `${ew}px`,
              height: `${eh}px`,
              fontSize: '16px',
              fontFamily: 'system-ui, sans-serif',
              color: '#222222',
            },
            text: 'Text',
          };
        }

        if (newElement) {
          const withParent = parentFrameId
            ? { ...newElement, parentId: parentFrameId }
            : newElement;
          addElement(withParent);
          if (parentFrameId) addChild(parentFrameId, newElement.id);
        }
      }
    };

    const handleWheel = (e: WheelEvent) => {
      if (!e.metaKey && !e.ctrlKey) return;
      e.preventDefault();
      const { translateX, translateY, scale } = getTransform();
      const rect = canvas.getBoundingClientRect();
      const delta = e.deltaY > 0 ? 0.9 : 1.1;
      const newScale = Math.min(Math.max(scale * delta, 0.1), 10);
      const mx = e.clientX - rect.left;
      const my = e.clientY - rect.top;
      const sc = newScale / scale;
      setTransform({
        scale: newScale,
        translateX: mx - (mx - translateX) * sc,
        translateY: my - (my - translateY) * sc,
      });
    };

    canvas.addEventListener('mousedown', handleMouseDown);
    window.addEventListener('mousemove', handleMouseMove);
    window.addEventListener('mouseup', handleMouseUp);
    canvas.addEventListener('wheel', handleWheel, { passive: false });

    return () => {
      canvas.removeEventListener('mousedown', handleMouseDown);
      window.removeEventListener('mousemove', handleMouseMove);
      window.removeEventListener('mouseup', handleMouseUp);
      canvas.removeEventListener('wheel', handleWheel);
    };
  }, []); // registered once at mount

  const [exportStatus, setExportStatus] = useState<string>('');

  const handleExport = useCallback(async () => {
    setExportStatus('');
    let dirHandle: FileSystemDirectoryHandle | null = null;

    // Try modern DirectoryPicker API
    if ('showDirectoryPicker' in window) {
      try {
        dirHandle = await (window as unknown as { showDirectoryPicker: () => Promise<FileSystemDirectoryHandle> }).showDirectoryPicker();
      } catch {
        // User cancelled
        return;
      }
    } else {
      // Fallback: hidden file input with webkitdirectory
      return new Promise<void>((resolve) => {
        const input = document.createElement('input');
        input.type = 'file';
        input.webkitdirectory = true;
        input.style.display = 'none';
        document.body.appendChild(input);
        input.click();
        input.addEventListener('change', async () => {
          document.body.removeChild(input);
          if (input.files && input.files.length > 0) {
            // webkitdirectory gives us a path — use the first file's path as the dir
            const dir = (input.files[0] as File & { path?: string }).path;
            if (dir) {
              try {
                const result = await bridge.exportArtboards(dir) as { success?: boolean; error?: string; exported?: string[] };
                setExportStatus(result.success ? `Exported: ${(result.exported || []).join(', ')}` : `Error: ${result.error}`);
              } catch {
                setExportStatus('Export failed');
              }
            }
          }
          resolve();
        });
      });
    }

    if (dirHandle) {
      // For DirectoryPicker, we get a handle — send the name/key to backend via persisted access
      // Since we can't get a raw path from DirectoryPicker, use the last-folder name as a hint
      // and store the handle for subsequent writes. For simplicity, use a known path approach.
      // Prompt for path string as fallback
      const dirPath = prompt('Enter the full path to export to (e.g. /Users/you/Desktop/export):');
      if (!dirPath) return;
      try {
        const result = await bridge.exportArtboards(dirPath) as { success?: boolean; error?: string; exported?: string[] };
        setExportStatus(result.success ? `Exported: ${(result.exported || []).join(', ')}` : `Error: ${result.error}`);
      } catch {
        setExportStatus('Export failed');
      }
    }
  }, []);

  const handleCanvasClick = useCallback(
    (e: React.MouseEvent) => {
      if (e.target === canvasRef.current) {
        // handled in mousedown
      }
    },
    []
  );

  const cursorStyle =
    spaceDown || isPanning
      ? 'grab'
      : activeTool === 'pan'
      ? 'grab'
      : activeTool === 'select'
      ? 'default'
      : 'crosshair';

  return (
    <div
      id="paper-canvas"
      ref={canvasRef}
      style={{
        width: '100%',
        height: '100%',
        overflow: 'hidden',
        background: '#2a2a2a',
        cursor: cursorStyle,
        backgroundImage: `linear-gradient(rgba(255,255,255,0.03) 1px, transparent 1px), linear-gradient(90deg, rgba(255,255,255,0.03) 1px, transparent 1px)`,
        backgroundSize: `${20 * transform.scale}px ${20 * transform.scale}px`,
        backgroundPosition: `${transform.translateX}px ${transform.translateY}px`,
        position: 'relative',
      }}
      onClick={handleCanvasClick}
    >
      {/* No artboards yet */}
      {(!doc || doc.pages.length === 0) && (
        <div style={{
          position: 'absolute',
          inset: 0,
          display: 'flex',
          flexDirection: 'column',
          alignItems: 'center',
          justifyContent: 'center',
          gap: 8,
          color: '#555',
          fontSize: 14,
          fontFamily: 'system-ui, sans-serif',
          pointerEvents: 'none',
        }}>
          <div style={{ fontSize: 32 }}>🎨</div>
          <div>No artboards yet</div>
          <div style={{ fontSize: 12, color: '#444' }}>
            Add one from the left panel
          </div>
        </div>
      )}

      {/* Canvas transform layer */}
      <div
        style={{
          position: 'absolute',
          transform: `translate(${transform.translateX}px, ${transform.translateY}px) scale(${transform.scale})`,
          transformOrigin: '0 0',
          left: 0,
          top: 0,
          right: 0,
          bottom: 0,
        }}
      >
        {/* All artboards */}
        {doc && doc.pages.map((page) => (
          <ArtboardFrame
            key={page.id}
            page={page}
            elementsMap={elementsMap}
          />
        ))}
      </div>

      {/* Drawing preview */}
      {preview && (
        <div
          style={{
            position: 'absolute',
            left: transform.translateX + preview.x * transform.scale,
            top: transform.translateY + preview.y * transform.scale,
            width: preview.w * transform.scale,
            height: preview.h * transform.scale,
            border: '1px solid #0066ff',
            backgroundColor: 'rgba(0,102,255,0.05)',
            pointerEvents: 'none',
            zIndex: 9999,
          }}
        />
      )}

      {/* Zoom + Export controls */}
      <div
        style={{
          position: 'absolute',
          bottom: 16,
          right: 16,
          display: 'flex',
          alignItems: 'center',
          gap: 6,
          zIndex: 10,
        }}
      >
        {/* Export button */}
        <button
          onClick={handleExport}
          title="Export all artboards as HTML"
          style={{
            padding: '4px 10px',
            background: '#0066ff',
            color: '#fff',
            border: 'none',
            borderRadius: 4,
            fontSize: 12,
            cursor: 'pointer',
            fontWeight: 500,
          }}
        >
          Export
        </button>

        {/* Zoom indicator */}
        <div
          style={{
            padding: '4px 8px',
            background: 'rgba(0,0,0,0.6)',
            color: '#fff',
            fontSize: 12,
            borderRadius: 4,
            pointerEvents: 'none',
          }}
        >
          {Math.round(transform.scale * 100)}%
        </div>
      </div>

      {/* Export status toast */}
      {exportStatus && (
        <div
          style={{
            position: 'absolute',
            bottom: 50,
            right: 16,
            padding: '6px 12px',
            background: 'rgba(0,0,0,0.8)',
            color: '#fff',
            fontSize: 12,
            borderRadius: 4,
            zIndex: 20,
          }}
        >
          {exportStatus}
        </div>
      )}
    </div>
  );
}
