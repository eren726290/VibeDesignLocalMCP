/**
 * Bridge API - Communication with Python backend
 */

const API_BASE = 'http://localhost:3004';

// Current active document ID — stored in localStorage so different tabs
// can work on different documents. AI uses the same ID via header.
function getActiveDocId(): string {
  return localStorage.getItem('paper-active-doc') || 'default';
}

function resolveDocId(docId?: string): string {
  return docId || getActiveDocId();
}

export function setActiveDocId(id: string) {
  localStorage.setItem('paper-active-doc', id);
}

export function getCurrentDocId() {
  return getActiveDocId();
}

export function switchDocument(id: string) {
  setActiveDocId(id);
}

async function api<T>(endpoint: string, options: RequestInit = {}, docId?: string): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'x-paper-doc-id': resolveDocId(docId),
      ...options.headers,
    },
  });

  if (!response.ok) {
    throw new Error(`API Error: ${response.status}`);
  }

  return response.json();
}

// =============================================================================
// Document API
// =============================================================================

export async function newDocument() {
  return api('/api/documents/new', { method: 'POST' });
}

export async function getDocument(docId?: string) {
  // Read from in-memory state (server is source of truth)
  const id = resolveDocId(docId);
  return api(`/api/documents/${id}`, {}, id);
}

export async function saveDocument(docId: string, filePath?: string) {
  const id = resolveDocId(docId);
  return api(`/api/documents/${id}/save`, {
    method: 'POST',
    body: JSON.stringify({ filePath }),
  }, id);
}

export async function openDocument(docId: string, filePath: string) {
  const id = resolveDocId(docId);
  return api(`/api/documents/${id}/open`, {
    method: 'POST',
    body: JSON.stringify({ file_path: filePath }),
  }, id);
}

export async function createElement(docId: string, element: Record<string, unknown>, pageId?: string) {
  const id = resolveDocId(docId);
  return api(`/api/documents/${id}/elements`, {
    method: 'POST',
    body: JSON.stringify(pageId ? { element, pageId } : element),
  }, id);
}

export async function createPage(docId: string, page: Record<string, unknown>) {
  const id = resolveDocId(docId);
  return api(`/api/documents/${id}/pages`, {
    method: 'POST',
    body: JSON.stringify(page),
  }, id);
}

export async function updateElement(docId: string, elementId: string, updates: Record<string, unknown>) {
  const id = resolveDocId(docId);
  return api(`/api/documents/${id}/elements/${elementId}`, {
    method: 'PUT',
    body: JSON.stringify(updates),
  }, id);
}

export async function updatePage(docId: string, pageId: string, updates: Record<string, unknown>) {
  const id = resolveDocId(docId);
  return api(`/api/documents/${id}/pages/${pageId}`, {
    method: 'PUT',
    body: JSON.stringify(updates),
  }, id);
}

export async function deleteElement(docId: string, elementId: string) {
  const id = resolveDocId(docId);
  return api(`/api/documents/${id}/elements/${elementId}`, {
    method: 'DELETE',
  }, id);
}

export async function deletePage(docId: string, pageId: string) {
  const id = resolveDocId(docId);
  return api(`/api/documents/${id}/pages/${pageId}`, {
    method: 'DELETE',
  }, id);
}

export async function duplicateElement(docId: string, elementId: string) {
  const id = resolveDocId(docId);
  return api(`/api/documents/${id}/duplicate`, {
    method: 'POST',
    body: JSON.stringify({ elementId }),
  }, id);
}

export async function exportHtml(docId: string, pretty: boolean = true) {
  const id = resolveDocId(docId);
  return api(`/api/documents/${id}/export`, {
    method: 'POST',
    body: JSON.stringify({ pretty }),
  }, id);
}

/** Export all artboards as individual HTML files to a chosen directory */
export async function exportArtboards(directory: string) {
  return api(`/api/documents/${getActiveDocId()}/export-artboards`, {
    method: 'POST',
    body: JSON.stringify({ directory }),
  });
}

export async function setScreenshotData(docId: string, data: string) {
  const id = resolveDocId(docId);
  return api(`/api/documents/${id}/screenshot`, {
    method: 'POST',
    body: JSON.stringify({ data }),
  }, id);
}

export async function setCurrentPage(docId: string, index: number) {
  const id = resolveDocId(docId);
  return api(`/api/documents/${id}/current-page`, {
    method: 'PATCH',
    body: JSON.stringify({ current_page: index }),
  }, id);
}

// =============================================================================
// Window Bridge (for pywebview)
// =============================================================================

declare global {
  interface Window {
    paperBridge?: {
      newDocument: () => Promise<unknown>;
      getDocument: (docId: string) => Promise<unknown>;
      saveDocument: (docId: string, filePath?: string) => Promise<unknown>;
      openDocument: (docId: string, filePath: string) => Promise<unknown>;
      createElement: (docId: string, element: Record<string, unknown>, pageId?: string) => Promise<unknown>;
      createPage: (docId: string, page: Record<string, unknown>) => Promise<unknown>;
      updateElement: (docId: string, elementId: string, updates: Record<string, unknown>) => Promise<unknown>;
      deleteElement: (docId: string, elementId: string) => Promise<unknown>;
      duplicateElement: (docId: string, elementId: string) => Promise<unknown>;
      exportHtml: (docId: string, pretty?: boolean) => Promise<unknown>;
      exportArtboards: (directory: string) => Promise<unknown>;
      setScreenshotData: (docId: string, data: string) => Promise<unknown>;
      setCurrentPage: (docId: string, index: number) => Promise<unknown>;
      getCurrentDocId: () => string;
      setActiveDocId: (id: string) => void;
      switchDocument: (id: string) => void;
    };
  }
}
// Export API for use in components
export const bridge = {
  newDocument,
  getDocument,
  saveDocument,
  openDocument,
  createElement,
  createPage,
  updateElement,
  updatePage,
  deleteElement,
  deletePage,
  duplicateElement,
  exportHtml,
  exportArtboards,
  setScreenshotData,
  setCurrentPage,
  getCurrentDocId,
  setActiveDocId,
  switchDocument,
};
