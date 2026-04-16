/**
 * Bridge API - Communication with Python backend
 */

const API_BASE = 'http://localhost:3004';

async function api<T>(endpoint: string, options: RequestInit = {}): Promise<T> {
  const response = await fetch(`${API_BASE}${endpoint}`, {
    ...options,
    headers: {
      'Content-Type': 'application/json',
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

export async function getDocument(docId: string) {
  return api(`/api/documents/${docId}`);
}

export async function saveDocument(docId: string, filePath?: string) {
  return api(`/api/documents/${docId}/save`, {
    method: 'POST',
    body: JSON.stringify({ filePath }),
  });
}

export async function openDocument(docId: string, filePath: string) {
  return api(`/api/documents/${docId}/open`, {
    method: 'POST',
    body: JSON.stringify({ file_path: filePath }),
  });
}

export async function createElement(docId: string, element: Record<string, unknown>) {
  return api(`/api/documents/${docId}/elements`, {
    method: 'POST',
    body: JSON.stringify(element),
  });
}

export async function createPage(docId: string, page: Record<string, unknown>) {
  return api(`/api/documents/${docId}/pages`, {
    method: 'POST',
    body: JSON.stringify(page),
  });
}

export async function updateElement(docId: string, elementId: string, updates: Record<string, unknown>) {
  return api(`/api/documents/${docId}/elements/${elementId}`, {
    method: 'PUT',
    body: JSON.stringify(updates),
  });
}

export async function deleteElement(docId: string, elementId: string) {
  return api(`/api/documents/${docId}/elements/${elementId}`, {
    method: 'DELETE',
  });
}

export async function duplicateElement(docId: string, elementId: string) {
  return api(`/api/documents/${docId}/duplicate`, {
    method: 'POST',
    body: JSON.stringify({ elementId }),
  });
}

export async function exportHtml(docId: string, pretty: boolean = true) {
  return api(`/api/documents/${docId}/export`, {
    method: 'POST',
    body: JSON.stringify({ pretty }),
  });
}

export async function setScreenshotData(docId: string, data: string) {
  return api(`/api/documents/${docId}/screenshot`, {
    method: 'POST',
    body: JSON.stringify({ data }),
  });
}

export async function setCurrentPage(docId: string, index: number) {
  return api(`/api/documents/${docId}/current-page`, {
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
      newDocument: () => Promise<ReturnType<typeof newDocument>>;
      getDocument: (docId: string) => Promise<ReturnType<typeof getDocument>>;
      saveDocument: (docId: string, filePath?: string) => Promise<ReturnType<typeof saveDocument>>;
      openDocument: (docId: string, filePath: string) => Promise<ReturnType<typeof openDocument>>;
      createElement: (docId: string, element: Record<string, unknown>) => Promise<ReturnType<typeof createElement>>;
      createPage: (docId: string, page: Record<string, unknown>) => Promise<ReturnType<typeof createPage>>;
      updateElement: (docId: string, elementId: string, updates: Record<string, unknown>) => Promise<ReturnType<typeof updateElement>>;
      deleteElement: (docId: string, elementId: string) => Promise<ReturnType<typeof deleteElement>>;
      duplicateElement: (docId: string, elementId: string) => Promise<ReturnType<typeof duplicateElement>>;
      exportHtml: (docId: string, pretty?: boolean) => Promise<ReturnType<typeof exportHtml>>;
      setScreenshotData: (docId: string, data: string) => Promise<ReturnType<typeof setScreenshotData>>;
      setCurrentPage: (docId: string, index: number) => Promise<ReturnType<typeof setCurrentPage>>;
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
  deleteElement,
  duplicateElement,
  exportHtml,
  setScreenshotData,
  setCurrentPage,
};
