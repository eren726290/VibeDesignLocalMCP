import { useRef, useEffect, useState, useMemo, useCallback } from 'react';
import { useEditorStore } from '../store/editorStore';
import { bridge } from '../bridge/api';
import { ArtboardFrame } from './ArtboardFrame';
import type { Element as ElementType } from '../types';

// ─── Canvas ─────────────────────────────────────────────────────────────────────

export function Canvas() {
  const canvasRef = useRef<HTMLDivElement>(null);
  const [isPanning, setIsPanning] = useState(false);

  const isPanningRef = useRef(false);
  const panStartRef = useRef({ x: 0, y: 0 });

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

      // Left click with select tool → selection only, no drag/mutation
      if (e.button === 0 && activeTool === 'select') {
        const target = e.target as HTMLElement;
        if (!target.closest('[data-paper-node]')) {
          // Click on empty canvas → clear selection
          useEditorStore.getState().clearSelection();
        }
        return;
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
    };

    const handleMouseUp = () => {
      // End pan
      if (isPanningRef.current) {
        isPanningRef.current = false;
        setIsPanning(false);
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

  const cursorStyle =
    spaceDown || isPanning
      ? 'grab'
      : activeTool === 'pan'
      ? 'grab'
      : 'default';

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
