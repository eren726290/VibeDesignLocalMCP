export type ElementType = 'page' | 'frame' | 'rectangle' | 'text' | 'group';

export interface Element {
  id: string;
  name: string;
  tag: string;
  type: ElementType;
  style: Record<string, string>;
  text?: string;
  children?: string[]; // child element IDs
  parentId?: string | null;
  visible?: boolean;
  locked?: boolean;
}

export interface Page {
  id: string;
  name: string;
  x: number;
  y: number;
  width: number;
  height: number;
  backgroundColor?: string;
  elements: Element[];
}

export interface Document {
  id: string;
  title: string;
  pages: Page[];
  current_page: number;
  file_path?: string;
}

export type Tool = 'select' | 'pan' | 'frame' | 'rectangle' | 'text';

export interface Selection {
  nodeId: string;
  x: number;
  y: number;
  width: number;
  height: number;
}

export interface Transform {
  scale: number;
  translateX: number;
  translateY: number;
}
