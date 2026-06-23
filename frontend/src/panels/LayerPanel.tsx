import { useState } from 'react';
import { useEditorStore } from '../store/editorStore';
import { bridge } from '../bridge/api';
import type { Element, Page } from '../types';

// ─── Icons ─────────────────────────────────────────────────────────────────────

function GridIcon() {
  return (
    <svg width={13} height={13} viewBox="0 0 13 13" fill="currentColor">
      <path d="M2 0V2H8V8H2V2H0V13H8V8H13V0H2Z" />
    </svg>
  );
}

function AddIcon() {
  return (
    <svg width={10} height={10} viewBox="0 0 10 10" fill="none" stroke="currentColor" strokeWidth={1.5}>
      <path d="M5 0V5M5 5V10M5 5H10M5 5H0" />
    </svg>
  );
}

function PageIcon() {
  return (
    <svg width={16} height={16} viewBox="0 0 16 16" fill="none">
      <path
        d="M12.5 5.5L9.5 2.5H4.5C3.948 2.5 3.5 2.948 3.5 3.5V12.5C3.5 13.052 3.948 13.5 4.5 13.5H11.5C12.052 13.5 12.5 13.052 12.5 12.5V5.5Z"
        fill="currentColor"
        fillOpacity={0.125}
      />
      <path
        d="M12.5 5.5L9.5 2.5M12.5 5.5V12.5C12.5 13.052 12.052 13.5 11.5 13.5H4.5C3.948 13.5 3.5 13.052 3.5 12.5V3.5C3.5 2.948 3.948 2.5 4.5 2.5H9.5M12.5 5.5H9.5V2.5"
        stroke="currentColor"
      />
    </svg>
  );
}

function FrameIcon() {
  return (
    <svg width={16} height={16} viewBox="0 0 16 16" fill="currentColor">
      <rect x={3} y={2} width={10} height={12} fillOpacity={0.125} />
      <path transform="translate(0 1)" d="M4 9L4 12H7V13H4H3V12V9H4Z" />
      <path transform="translate(0 -1)" d="M7 3H4H3V4V7H4L4 4H7V3Z" />
      <path transform="translate(0 -1)" d="M9 3H12H13V4V7H12V4H9V3Z" />
      <path transform="translate(0 1)" d="M12 9V12H9V13H12H13V12V9H12Z" />
    </svg>
  );
}

function ChevronIcon() {
  return (
    <svg width={8} height={8} viewBox="0 0 8 8" fill="none" stroke="currentColor" strokeWidth={1.5}>
      <path d="M1 2.5L4 5.5L7 2.5" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

function CheckIcon() {
  return (
    <svg width={10} height={10} viewBox="0 0 10 10" fill="none" stroke="currentColor" strokeWidth={1.5}>
      <path d="M1.75 5.75L4.51562 8.25L8.75 1.75" strokeLinecap="round" strokeLinejoin="round" />
    </svg>
  );
}

// ─── Type inference ─────────────────────────────────────────────────────────────

function inferType(element: Element): Element['type'] {
  const style = element.style || {};
  const hasText = element.text != null && element.text !== '';
  const hasBg = !!(style.backgroundColor || style.background);
  if (element.type) return element.type;
  if (hasText) return 'text';
  if (hasBg) return 'rectangle';
  const w = parseFloat(style.width || '0');
  const h = parseFloat(style.height || '0');
  if (w > 200 && h > 100) return 'frame';
  return 'rectangle';
}

function getDisplayName(element: Element): string {
  if (element.name && element.name !== 'Div Element') return element.name;
  const type = inferType(element);
  if (type === 'text') return element.text?.slice(0, 30) || 'Text';
  if (type === 'frame') return 'Frame';
  if (type === 'group') return 'Group';
  return 'Rectangle';
}

// ─── Element type icon ──────────────────────────────────────────────────────────

function ElementIcon({ element }: { element: Element }) {
  const type = inferType(element);
  if (type === 'frame') return <FrameIcon />;
  if (type === 'text') {
    return (
      <span style={{ fontSize: 11, fontWeight: 600, letterSpacing: '-0.025em' }}>Aa</span>
    );
  }
  const bgColor = element.style.backgroundColor || element.style.background;
  return (
    <span
      style={{
        width: 10,
        height: 3,
        border: '1px solid currentColor',
        borderRadius: 0,
        display: 'block',
        backgroundColor: bgColor || 'transparent',
        opacity: bgColor ? 0.6 : 1,
      }}
    />
  );
}

// ─── Tree builder ────────────────────────────────────────────────────────────

interface TreeNode {
  element: Element;
  children: TreeNode[];
}

function buildTree(elements: Element[]): TreeNode[] {
  const map = new Map<string, TreeNode>();
  elements.forEach((el) => map.set(el.id, { element: el, children: [] }));
  const roots: TreeNode[] = [];
  elements.forEach((el) => {
    const node = map.get(el.id)!;
    const parentId = el.parentId;
    if (parentId && map.has(parentId)) {
      map.get(parentId)!.children.push(node);
    } else {
      roots.push(node);
    }
  });
  return roots;
}

function LayerTreeItem({
  node,
  depth,
  expandedNodes,
  onToggle,
  selectedId,
  onSelect,
}: {
  node: TreeNode;
  depth: number;
  expandedNodes: Set<string>;
  onToggle: (id: string) => void;
  selectedId: string | undefined;
  onSelect: (el: Element) => void;
}) {
  const { element, children } = node;
  const hasChildren = children.length > 0;
  const isExpanded = expandedNodes.has(element.id);
  const isSelected = selectedId === element.id;

  return (
    <>
      <div
        data-node-id={element.id}
        onClick={() => onSelect(element)}
        style={{
          display: 'flex',
          alignItems: 'center',
          paddingLeft: `${12 + depth * 16}px`,
          paddingRight: 8,
          height: 48,
          cursor: 'pointer',
          background: isSelected ? '#0066ff' : 'transparent',
          color: isSelected ? '#fff' : '#aaa',
          borderRadius: 4,
          margin: '0 4px',
          gap: 0,
          transition: 'background 0.1s',
        }}
        onMouseEnter={(e) => {
          if (!isSelected) (e.currentTarget as HTMLDivElement).style.background = 'rgba(255,255,255,0.05)';
        }}
        onMouseLeave={(e) => {
          if (!isSelected) (e.currentTarget as HTMLDivElement).style.background = 'transparent';
        }}
      >
        {/* Collapse chevron */}
        <div
          style={{
            width: 24,
            height: 24,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
            opacity: hasChildren ? 0.6 : 0,
            transform: isExpanded ? 'rotate(0deg)' : 'rotate(-90deg)',
            transition: 'transform 0.15s',
          }}
          onClick={(e) => {
            if (hasChildren) {
              e.stopPropagation();
              onToggle(element.id);
            }
          }}
        >
          <ChevronIcon />
        </div>

        {/* Type icon */}
        <div
          style={{
            width: 48,
            height: 48,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            flexShrink: 0,
            color: isSelected ? '#fff' : '#888',
          }}
        >
          <ElementIcon element={element} />
        </div>

        {/* Name */}
        <div
          style={{
            flex: 1,
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
            fontSize: 12,
            fontWeight: 500,
          }}
        >
          {getDisplayName(element)}
        </div>
      </div>

      {/* Children */}
      {hasChildren && isExpanded &&
        children.map((child) => (
          <LayerTreeItem
            key={child.element.id}
            node={child}
            depth={depth + 1}
            expandedNodes={expandedNodes}
            onToggle={onToggle}
            selectedId={selectedId}
            onSelect={onSelect}
          />
        ))}
    </>
  );
}

// ─── Page item ────────────────────────────────────────────────────────────────

function TrashIcon() {
  return (
    <svg width={12} height={12} viewBox="0 0 12 12" fill="none" stroke="currentColor" strokeWidth={1.5}>
      <path d="M1.5 3H10.5M4 3V1.5H8V3M4.5 5.5V9.5M7.5 5.5V9.5M2 3L2.5 10.5H9.5L10 3H2Z" strokeLinecap="round" strokeLinejoin="round"/>
    </svg>
  );
}

function PageItem({
  page,
  isCurrent,
  onSelect,
  onDelete,
  canDelete,
}: {
  page: Page;
  isCurrent: boolean;
  onSelect: () => void;
  onDelete: () => void;
  canDelete: boolean;
}) {
  return (
    <div
      onClick={onSelect}
      style={{
        display: 'flex',
        alignItems: 'center',
        paddingLeft: 12,
        paddingRight: 8,
        height: 48,
        cursor: 'pointer',
        background: isCurrent ? '#2a2a2a' : 'transparent',
        color: isCurrent ? '#fff' : '#aaa',
        borderRadius: 4,
        margin: '0 4px',
        gap: 0,
        transition: 'background 0.1s',
      }}
      onMouseEnter={(e) => {
        if (!isCurrent) (e.currentTarget as HTMLDivElement).style.background = 'rgba(255,255,255,0.05)';
      }}
      onMouseLeave={(e) => {
        if (!isCurrent) (e.currentTarget as HTMLDivElement).style.background = 'transparent';
      }}
    >
      {/* No collapse chevron for pages */}
      <div style={{ width: 24, height: 24, flexShrink: 0 }} />

      {/* Page icon */}
      <div
        style={{
          width: 48,
          height: 48,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          flexShrink: 0,
          color: isCurrent ? '#fff' : '#888',
        }}
      >
        <PageIcon />
      </div>

      {/* Name */}
      <div
        style={{
          flex: 1,
          overflow: 'hidden',
          textOverflow: 'ellipsis',
          whiteSpace: 'nowrap',
          fontSize: 12,
          fontWeight: 500,
        }}
      >
        {page.name}
      </div>

      {/* Selected check */}
      {isCurrent && (
        <CheckIcon />
      )}
      {/* Delete button */}
      {canDelete && (
        <div
          onClick={(e) => { e.stopPropagation(); onDelete(); }}
          style={{
            width: 24,
            height: 24,
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            color: '#555',
            cursor: 'pointer',
            borderRadius: 4,
            flexShrink: 0,
          }}
          onMouseEnter={e => (e.currentTarget as HTMLDivElement).style.color = '#c44'}
          onMouseLeave={e => (e.currentTarget as HTMLDivElement).style.color = '#555'}
        >
          <TrashIcon />
        </div>
      )}
    </div>
  );
}

// ─── Artboard button ────────────────────────────────────────────────────────────

function ArtboardBtn({ label, sub, onClick }: { label: string; sub: string; onClick: () => void }) {
  return (
    <button
      onClick={onClick}
      style={{
        padding: '8px 10px',
        background: '#2a2a2a',
        border: '1px solid #333',
        borderRadius: 6,
        color: '#aaa',
        cursor: 'pointer',
        textAlign: 'left',
        display: 'flex',
        justifyContent: 'space-between',
        alignItems: 'center',
        fontSize: 12,
        fontFamily: 'system-ui, sans-serif',
      }}
      onMouseEnter={e => (e.currentTarget.style.background = '#333')}
      onMouseLeave={e => (e.currentTarget.style.background = '#2a2a2a')}
    >
      <div>
        <div style={{ color: '#fff', fontWeight: 500 }}>{label}</div>
        <div style={{ color: '#666', fontSize: 10 }}>{sub}</div>
      </div>
      <span style={{ color: '#555', fontSize: 14 }}>+</span>
    </button>
  );
}

// ─── LayerPanel ───────────────────────────────────────────────────────────────

export function LayerPanel() {
  const {
    document,
    selection,
    selectElement,
    expandedNodes,
    toggleExpanded,
    setCurrentPage,
    addPage,
    deletePage,
    setActiveTool,
    selectedArtboardId,
    selectArtboard,
  } = useEditorStore();
  const [pagesExpanded, setPagesExpanded] = useState(true);
  const [copied, setCopied] = useState(false);
  const docId = bridge.getCurrentDocId();

  const handleCopyId = () => {
    navigator.clipboard.writeText(docId).catch(() => {});
    setCopied(true);
    setTimeout(() => setCopied(false), 1500);
  };

  if (!document) return null;
  if (document.pages.length === 0) {
    return (
      <div style={{
        width: 240,
        background: '#1a1a1a',
        borderRight: '1px solid #333',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        justifyContent: 'center',
        gap: 8,
        padding: 16,
      }}>
        <div style={{ fontSize: 20 }}>🎨</div>
        <div style={{ color: '#666', fontSize: 12 }}>No artboards</div>
        <div style={{ display: 'flex', flexDirection: 'column', gap: 6, width: '100%', marginTop: 8 }}>
          <ArtboardBtn label="Desktop Web" sub="1440×900" onClick={() => addPage({ id: `page-${Date.now()}`, name: 'Desktop', x: 0, y: 0, width: 1440, height: 900, elements: [] })} />
          <ArtboardBtn label="Tablet" sub="768×1024" onClick={() => addPage({ id: `page-${Date.now()}`, name: 'Tablet', x: 0, y: 0, width: 768, height: 1024, elements: [] })} />
          <ArtboardBtn label="Mobile" sub="375×812" onClick={() => addPage({ id: `page-${Date.now()}`, name: 'Mobile', x: 0, y: 0, width: 375, height: 812, elements: [] })} />
          <ArtboardBtn label="Custom" sub="choose size" onClick={() => {
            const w = prompt('Width (px):', '1440');
            const h = prompt('Height (px):', '900');
            if (w && h) addPage({ id: `page-${Date.now()}`, name: 'Custom', x: 0, y: 0, width: parseInt(w), height: parseInt(h), elements: [] });
          }} />
        </div>
      </div>
    );
  }

  const currentPage = document.pages[document.current_page];
  if (!currentPage) return null;
  const tree = buildTree(currentPage.elements);

  const handleSelectElement = (element: Element) => {
    setActiveTool('select');
    selectElement({
      nodeId: element.id,
      x: parseFloat(element.style.left || '0'),
      y: parseFloat(element.style.top || '0'),
      width: parseFloat(element.style.width || '100'),
      height: parseFloat(element.style.height || '100'),
    });
    useEditorStore.getState().expandToNode(element.id);
  };

  const handleAddPage = () => {
    const w = prompt('Width (px):', '1440');
    const h = prompt('Height (px):', '900');
    const name = prompt('Name:', `Page ${document.pages.length + 1}`);
    if (!w || !h) return;
    const newPage: Page = {
      id: `page-${Date.now()}`,
      name: name || `Page ${document.pages.length + 1}`,
      x: 0,
      y: document.pages.reduce((sum, p) => sum + p.height + 20, 0),
      width: parseInt(w),
      height: parseInt(h),
      elements: [],
    };
    addPage(newPage);
    setCurrentPage(document.pages.length);
  };

  return (
    <div
      style={{
        width: 240,
        background: '#1a1a1a',
        borderRight: '1px solid #333',
        display: 'flex',
        flexDirection: 'column',
        overflow: 'hidden',
      }}
    >
      {/* ── Header: project name ── */}
      <div
        style={{
          display: 'flex',
          alignItems: 'center',
          gap: 8,
          padding: '8px 10px',
          borderBottom: '1px solid #333',
        }}
      >
        <div style={{ width: 28, height: 28, display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#666', flexShrink: 0 }}>
          <GridIcon />
        </div>
        <div
          style={{
            flex: 1,
            height: 24,
            display: 'flex',
            alignItems: 'center',
            padding: '0 6px',
            borderRadius: 4,
            fontSize: 14,
            fontWeight: 500,
            color: '#fff',
            overflow: 'hidden',
            textOverflow: 'ellipsis',
            whiteSpace: 'nowrap',
          }}
        >
          {document.title || 'Untitled'}
          <button
            title="Copy doc ID for AI"
            onClick={handleCopyId}
            style={{
              marginLeft: 8,
              padding: '1px 5px',
              fontSize: 9,
              background: copied ? '#2a6' : '#333',
              color: copied ? '#fff' : '#888',
              border: 'none',
              borderRadius: 3,
              cursor: 'pointer',
              flexShrink: 0,
            }}
          >
            {copied ? 'Copied!' : docId}
          </button>
        </div>
      </div>

      {/* ── Scrollable area ── */}
      <div className="paper-scroll" style={{ flex: 1, overflow: 'auto' }}>

        {/* Pages section */}
        <div style={{ padding: '8px 0' }}>
          {/* Pages subheader */}
          <div
            onClick={() => setPagesExpanded(p => !p)}
            style={{
              display: 'flex',
              alignItems: 'center',
              marginBottom: 4,
              paddingLeft: 12,
              paddingRight: 12,
              height: 32,
              cursor: 'pointer',
              gap: 4,
            }}
          >
            <div
              style={{
                transform: pagesExpanded ? 'rotate(0deg)' : 'rotate(-90deg)',
                transition: 'transform 0.15s',
                color: '#666',
                display: 'flex',
                alignItems: 'center',
              }}
            >
              <ChevronIcon />
            </div>
            <span style={{ flex: 1, fontSize: 11, fontWeight: 600, color: '#888', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Artboards
            </span>
            {/* Add page button */}
            <div
              onClick={(e) => { e.stopPropagation(); handleAddPage(); }}
              style={{
                width: 24,
                height: 24,
                display: 'flex',
                alignItems: 'center',
                justifyContent: 'center',
                color: '#666',
                cursor: 'pointer',
                borderRadius: 4,
              }}
              onMouseEnter={e => (e.currentTarget as HTMLDivElement).style.color = '#aaa'}
              onMouseLeave={e => (e.currentTarget as HTMLDivElement).style.color = '#666'}
            >
              <AddIcon />
            </div>
          </div>

          {/* Page items */}
          {pagesExpanded && document.pages.map((page, index) => (
            <PageItem
              key={page.id}
              page={page}
              isCurrent={!!selectedArtboardId && selectedArtboardId === page.id || !selectedArtboardId && document.current_page === index}
              onSelect={() => { selectArtboard(page.id); setCurrentPage(index); }}
              onDelete={() => deletePage(page.id)}
              canDelete={document.pages.length > 1}
            />
          ))}
        </div>

        {/* Divider */}
        <div style={{ height: 1, background: '#333', margin: '0 8px' }} />

        {/* Layers section */}
        <div style={{ paddingTop: 8, paddingBottom: 16 }}>
          <div style={{ paddingLeft: 12, paddingRight: 12, height: 32, display: 'flex', alignItems: 'center' }}>
            <span style={{ fontSize: 11, fontWeight: 600, color: '#888', textTransform: 'uppercase', letterSpacing: '0.5px' }}>
              Elements
            </span>
          </div>

          {currentPage.elements.length === 0 ? (
            <div style={{ padding: 16, textAlign: 'center', color: '#444', fontSize: 12 }}>
              No elements yet.
              <br />
              Double-click canvas to add.
            </div>
          ) : (
            tree.map((node) => (
              <LayerTreeItem
                key={node.element.id}
                node={node}
                depth={0}
                expandedNodes={expandedNodes}
                onToggle={toggleExpanded}
                selectedId={selection?.nodeId}
                onSelect={handleSelectElement}
              />
            ))
          )}
        </div>
      </div>

      {/* ── Bottom brand + new doc ── */}
      <div
        style={{
          padding: '8px 12px',
          borderTop: '1px solid #333',
          fontSize: 11,
          color: '#555',
          display: 'flex',
          gap: 8,
          alignItems: 'center',
        }}
      >
        <span style={{ fontWeight: 600 }}>Paper</span>
        <span>Clone</span>
        <button
          onClick={() => {
            const id = `doc-${Date.now().toString(36)}`;
            bridge.switchDocument(id);
            bridge.newDocument().then((doc: any) => {
              useEditorStore.getState().setDocument(doc);
            }).catch(() => {});
          }}
          style={{
            marginLeft: 'auto',
            padding: '2px 6px',
            fontSize: 10,
            background: '#333',
            color: '#888',
            border: 'none',
            borderRadius: 3,
            cursor: 'pointer',
          }}
        >
          + New Doc
        </button>
      </div>
    </div>
  );
}
