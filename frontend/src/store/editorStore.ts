import { create } from 'zustand';
import type { Document, Element, Page, Tool, Selection, Transform } from '../types';
import { bridge } from '../bridge/api';
import { syncManager } from './syncManager';

interface EditorState {
  document: Document | null;
  docId: string;
  activeTool: Tool;
  setActiveTool: (tool: Tool) => void;
  spaceDown: boolean;
  setSpaceDown: (v: boolean) => void;
  selection: Selection | null;
  setSelection: (sel: Selection | null) => void;
  selectedArtboardId: string | null;
  selectArtboard: (id: string | null) => void;
  updateArtboard: (id: string, updates: Partial<Page>) => void;
  transform: Transform;
  setTransform: (t: Partial<Transform>) => void;
  expandedNodes: Set<string>;
  toggleExpanded: (nodeId: string) => void;
  expandToNode: (nodeId: string) => void; // expand all ancestors so the node is visible in the layer tree
  history: Document[];
  historyIndex: number;
  pushHistory: () => void;
  setDocument: (doc: Document) => void;
  addElement: (element: Element) => void;
  updateElement: (id: string, updates: Partial<Element>) => void;
  deleteElement: (id: string) => void;
  duplicateElement: (id: string) => void;
  addChild: (parentId: string, childId: string) => void;
  removeChild: (parentId: string, childId: string) => void;
  addPage: (page: Page) => void;
  deletePage: (pageId: string) => void;
  setCurrentPage: (index: number) => void;
  copyElement: (id: string) => void;
  pasteElement: (x: number, y: number) => void;
  reparentElement: (id: string, x: number, y: number) => void;
  copiedElement: Element | null;
}

export const useEditorStore = create<EditorState>((set, get) => ({
  document: null,
  docId: 'default',
  activeTool: 'select',
  spaceDown: false,
  copiedElement: null,
  selection: null,
  transform: { scale: 1, translateX: 0, translateY: 0 },
  history: [],
  historyIndex: -1,
  expandedNodes: new Set<string>(),
  selectedArtboardId: null,

  setActiveTool: (tool) => set({ activeTool: tool }),

  setSpaceDown: (v) => set({ spaceDown: v }),

  setSelection: (sel) => set({ selection: sel }),

  selectArtboard: (id) => set({ selectedArtboardId: id }),

  updateArtboard: (id, updates) => {
    const { document } = get();
    if (!document) return;
    const pages = document.pages.map(p => p.id === id ? { ...p, ...updates } : p);
    syncManager.pauseSync();
    set({ document: { ...document, pages } });
    bridge.updatePage(document.id, id, updates as Record<string, unknown>)
      .catch(() => {})
      .finally(() => syncManager.resumeSync());
  },

  setTransform: (t) => set((state) => ({
    transform: { ...state.transform, ...t }
  })),

  toggleExpanded: (nodeId) => set((state) => {
    const next = new Set(state.expandedNodes);
    if (next.has(nodeId)) {
      next.delete(nodeId);
    } else {
      next.add(nodeId);
    }
    return { expandedNodes: next };
  }),

  expandToNode: (nodeId) => {
    const { document, selectedArtboardId } = get();
    if (!document) return;
    const currentPage = document.pages.find((p) => p.id === selectedArtboardId)
      ?? document.pages[document.current_page];
    if (!currentPage) return;
    const elementMap = new Map(currentPage.elements.map((el) => [el.id, el]));
    const toExpand: string[] = [];
    let curId: string | undefined = nodeId;
    while (curId) {
      const parentId = elementMap.get(curId)?.parentId;
      if (parentId) toExpand.push(parentId);
      curId = parentId;
    }
    if (toExpand.length === 0) return;
    set((state) => {
      const next = new Set(state.expandedNodes);
      toExpand.forEach((id) => next.add(id));
      return { expandedNodes: next };
    });
  },

  pushHistory: () => {
    const { document, history, historyIndex } = get();
    if (!document) return;
    const newHistory = history.slice(0, historyIndex + 1);
    newHistory.push(JSON.parse(JSON.stringify(document)));
    set({ history: newHistory.slice(-50), historyIndex: newHistory.length - 1 });
  },

  setDocument: (doc) => {
    set({ document: doc });
    get().pushHistory();
  },

  addElement: (element) => {
    const { document } = get();
    if (!document) return;
    const updated = {
      ...document,
      pages: document.pages.map((page, i) =>
        i === document.current_page
          ? { ...page, elements: [...page.elements, element] }
          : page
      ),
    };
    syncManager.pauseSync();
    set({ document: updated });
    bridge.createElement(document.id, element as unknown as Record<string, unknown>)
      .catch(() => {})
      .finally(() => syncManager.resumeSync());
    get().pushHistory();
  },

  updateElement: (id, updates) => {
    const { document } = get();
    if (!document) return;
    const updated = {
      ...document,
      pages: document.pages.map((page, i) =>
        i === document.current_page
          ? { ...page, elements: page.elements.map((el) => el.id === id ? { ...el, ...updates } : el) }
          : page
      ),
    };
    syncManager.pauseSync();
    set({ document: updated });
    bridge.updateElement(document.id, id, updates as Record<string, unknown>)
      .catch(() => {})
      .finally(() => syncManager.resumeSync());
  },

  deleteElement: (id) => {
    const { document } = get();
    if (!document) return;
    const updated = {
      ...document,
      pages: document.pages.map((page, i) =>
        i === document.current_page
          ? { ...page, elements: page.elements.filter((el) => el.id !== id) }
          : page
      ),
    };
    syncManager.pauseSync();
    set({ document: updated });
    bridge.deleteElement(document.id, id)
      .catch(() => {})
      .finally(() => syncManager.resumeSync());
    set({ selection: null });
    get().pushHistory();
  },

  duplicateElement: (id) => {
    const { document } = get();
    if (!document) return;
    const page = document.pages[document.current_page];
    const element = page.elements.find((el) => el.id === id);
    if (!element) return;
    const newElement: Element = {
      ...JSON.parse(JSON.stringify(element)),
      id: `n-${Date.now().toString(36)}`,
    };
    if (newElement.style?.left) {
      newElement.style.left = `${parseFloat(newElement.style.left) + 20}px`;
    }
    if (newElement.style?.top) {
      newElement.style.top = `${parseFloat(newElement.style.top) + 20}px`;
    }
    const updated = {
      ...document,
      pages: document.pages.map((page, i) =>
        i === document.current_page
          ? { ...page, elements: [...page.elements, newElement] }
          : page
      ),
    };
    syncManager.pauseSync();
    set({ document: updated });
    bridge.duplicateElement(document.id, id)
      .catch(() => {})
      .finally(() => syncManager.resumeSync());
    get().pushHistory();
  },

  addChild: (parentId, childId) => {
    const { document } = get();
    if (!document) return;
    const page = document.pages[document.current_page];
    const parent = page.elements.find((el) => el.id === parentId);
    const child = page.elements.find((el) => el.id === childId);
    if (!parent || !child) return;

    // Nested Frame (inside another Frame) → flow (relative, no left/top)
    // Root Frame or Rectangle parent → absolute, coords relative to parent
    const isNestedFrame = parent.type === 'frame' && parent.parentId != null;
    const { left, top, position, ...restStyle } = child.style as Record<string, string>;
    const newStyle: Record<string, string> = isNestedFrame
      ? { ...restStyle, position: 'relative' }
      : { ...restStyle, position: 'absolute', left: left || '0px', top: top || '0px' };

    const updated = {
      ...document,
      pages: document.pages.map((page, i) =>
        i === document.current_page
          ? {
              ...page,
              elements: page.elements.map((el) =>
                el.id === parentId
                  ? { ...el, children: [...(el.children || []), childId] }
                  : el.id === childId
                  ? { ...el, parentId, style: newStyle }
                  : el
              ),
            }
          : page
      ),
    };
    set({ document: updated });
  },

  removeChild: (parentId, childId) => {
    const { document } = get();
    if (!document) return;
    const updated = {
      ...document,
      pages: document.pages.map((page, i) =>
        i === document.current_page
          ? {
              ...page,
              elements: page.elements.map((el) =>
                el.id === parentId
                  ? { ...el, children: (el.children || []).filter((c) => c !== childId) }
                  : el
              ),
            }
          : page
      ),
    };
    set({ document: updated });
  },

  addPage: (page: Page) => {
    const { document } = get();
    if (!document) return;
    const updated = {
      ...document,
      pages: [...document.pages, page],
    };
    syncManager.pauseSync();
    set({ document: updated });
    bridge.createPage(document.id, page as unknown as Record<string, unknown>)
      .catch(() => {})
      .finally(() => syncManager.resumeSync());
  },

  deletePage: (pageId: string) => {
    const { document } = get();
    if (!document) return;
    if (document.pages.length <= 1) return; // keep at least one
    const idx = document.pages.findIndex(p => p.id === pageId);
    if (idx === -1) return;
    const pages = document.pages.filter(p => p.id !== pageId);
    let current_page = document.current_page;
    if (idx <= current_page) current_page = Math.max(0, current_page - 1);
    syncManager.pauseSync();
    set({ document: { ...document, pages, current_page }, selection: null, selectedArtboardId: null });
    bridge.deletePage(document.id, pageId)
      .catch(() => {})
      .finally(() => syncManager.resumeSync());
  },

  setCurrentPage: (index) => {
    const { document } = get();
    if (!document) return;
    set({ document: { ...document, current_page: index }, selection: null });
    bridge.setCurrentPage(document.id, index).catch(() => {});
  },

  copyElement: (id) => {
    const { document } = get();
    if (!document) return;
    const page = document.pages[document.current_page];
    const el = page.elements.find((e) => e.id === id);
    if (el) set({ copiedElement: JSON.parse(JSON.stringify(el)) });
  },

  pasteElement: (x, y) => {
    const { document, copiedElement } = get();
    if (!document || !copiedElement) return;
    const newElement: Element = {
      ...JSON.parse(JSON.stringify(copiedElement)),
      id: `n-${Date.now().toString(36)}`,
      style: {
        ...JSON.parse(JSON.stringify(copiedElement.style)),
        left: `${x}px`,
        top: `${y}px`,
      },
    };
    const { addElement } = get();
    addElement(newElement);
    set({
      selection: {
        nodeId: newElement.id,
        x,
        y,
        width: parseFloat(newElement.style.width || '100'),
        height: parseFloat(newElement.style.height || '100'),
      },
    });
  },

  reparentElement: (id: string, cx: number, cy: number) => {
    const { document } = get();
    if (!document) return;
    const page = document.pages[document.current_page];
    const element = page.elements.find((el) => el.id === id);
    if (!element) return;

    const oldParentId = element.parentId || null;

    // Find frame at drop position
    const frames = page.elements.filter((el) => el.type === 'frame');
    let targetFrame: Element | null = null;
    for (const frame of frames) {
      const left = parseFloat(frame.style.left || '0');
      const top = parseFloat(frame.style.top || '0');
      const w = parseFloat(frame.style.width || '0');
      const h = parseFloat(frame.style.height || '0');
      if (cx >= left && cx <= left + w && cy >= top && cy <= top + h) {
        const area = w * h;
        if (!targetFrame || area < parseFloat(targetFrame.style.width || '0') * parseFloat(targetFrame.style.height || '0')) {
          targetFrame = frame;
        }
      }
    }

    // If dropping in the same parent, update position but keep parent
    if (targetFrame && targetFrame.id === oldParentId) {
      const parent = targetFrame;
      const parentX = parseFloat(parent.style.left || '0');
      const parentY = parseFloat(parent.style.top || '0');
      set({
        document: {
          ...document,
          pages: document.pages.map((p, i) =>
            i === document.current_page
              ? { ...p, elements: p.elements.map((el) => el.id === id ? { ...el, style: { ...el.style, left: `${cx - parentX}px`, top: `${cy - parentY}px` } } : el) }
              : p
          ),
        },
      });
      get().pushHistory();
      return;
    }

    let updated: Document;

    if (targetFrame) {
      // ── Dropped inside a frame ──
      const isNestedFrame = targetFrame.type === 'frame' && targetFrame.parentId != null;
      const parentX = parseFloat(targetFrame.style.left || '0');
      const parentY = parseFloat(targetFrame.style.top || '0');
      const parentRelX = cx - parentX;
      const parentRelY = cy - parentY;

      const { left, top, position, ...restStyle } = element.style as Record<string, string>;
      const newStyle: Record<string, string> = isNestedFrame
        ? { ...restStyle, position: 'relative', left: `${parentRelX}px`, top: `${parentRelY}px` }
        : { ...restStyle, position: 'absolute', left: `${parentRelX}px`, top: `${parentRelY}px` };

      updated = {
        ...document,
        pages: document.pages.map((p, i) =>
          i === document.current_page
            ? {
                ...p,
                elements: p.elements.map((el) => {
                  if (el.id === oldParentId && oldParentId !== targetFrame!.id) {
                    return { ...el, children: (el.children || []).filter((c) => c !== id) };
                  }
                  if (el.id === targetFrame!.id) {
                    return { ...el, children: [...(el.children || []), id] };
                  }
                  if (el.id === id) {
                    return { ...el, parentId: targetFrame!.id, style: newStyle };
                  }
                  return el;
                }),
              }
            : p
        ),
      };
    } else {
      // ── Dropped outside any frame → become root ──
      updated = {
        ...document,
        pages: document.pages.map((p, i) =>
          i === document.current_page
            ? {
                ...p,
                elements: p.elements.map((el) => {
                  if (el.id === oldParentId) {
                    return { ...el, children: (el.children || []).filter((c) => c !== id) };
                  }
                  if (el.id === id) {
                    return { ...el, parentId: null, style: { ...el.style, position: 'absolute', left: `${cx}px`, top: `${cy}px` } };
                  }
                  return el;
                }),
              }
            : p
        ),
      };
    }

    set({ document: updated });
    get().pushHistory();
  },
}));
