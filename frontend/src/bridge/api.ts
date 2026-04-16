/**
 * Bridge API - Communication with Python backend
 */

const API_BASE = 'http://localhost:3004';

// Current active document ID — stored in localStorage so different tabs
// can work on different documents. AI uses the same ID via header.
function getActiveDocId(): string {
  return localStorage.getItem('paper-active-doc') || 'default';
}

function setActiveDocId(id: string) {
  localStorage.setItem('paper-active-doc', id);
}

export function getCurrentDocId() {
  return getActiveDocId();
}

export function switchDocument(id: string) {
  setActiveDocId(id);
}

async function api<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
      'x-paper-doc-id': getActiveDocId(),
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

export async function getDocument(_docId?: string) {
  // Read from in-memory state (server is source of truth)
  return api(`/api/documents/${getActiveDocId()}`);
}

export async function saveDocument(_docId: string, filePath?: string) {
  return api(`/api/documents/${getActiveDocId()}/save`, {
    method: 'POST',
    body: JSON.stringify({ filePath }),
  });
}

export async function openDocument(_docId: string, filePath: string) {
  return api(`/api/documents/${getActiveDocId()}/open`, {
    method: 'POST',
    body: JSON.stringify({ file_path: filePath }),
  });
}

export async function createElement(_docId: string, element: Record<string, unknown>) {
  return api(`/api/documents/${getActiveDocId()}/elements`, {
    method: 'POST',
    body: JSON.stringify(element),
  });
}

export async function createPage(_docId: string, page: Record<string, unknown>) {
  return api(`/api/documents/${getActiveDocId()}/pages`, {
    method: 'POST',
    body: JSON.stringify(page),
  });
}

export async function updateElement(_docId: string, elementId: string, updates: Record<string, unknown>) {
  return api(`/api/documents/${getActiveDocId()}/elements/${elementId}`, {
    method: 'PUT',
    body: JSON.stringify(updates),
  });
}

export async function updatePage(_docId: string, pageId: string, updates: Record<string, unknown>) {
  return api(`/api/documents/${getActiveDocId()}/pages/${pageId}`, {
    method: 'PUT',
    body: JSON.stringify(updates),
  });
}

export async function deleteElement(_docId: string, elementId: string) {
  return api(`/api/documents/${getActiveDocId()}/elements/${elementId}`, {
    method: 'DELETE',
  });
}

export async function deletePage(_docId: string, pageId: string) {
  return api(`/api/documents/${getActiveDocId()}/pages/${pageId}`, {
    method: 'DELETE',
  });
}

export async function duplicateElement(_docId: string, elementId: string) {
  return api(`/api/documents/${getActiveDocId()}/duplicate`, {
    method: 'POST',
    body: JSON.stringify({ elementId }),
  });
}

export async function exportHtml(_docId: string, pretty: boolean = true) {
  return api(`/api/documents/${getActiveDocId()}/export`, {
    method: 'POST',
    body: JSON.stringify({ pretty }),
  });
}

export async function setScreenshotData(_docId: string, data: string) {
  return api(`/api/documents/${getActiveDocId()}/screenshot`, {
    method: 'POST',
    body: JSON.stringify({ data }),
  });
}

export async function setCurrentPage(_docId: string, index: number) {
  return api(`/api/documents/${getActiveDocId()}/current-page`, {
    method: 'PATCH',
    body: JSON.stringify({ current_page: index }),
  });
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
      createElement: (docId: string, element: Record<string, unknown>) => Promise<unknown>;
      createPage: (docId: string, page: Record<string, unknown>) => Promise<unknown>;
      updateElement: (docId: string, elementId: string, updates: Record<string, unknown>) => Promise<unknown>;
      deleteElement: (docId: string, elementId: string) => Promise<unknown>;
      duplicateElement: (docId: string, elementId: string) => Promise<unknown>;
      exportHtml: (docId: string, pretty?: boolean) => Promise<unknown>;
      setScreenshotData: (docId: string, data: string) => Promise<unknown>;
      setCurrentPage: (docId: string, index: number) => Promise<unknown>;
      getCurrentDocId: () => string;
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
  setScreenshotData,
  setCurrentPage,
  getCurrentDocId,
  switchDocument,
};
