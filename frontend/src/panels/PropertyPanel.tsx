import { useRef } from 'react';
import { useEditorStore } from '../store/editorStore';
import type { Page } from '../types';

const inputStyle: React.CSSProperties = {
  width: '100%',
  padding: '6px 8px',
  background: '#2a2a2a',
  border: '1px solid #333',
  borderRadius: 4,
  color: '#fff',
  fontSize: 12,
  outline: 'none',
};

// ─── Artboard Properties ───────────────────────────────────────────────────────

function ArtboardProps({ page }: { page: Page }) {
  const { document, setDocument, updateArtboard } = useEditorStore();
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const updatePage = (updates: Partial<Page>) => {
    if (!document) return;
    // Update local store immediately
    const pages = document.pages.map(p => p.id === page.id ? { ...p, ...updates } : p);
    setDocument({ ...document, pages });
    // Debounced sync to backend (store handles pause/resume)
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => {
      updateArtboard(page.id, updates);
    }, 500);
  };

  return (
    <>
      {/* Header */}
      <div style={{ padding: '12px 16px', borderBottom: '1px solid #333' }}>
        <span style={{ color: '#fff', fontSize: 12, fontWeight: 600 }}>{page.name}</span>
      </div>

      {/* Position on canvas */}
      <div style={{ padding: '0 16px 16px' }}>
        <div style={{ color: '#888', fontSize: 10, textTransform: 'uppercase', marginBottom: 8 }}>
          Position
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
          <div>
            <label style={{ color: '#666', fontSize: 10 }}>X</label>
            <input
              type="number"
              value={page.x}
              onChange={(e) => updatePage({ x: parseInt(e.target.value) || 0 })}
              style={inputStyle}
            />
          </div>
          <div>
            <label style={{ color: '#666', fontSize: 10 }}>Y</label>
            <input
              type="number"
              value={page.y}
              onChange={(e) => updatePage({ y: parseInt(e.target.value) || 0 })}
              style={inputStyle}
            />
          </div>
        </div>
      </div>

      {/* Artboard Size */}
      <div style={{ padding: '0 16px 16px' }}>
        <div style={{ color: '#888', fontSize: 10, textTransform: 'uppercase', marginBottom: 8 }}>
          Size
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
          <div>
            <label style={{ color: '#666', fontSize: 10 }}>W</label>
            <input
              type="number"
              value={page.width}
              onChange={(e) => updatePage({ width: parseInt(e.target.value) || 375 })}
              style={inputStyle}
            />
          </div>
          <div>
            <label style={{ color: '#666', fontSize: 10 }}>H</label>
            <input
              type="number"
              value={page.height}
              onChange={(e) => updatePage({ height: parseInt(e.target.value) || 812 })}
              style={inputStyle}
            />
          </div>
        </div>
      </div>

      {/* Background Color */}
      <div style={{ padding: '0 16px 16px' }}>
        <div style={{ color: '#888', fontSize: 10, textTransform: 'uppercase', marginBottom: 8 }}>
          Background
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <input
            type="color"
            value={page.backgroundColor || '#ffffff'}
            onChange={(e) => updatePage({ backgroundColor: e.target.value })}
            style={{ ...inputStyle, width: 40, height: 32, padding: 2, cursor: 'pointer' }}
          />
          <input
            type="text"
            value={page.backgroundColor || '#ffffff'}
            onChange={(e) => updatePage({ backgroundColor: e.target.value })}
            style={{ ...inputStyle, flex: 1 }}
          />
        </div>
      </div>

      {/* Preset sizes */}
      <div style={{ padding: '0 16px 16px' }}>
        <div style={{ color: '#888', fontSize: 10, textTransform: 'uppercase', marginBottom: 8 }}>
          Presets
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 4 }}>
          {[
            { label: 'Desktop', w: 1440, h: 900 },
            { label: 'Laptop', w: 1366, h: 768 },
            { label: 'Tablet', w: 768, h: 1024 },
            { label: 'Mobile', w: 375, h: 812 },
          ].map(preset => (
            <button
              key={preset.label}
              onClick={() => updatePage({ width: preset.w, height: preset.h })}
              style={{
                padding: '4px 6px',
                background: '#2a2a2a',
                border: '1px solid #333',
                borderRadius: 4,
                color: '#aaa',
                cursor: 'pointer',
                fontSize: 10,
                fontFamily: 'system-ui, sans-serif',
              }}
              onMouseEnter={e => (e.currentTarget.style.background = '#333')}
              onMouseLeave={e => (e.currentTarget.style.background = '#2a2a2a')}
            >
              {preset.label}<br />
              <span style={{ color: '#555', fontSize: 9 }}>{preset.w}×{preset.h}</span>
            </button>
          ))}
        </div>
      </div>
    </>
  );
}

// ─── Element Properties ───────────────────────────────────────────────────────

function ElementProps() {
  const { document, selection, updateElement } = useEditorStore();
  if (!document || !selection) return null;

  const currentPage = document.pages[document.current_page];
  const element = currentPage.elements.find((el) => el.id === selection.nodeId);
  if (!element) return null;

  const updateStyle = (key: string, value: string) => {
    updateElement(element.id, {
      style: { ...element.style, [key]: value },
    });
  };

  return (
    <>
      {/* Header */}
      <div style={{ padding: '12px 16px', borderBottom: '1px solid #333' }}>
        <span style={{ color: '#fff', fontSize: 12, fontWeight: 600 }}>
          {element.name}
        </span>
      </div>

      {/* Position */}
      <div style={{ padding: '0 16px 16px' }}>
        <div style={{ color: '#888', fontSize: 10, textTransform: 'uppercase', marginBottom: 8 }}>
          Coordinates
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
          <div>
            <label style={{ color: '#666', fontSize: 10 }}>X</label>
            <input type="number" value={parseFloat(element.style.left) || 0}
              onChange={(e) => updateStyle('left', `${e.target.value}px`)} style={inputStyle} />
          </div>
          <div>
            <label style={{ color: '#666', fontSize: 10 }}>Y</label>
            <input type="number" value={parseFloat(element.style.top) || 0}
              onChange={(e) => updateStyle('top', `${e.target.value}px`)} style={inputStyle} />
          </div>
        </div>
      </div>

      {/* Size */}
      <div style={{ padding: '0 16px 16px' }}>
        <div style={{ color: '#888', fontSize: 10, textTransform: 'uppercase', marginBottom: 8 }}>
          Size
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
          <div>
            <label style={{ color: '#666', fontSize: 10 }}>W</label>
            <input type="number" value={parseFloat(element.style.width) || 100}
              onChange={(e) => updateStyle('width', `${e.target.value}px`)} style={inputStyle} />
          </div>
          <div>
            <label style={{ color: '#666', fontSize: 10 }}>H</label>
            <input type="number" value={parseFloat(element.style.height) || 100}
              onChange={(e) => updateStyle('height', `${e.target.value}px`)} style={inputStyle} />
          </div>
        </div>
      </div>

      {/* Background */}
      <div style={{ padding: '0 16px 16px' }}>
        <div style={{ color: '#888', fontSize: 10, textTransform: 'uppercase', marginBottom: 8 }}>
          Fill
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <input type="color" value={element.style.backgroundColor || '#ffffff'}
            onChange={(e) => updateStyle('backgroundColor', e.target.value)}
            style={{ ...inputStyle, width: 40, height: 32, padding: 2, cursor: 'pointer' }} />
          <input type="text" value={element.style.backgroundColor || '#ffffff'}
            onChange={(e) => updateStyle('backgroundColor', e.target.value)}
            style={{ ...inputStyle, flex: 1 }} />
        </div>
      </div>

      {/* Border Radius */}
      <div style={{ padding: '0 16px 16px' }}>
        <div style={{ color: '#888', fontSize: 10, textTransform: 'uppercase', marginBottom: 8 }}>
          Border Radius
        </div>
        <input type="number" value={parseFloat(element.style.borderRadius) || 0}
          onChange={(e) => updateStyle('borderRadius', `${e.target.value}px`)} style={inputStyle} />
      </div>

      {/* Text properties */}
      {element.text !== undefined && (
        <>
          <div style={{ padding: '0 16px 16px' }}>
            <div style={{ color: '#888', fontSize: 10, textTransform: 'uppercase', marginBottom: 8 }}>
              Text Color
            </div>
            <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
              <input type="color" value={element.style.color || '#222222'}
                onChange={(e) => updateStyle('color', e.target.value)}
                style={{ ...inputStyle, width: 40, height: 32, padding: 2, cursor: 'pointer' }} />
              <input type="text" value={element.style.color || '#222222'}
                onChange={(e) => updateStyle('color', e.target.value)}
                style={{ ...inputStyle, flex: 1 }} />
            </div>
          </div>
          <div style={{ padding: '0 16px 16px' }}>
            <div style={{ color: '#888', fontSize: 10, textTransform: 'uppercase', marginBottom: 8 }}>
              Font Size
            </div>
            <input type="number" value={parseFloat(element.style.fontSize) || 16}
              onChange={(e) => updateStyle('fontSize', `${e.target.value}px`)} style={inputStyle} />
          </div>
        </>
      )}
    </>
  );
}

// ─── Property Panel ───────────────────────────────────────────────────────────

export function PropertyPanel() {
  const { document, selection, selectedArtboardId } = useEditorStore();

  if (!document) {
    return (
      <div style={{
        width: 280, background: '#1a1a1a', borderLeft: '1px solid #333',
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: '#666', fontSize: 12,
      }}>
        No document
      </div>
    );
  }

  const currentPage = document.pages[document.current_page];
  if (!currentPage) return null;

  return (
    <div className="paper-scroll" style={{
      width: 280, background: '#1a1a1a', borderLeft: '1px solid #333', overflow: 'auto',
    }}>
      {selectedArtboardId ? (
        <ArtboardProps page={document.pages.find(p => p.id === selectedArtboardId) || currentPage} />
      ) : selection ? (
        <ElementProps />
      ) : (
        <ArtboardProps page={currentPage} />
      )}
    </div>
  );
}
