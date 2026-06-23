import type { Document, Page, Transform } from '../types';

const TOOLBAR_WIDTH = 40;
const RIGHT_PANEL_WIDTH = 280;
const DEFAULT_PADDING = 0.1;
const MAX_SCALE = 2;

function getViewportSize() {
  return {
    width: window.innerWidth - TOOLBAR_WIDTH - RIGHT_PANEL_WIDTH,
    height: window.innerHeight,
  };
}

function computePageTransform(page: Page, viewportWidth: number, viewportHeight: number): Transform | null {
  if (page.width <= 0 || page.height <= 0) return null;

  const scaleX = viewportWidth / page.width / (1 + DEFAULT_PADDING);
  const scaleY = viewportHeight / page.height / (1 + DEFAULT_PADDING);
  const scale = Math.min(scaleX, scaleY, MAX_SCALE);

  return {
    scale,
    translateX: (viewportWidth - page.width * scale) / 2 - page.x * scale,
    translateY: (viewportHeight - page.height * scale) / 2 - page.y * scale,
  };
}

export function computeFitAllTransform(document: Document): Transform | null {
  if (document.pages.length === 0) return null;

  let minX = Infinity;
  let minY = Infinity;
  let maxX = -Infinity;
  let maxY = -Infinity;

  for (const page of document.pages) {
    if (page.x < minX) minX = page.x;
    if (page.y < minY) minY = page.y;
    if (page.x + page.width > maxX) maxX = page.x + page.width;
    if (page.y + page.height > maxY) maxY = page.y + page.height;
  }

  const boundsWidth = maxX - minX;
  const boundsHeight = maxY - minY;
  if (boundsWidth <= 0 || boundsHeight <= 0) return null;

  const { width: viewportWidth, height: viewportHeight } = getViewportSize();
  const scaleX = viewportWidth / boundsWidth / (1 + DEFAULT_PADDING);
  const scaleY = viewportHeight / boundsHeight / (1 + DEFAULT_PADDING);
  const scale = Math.min(scaleX, scaleY, MAX_SCALE);

  return {
    scale,
    translateX: (viewportWidth - boundsWidth * scale) / 2 - minX * scale,
    translateY: (viewportHeight - boundsHeight * scale) / 2 - minY * scale,
  };
}

export function computeStartupFocusTransform(document: Document): Transform | null {
  if (document.pages.length === 0) return null;

  const { width: viewportWidth, height: viewportHeight } = getViewportSize();
  const currentPage = document.pages[document.current_page];
  const pageTransform = currentPage
    ? computePageTransform(currentPage, viewportWidth, viewportHeight)
    : null;

  if (pageTransform) return pageTransform;

  return computeFitAllTransform(document);
}
