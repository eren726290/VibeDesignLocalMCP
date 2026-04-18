import { useRef, useState } from 'react';
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

// ─── Shared color row ─────────────────────────────────────────────────────────

function ColorRow({ label, value, onChange }: { label: string; value: string; onChange: (v: string) => void }) {
  return (
    <div style={{ padding: '0 16px 12px' }}>
      <div style={{ color: '#888', fontSize: 10, textTransform: 'uppercase', marginBottom: 6 }}>
        {label}
      </div>
      <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
        <input type="color" value={value || '#000000'}
          onChange={(e) => onChange(e.target.value)}
          style={{ ...inputStyle, width: 36, height: 30, padding: 2, cursor: 'pointer' }} />
        <input type="text" value={value || ''}
          onChange={(e) => onChange(e.target.value)}
          style={{ ...inputStyle, flex: 1 }} />
      </div>
    </div>
  );
}

// ─── Artboard Properties ───────────────────────────────────────────────────────

function ArtboardProps({ page }: { page: Page }) {
  const { document, setDocument, updateArtboard } = useEditorStore();
  const debounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);

  const updatePage = (updates: Partial<Page>) => {
    if (!document) return;
    const pages = document.pages.map(p => p.id === page.id ? { ...p, ...updates } : p);
    setDocument({ ...document, pages });
    if (debounceRef.current) clearTimeout(debounceRef.current);
    debounceRef.current = setTimeout(() => updateArtboard(page.id, updates), 500);
  };

  return (
    <>
      <div style={{ padding: '12px 16px', borderBottom: '1px solid #333' }}>
        <span style={{ color: '#fff', fontSize: 12, fontWeight: 600 }}>{page.name}</span>
      </div>

      <div style={{ padding: '0 16px 16px' }}>
        <div style={{ color: '#888', fontSize: 10, textTransform: 'uppercase', marginBottom: 8 }}>Position</div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
          {[['X', page.x, 'x'], ['Y', page.y, 'y']].map(([label, val, key]) => (
            <div key={key}>
              <label style={{ color: '#666', fontSize: 10 }}>{label}</label>
              <input type="number" value={val as number}
                onChange={(e) => updatePage({ [key]: parseInt(e.target.value) || 0 })}
                style={inputStyle} />
            </div>
          ))}
        </div>
      </div>

      <div style={{ padding: '0 16px 16px' }}>
        <div style={{ color: '#888', fontSize: 10, textTransform: 'uppercase', marginBottom: 8 }}>Size</div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
          {[['W', page.width], ['H', page.height]].map(([label, val]) => (
            <div key={label}>
              <label style={{ color: '#666', fontSize: 10 }}>{label}</label>
              <input type="number" value={val as number}
                onChange={(e) => updatePage({ [label === 'W' ? 'width' : 'height']: parseInt(e.target.value) || 375 })}
                style={inputStyle} />
            </div>
          ))}
        </div>
      </div>

      <div style={{ padding: '0 16px 16px' }}>
        <div style={{ color: '#888', fontSize: 10, textTransform: 'uppercase', marginBottom: 8 }}>Background</div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <input type="color" value={page.backgroundColor || '#ffffff'}
            onChange={(e) => updatePage({ backgroundColor: e.target.value })}
            style={{ ...inputStyle, width: 40, height: 32, padding: 2, cursor: 'pointer' }} />
          <input type="text" value={page.backgroundColor || '#ffffff'}
            onChange={(e) => updatePage({ backgroundColor: e.target.value })}
            style={{ ...inputStyle, flex: 1 }} />
        </div>
      </div>

      <div style={{ padding: '0 16px 16px' }}>
        <div style={{ color: '#888', fontSize: 10, textTransform: 'uppercase', marginBottom: 8 }}>Presets</div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 4 }}>
          {[
            { label: 'Desktop', w: 1440, h: 900 },
            { label: 'Laptop', w: 1366, h: 768 },
            { label: 'Tablet', w: 768, h: 1024 },
            { label: 'Mobile', w: 375, h: 812 },
          ].map(preset => (
            <button key={preset.label}
              onClick={() => updatePage({ width: preset.w, height: preset.h })}
              style={{ padding: '4px 6px', background: '#2a2a2a', border: '1px solid #333', borderRadius: 4, color: '#aaa', cursor: 'pointer', fontSize: 10, fontFamily: 'system-ui, sans-serif' }}
              onMouseEnter={e => (e.currentTarget.style.background = '#333')}
              onMouseLeave={e => (e.currentTarget.style.background = '#2a2a2a')}
            >
              {preset.label}<br /><span style={{ color: '#555', fontSize: 9 }}>{preset.w}×{preset.h}</span>
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

  const textDebounceRef = useRef<ReturnType<typeof setTimeout> | null>(null);
  const [textValue, setTextValue] = useState(element.text ?? '');

  const updateStyle = (key: string, value: string) => {
    updateElement(element.id, {
      style: { ...element.style, [key]: value },
    });
  };

  const updateText = (newText: string) => {
    setTextValue(newText);
    if (textDebounceRef.current) clearTimeout(textDebounceRef.current);
    textDebounceRef.current = setTimeout(() => {
      updateElement(element.id, { text: newText });
    }, 300);
  };

  // ── SVG element types ──────────────────────────────────────────────────────
  const isSvg = ['svg', 'path', 'circle', 'rect', 'line', 'polyline', 'polygon', 'ellipse'].includes(element.tag);
  const isCircle = element.tag === 'circle';
  const isRect = element.tag === 'rect';
  const isLine = element.tag === 'line';
  const isSvgContainer = element.tag === 'svg';

  const hasText = element.text !== undefined;

  return (
    <>
      {/* Header */}
      <div style={{ padding: '12px 16px', borderBottom: '1px solid #333' }}>
        <span style={{ color: '#fff', fontSize: 12, fontWeight: 600 }}>{element.name}</span>
        <span style={{ marginLeft: 6, color: '#555', fontSize: 10 }}>{element.tag}</span>
      </div>

      {/* Text content — editable at the top for text elements */}
      {hasText && (
        <div style={{ padding: '12px 16px', borderBottom: '1px solid #222' }}>
          <div style={{ color: '#888', fontSize: 10, textTransform: 'uppercase', marginBottom: 6 }}>Text</div>
          <textarea
            value={textValue}
            onChange={(e) => updateText(e.target.value)}
            onFocus={() => setTextValue(element.text ?? '')}
            rows={3}
            style={{
              ...inputStyle,
              resize: 'vertical',
              minHeight: 60,
              fontFamily: element.style.fontFamily || 'system-ui',
              fontSize: parseFloat(element.style.fontSize || '14'),
              lineHeight: 1.4,
            }}
          />
        </div>
      )}

      {/* SVG-specific attributes */}
      {isSvg && (
        <>
          <ColorRow
            label="Fill"
            value={element.style.fill || 'none'}
            onChange={(v) => updateStyle('fill', v)}
          />
          <ColorRow
            label="Stroke"
            value={element.style.stroke || 'none'}
            onChange={(v) => updateStyle('stroke', v)}
          />
          <div style={{ padding: '0 16px 12px' }}>
            <div style={{ color: '#888', fontSize: 10, textTransform: 'uppercase', marginBottom: 6 }}>Stroke Width</div>
            <input type="number" min={0}
              value={parseFloat(element.style.strokeWidth || '0') || 0}
              onChange={(e) => updateStyle('strokeWidth', `${e.target.value}px`)}
              style={inputStyle} />
          </div>
        </>
      )}

      {/* Circle: radius */}
      {isCircle && (
        <div style={{ padding: '0 16px 12px' }}>
          <div style={{ color: '#888', fontSize: 10, textTransform: 'uppercase', marginBottom: 6 }}>Radius (r)</div>
          <input type="number" min={0}
            value={parseFloat(element.style.r || '0') || 0}
            onChange={(e) => updateStyle('r', `${e.target.value}px`)}
            style={inputStyle} />
        </div>
      )}

      {/* Rect / SVG container: border radius */}
      {(isRect || isSvgContainer) && (
        <div style={{ padding: '0 16px 12px' }}>
          <div style={{ color: '#888', fontSize: 10, textTransform: 'uppercase', marginBottom: 6 }}>Border Radius</div>
          <input type="number" min={0}
            value={parseFloat(element.style.borderRadius || '0') || 0}
            onChange={(e) => updateStyle('borderRadius', `${e.target.value}px`)}
            style={inputStyle} />
        </div>
      )}

      {/* Coordinates */}
      {!isSvg && (
        <div style={{ padding: '0 16px 16px' }}>
          <div style={{ color: '#888', fontSize: 10, textTransform: 'uppercase', marginBottom: 8 }}>Coordinates</div>
          <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
            {[['X', 'left'], ['Y', 'top']].map(([label, key]) => (
              <div key={key}>
                <label style={{ color: '#666', fontSize: 10 }}>{label}</label>
                <input type="number"
                  value={parseFloat(element.style[key as keyof typeof element.style] as string) || 0}
                  onChange={(e) => updateStyle(key, `${e.target.value}px`)}
                  style={inputStyle} />
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Size */}
      <div style={{ padding: '0 16px 16px' }}>
        <div style={{ color: '#888', fontSize: 10, textTransform: 'uppercase', marginBottom: 8 }}>Size</div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
          {[['W', 'width'], ['H', 'height']].map(([label, key]) => (
            <div key={key}>
              <label style={{ color: '#666', fontSize: 10 }}>{label}</label>
              <input type="number" min={0}
                value={parseFloat(element.style[key as keyof typeof element.style] as string) || 0}
                onChange={(e) => updateStyle(key, `${e.target.value}px`)}
                style={inputStyle} />
            </div>
          ))}
        </div>
      </div>

      {/* Background / Fill */}
      {!isSvg && (
        <ColorRow
          label="Fill"
          value={element.style.backgroundColor || '#ffffff'}
          onChange={(v) => updateStyle('backgroundColor', v)}
        />
      )}

      {/* Border Radius */}
      {!isSvg && (
        <div style={{ padding: '0 16px 12px' }}>
          <div style={{ color: '#888', fontSize: 10, textTransform: 'uppercase', marginBottom: 6 }}>Border Radius</div>
          <input type="number" min={0}
            value={parseFloat(element.style.borderRadius || '0') || 0}
            onChange={(e) => updateStyle('borderRadius', `${e.target.value}px`)}
            style={inputStyle} />
        </div>
      )}

      {/* Text color & font */}
      {hasText && (
        <>
          <ColorRow
            label="Text Color"
            value={element.style.color || '#222222'}
            onChange={(v) => updateStyle('color', v)}
          />
          <div style={{ padding: '0 16px 12px' }}>
            <div style={{ color: '#888', fontSize: 10, textTransform: 'uppercase', marginBottom: 6 }}>Font Size</div>
            <input type="number" min={1}
              value={parseFloat(element.style.fontSize || '14') || 14}
              onChange={(e) => updateStyle('fontSize', `${e.target.value}px`)}
              style={inputStyle} />
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
        <ElementProps key={selection.nodeId} />
      ) : (
        <ArtboardProps page={currentPage} />
      )}
    </div>
  );
}
