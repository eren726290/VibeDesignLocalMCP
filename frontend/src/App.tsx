import { useEffect, useRef, useState, useCallback } from 'react';
import { useEditorStore } from './store/editorStore';
import { Canvas } from './canvas/Canvas';
import { Toolbar } from './toolbar/Toolbar';
import { LayerPanel } from './panels/LayerPanel';
import { PropertyPanel } from './panels/PropertyPanel';
import { bridge } from './bridge/api';
import { syncManager } from './store/syncManager';
import { computeStartupFocusTransform } from './canvas/viewport';
import type { Document } from './types';

// ─── Global Sync Manager (server-first, pausable polling) ────────────────────

interface ContextMenuState {
  visible: boolean;
  x: number;
  y: number;
}

export function App() {
  const { setDocument, setTransform, transform, spaceDown, setSpaceDown } = useEditorStore();
  const docIdRef = useRef('default');
  const syncIntervalRef = useRef<number | null>(null);
  const hasFocusedStartupRef = useRef(false);
  const [contextMenu, setContextMenu] = useState<ContextMenuState>({ visible: false, x: 0, y: 0 });
  const [isPanning, setIsPanning] = useState(false);
  const [panStart, setPanStart] = useState({ x: 0, y: 0 });

  // Initialize document — query existing doc first, don't auto-create
  useEffect(() => {
    const init = async () => {
      try {
        const doc = await bridge.getDocument(docIdRef.current);
        setDocument(doc as Document);
        const startupTransform = computeStartupFocusTransform(doc as Document);
        if (startupTransform && !hasFocusedStartupRef.current) {
          setTransform(startupTransform);
          hasFocusedStartupRef.current = true;
        }
        if ((doc as Document).id) {
          docIdRef.current = (doc as Document).id;
          bridge.setActiveDocId((doc as Document).id);
        }
      } catch (e) {
        // Backend unreachable — show empty state, user can click + to create
        setDocument({
          id: 'default',
          title: 'Untitled',
          pages: [],
          current_page: 0,
        });
        docIdRef.current = 'default';
        bridge.setActiveDocId('default');
      }
    };
    init();
  }, [setDocument]);

  // ─── Sync with backend (polls for AI/MCP changes) ─────────────────────────────
  useEffect(() => {
    let lastSync = 0;
    const sync = async () => {
      // Throttle
      const now = Date.now();
      if (now - lastSync < 800) return;
      lastSync = now;

      // Skip if a local PUT is in-flight (pause polling to avoid overwriting)
      if (syncManager.pauseRef.count > 0) return;

      try {
        const doc = await bridge.getDocument(docIdRef.current);
        if (!doc) return;
        // Server is source of truth — always overwrite local state
        useEditorStore.getState().setDocument(doc as Document);
      } catch (e) {
        // silently ignore sync errors
      }
    };
    syncIntervalRef.current = window.setInterval(sync, 1000);
    return () => {
      if (syncIntervalRef.current) {
        clearInterval(syncIntervalRef.current);
      }
    };
  }, []);

  // ─── Keyboard shortcuts (document-level) ─────────────────────────────────────
  useEffect(() => {
    const handleKeyDown = (e: KeyboardEvent) => {
      const state = useEditorStore.getState();
      const target = e.target as HTMLElement;
      const isTyping = target.closest('input') || target.closest('textarea') || target.isContentEditable;

      // Space → toggle pan mode
      if (e.code === 'Space' && !e.repeat && !isTyping) {
        e.preventDefault();
        setSpaceDown(true);
        return;
      }

      // Don't process other shortcuts while typing
      if (isTyping) return;

      // Tool shortcuts
      if (e.key === 'v' || e.key === 'V') state.setActiveTool('select');
      else if (e.key === 'h' || e.key === 'H') state.setActiveTool('pan');
      // R, T, F shortcuts removed — tools disabled in Task 24

      // Delete / Backspace → delete selected element
      if (e.key === 'Delete' || e.key === 'Backspace') {
        const sel = state.selection;
        if (sel) state.deleteElement(sel.nodeId);
      }

      // Cmd+C → copy
      if ((e.metaKey || e.ctrlKey) && e.key === 'c') {
        const sel = state.selection;
        if (sel) state.copyElement(sel.nodeId);
      }

      // Cmd+V → paste at cursor (use last mouse pos or center)
      if ((e.metaKey || e.ctrlKey) && e.key === 'v') {
        if (state.copiedElement) {
          // Paste near center of viewport
          state.pasteElement(200, 200);
        }
      }

      // Cmd+D → duplicate
      if ((e.metaKey || e.ctrlKey) && e.key === 'd') {
        e.preventDefault();
        const sel = state.selection;
        if (sel) state.duplicateElement(sel.nodeId);
      }

      // Escape → deselect
      if (e.key === 'Escape') {
        state.setSelection(null);
        setContextMenu({ visible: false, x: 0, y: 0 });
      }

      // Zoom: Cmd+Plus / Cmd+Minus
      if ((e.metaKey || e.ctrlKey) && (e.key === '=' || e.key === '+')) {
        e.preventDefault();
        const newScale = Math.min(transform.scale * 1.2, 10);
        setTransform({ scale: newScale });
      }
      if ((e.metaKey || e.ctrlKey) && e.key === '-') {
        e.preventDefault();
        const newScale = Math.max(transform.scale / 1.2, 0.1);
        setTransform({ scale: newScale });
      }
    };

    const handleKeyUp = (e: KeyboardEvent) => {
      if (e.code === 'Space') {
        setSpaceDown(false);
        setIsPanning(false);
      }
    };

    window.addEventListener('keydown', handleKeyDown);
    window.addEventListener('keyup', handleKeyUp);
    return () => {
      window.removeEventListener('keydown', handleKeyDown);
      window.removeEventListener('keyup', handleKeyUp);
    };
  }, [transform.scale, setTransform, setSpaceDown]);

  // ─── Space pan mouse tracking ────────────────────────────────────────────────
  const handleAppMouseDown = useCallback((e: React.MouseEvent) => {
    if (spaceDown) {
      setIsPanning(true);
      setPanStart({ x: e.clientX - transform.translateX, y: e.clientY - transform.translateY });
    }
  }, [spaceDown, transform.translateX, transform.translateY]);

  const handleAppMouseMove = useCallback((e: React.MouseEvent) => {
    if (isPanning) {
      setTransform({
        translateX: e.clientX - panStart.x,
        translateY: e.clientY - panStart.y,
      });
    }
  }, [isPanning, panStart, setTransform]);

  const handleAppMouseUp = useCallback(() => setIsPanning(false), []);

  // Context menu — disabled
  // useEffect(() => {
  //   const handleContextMenu = (e: MouseEvent) => {
  //     e.preventDefault();
  //     setContextMenu({ visible: true, x: e.clientX, y: e.clientY });
  //   };
  //   const handleClick = () => setContextMenu({ visible: false, x: 0, y: 0 });
  //   window.addEventListener('contextmenu', handleContextMenu, true);
  //   window.addEventListener('click', handleClick);
  //   return () => {
  //     window.removeEventListener('contextmenu', handleContextMenu, true);
  //     window.removeEventListener('click', handleClick);
  //   };
  // }, []);

  const handleContextMenuAction = useCallback((action: string) => {
    const state = useEditorStore.getState();
    const sel = state.selection;

    switch (action) {
      case 'duplicate':
        if (sel) state.duplicateElement(sel.nodeId);
        break;
      case 'delete':
        if (sel) state.deleteElement(sel.nodeId);
        break;
      case 'select-parent':
        // TODO: implement
        break;
    }
    setContextMenu({ visible: false, x: 0, y: 0 });
  }, []);

  return (
    <div
      style={{
        display: 'flex',
        width: '100%',
        height: '100%',
        position: 'absolute',
        inset: 0,
        background: '#1a1a1a',
        cursor: spaceDown || isPanning ? 'grab' : 'default',
      }}
      onMouseDown={handleAppMouseDown}
      onMouseMove={handleAppMouseMove}
      onMouseUp={handleAppMouseUp}
      onMouseLeave={handleAppMouseUp}
    >
      {/* 4-column layout */}
      <LayerPanel />

      <Toolbar />

      <div style={{ flex: 1, minWidth: 0, minHeight: 0, position: 'relative' }}>
        <Canvas />
      </div>

      <PropertyPanel />

      {/* Context Menu */}
      {contextMenu.visible && (
        <div
          style={{
            position: 'fixed',
            left: contextMenu.x,
            top: contextMenu.y,
            background: '#2a2a2a',
            border: '1px solid #444',
            borderRadius: 8,
            padding: 4,
            minWidth: 200,
            boxShadow: '0 8px 24px rgba(0,0,0,0.5)',
            zIndex: 9999,
          }}
          onClick={(e) => e.stopPropagation()}
        >
          {[
            { label: 'Copy', shortcut: '⌘C', action: 'copy' },
            { label: 'Copy link', action: 'copy-link' },
            { divider: true },
            { label: 'Copy as', children: ['Copy as PNG', 'Copy as Tailwind', 'Copy as React CSS'] },
            { divider: true },
            { label: 'Paste', shortcut: '⌘V', action: 'paste' },
            { label: 'Paste on top', shortcut: '⇧⌘V', action: 'paste-top' },
            { label: 'Paste to replace', shortcut: '⇧⌘R', action: 'paste-replace' },
            { divider: true },
            { label: 'Duplicate', shortcut: '⌘D', action: 'duplicate' },
            { label: 'Copy styles', shortcut: '⌥⌘C', action: 'copy-styles' },
            { label: 'Paste styles', shortcut: '⌥⌘V', action: 'paste-styles' },
            { divider: true },
            { label: 'Frame selection', shortcut: '⇧F', action: 'frame-selection' },
            { label: 'Add flex layout', shortcut: '⇧A', action: 'add-flex' },
            { label: 'Ungroup', shortcut: '⇧⌘G', action: 'ungroup' },
            { divider: true },
            { label: 'Show / hide', shortcut: '⇧⌘H', action: 'show-hide' },
            { label: 'Lock / unlock', shortcut: '⇧⌘L', action: 'lock' },
            { divider: true },
            { label: 'Arrange', children: ['Bring to front', 'Send to back', 'Bring forward', 'Send backward'] },
            { divider: true },
            { label: 'Select parent', shortcut: 'Escape', action: 'select-parent' },
            { label: 'Select children', shortcut: 'Enter', action: 'select-children' },
          ].map((item, i) => {
            if ('divider' in item && item.divider) {
              return <div key={i} style={{ height: 1, background: '#444', margin: '4px 0' }} />;
            }
            return (
              <div
                key={i}
                onClick={() => item.action && handleContextMenuAction(item.action)}
                style={{
                  padding: '6px 12px',
                  color: '#fff',
                  fontSize: 12,
                  cursor: 'pointer',
                  display: 'flex',
                  justifyContent: 'space-between',
                  borderRadius: 4,
                  gap: 16,
                }}
                onMouseEnter={(e) => (e.currentTarget.style.background = '#444')}
                onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
              >
                <span>{item.label}</span>
                {'shortcut' in item && item.shortcut && (
                  <span style={{ color: '#888' }}>{item.shortcut}</span>
                )}
              </div>
            );
          })}
        </div>
      )}
    </div>
  );
}
