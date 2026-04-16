import { useEditorStore } from '../store/editorStore';

export function PropertyPanel() {
  const { document, selection, updateElement } = useEditorStore();

  if (!document || !selection) {
    return (
      <div
        style={{
          width: 280,
          background: '#1a1a1a',
          borderLeft: '1px solid #333',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          color: '#666',
          fontSize: 12,
        }}
      >
        Select an element to edit properties
      </div>
    );
  }

  const currentPage = document.pages[document.current_page];
  const element = currentPage.elements.find((el) => el.id === selection.nodeId);

  if (!element) {
    return null;
  }

  const updateStyle = (key: string, value: string) => {
    updateElement(element.id, {
      style: { ...element.style, [key]: value },
    });
  };

  return (
    <div
      className="property-panel"
      style={{
        width: 280,
        background: '#1a1a1a',
        borderLeft: '1px solid #333',
        overflow: 'auto',
      }}
    >
      {/* Header */}
      <div
        style={{
          padding: '12px 16px',
          borderBottom: '1px solid #333',
        }}
      >
        <span style={{ color: '#fff', fontSize: 12, fontWeight: 600 }}>
          {element.name}
        </span>
      </div>

      {/* Position Type */}
      <div style={{ padding: '0 16px 16px' }}>
        <div
          style={{
            color: '#888',
            fontSize: 10,
            textTransform: 'uppercase',
            marginBottom: 8,
          }}
        >
          Position
        </div>
        <select
          value={element.style.position || 'absolute'}
          onChange={(e) => updateStyle('position', e.target.value)}
          style={{
            ...inputStyle,
            cursor: 'pointer',
          }}
        >
          <option value="absolute">Absolute</option>
          <option value="relative">Relative</option>
          <option value="static">Static</option>
        </select>
      </div>

      {/* Position */}
      <div style={{ padding: '0 16px 16px' }}>
        <div
          style={{
            color: '#888',
            fontSize: 10,
            textTransform: 'uppercase',
            marginBottom: 8,
          }}
        >
          Coordinates
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
          <div>
            <label style={{ color: '#666', fontSize: 10 }}>X</label>
            <input
              type="number"
              value={parseFloat(element.style.left) || 0}
              onChange={(e) => updateStyle('left', `${e.target.value}px`)}
              style={inputStyle}
            />
          </div>
          <div>
            <label style={{ color: '#666', fontSize: 10 }}>Y</label>
            <input
              type="number"
              value={parseFloat(element.style.top) || 0}
              onChange={(e) => updateStyle('top', `${e.target.value}px`)}
              style={inputStyle}
            />
          </div>
        </div>
      </div>

      {/* Size */}
      <div style={{ padding: '0 16px 16px' }}>
        <div
          style={{
            color: '#888',
            fontSize: 10,
            textTransform: 'uppercase',
            marginBottom: 8,
          }}
        >
          Size
        </div>
        <div style={{ display: 'grid', gridTemplateColumns: '1fr 1fr', gap: 8 }}>
          <div>
            <label style={{ color: '#666', fontSize: 10 }}>W</label>
            <input
              type="number"
              value={parseFloat(element.style.width) || 100}
              onChange={(e) => updateStyle('width', `${e.target.value}px`)}
              style={inputStyle}
            />
          </div>
          <div>
            <label style={{ color: '#666', fontSize: 10 }}>H</label>
            <input
              type="number"
              value={parseFloat(element.style.height) || 100}
              onChange={(e) => updateStyle('height', `${e.target.value}px`)}
              style={inputStyle}
            />
          </div>
        </div>
      </div>

      {/* Background */}
      <div style={{ padding: '0 16px 16px' }}>
        <div
          style={{
            color: '#888',
            fontSize: 10,
            textTransform: 'uppercase',
            marginBottom: 8,
          }}
        >
          Fill
        </div>
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          <input
            type="color"
            value={element.style.backgroundColor || '#ffffff'}
            onChange={(e) => updateStyle('backgroundColor', e.target.value)}
            style={{
              ...inputStyle,
              width: 40,
              height: 32,
              padding: 2,
              cursor: 'pointer',
            }}
          />
          <input
            type="text"
            value={element.style.backgroundColor || '#ffffff'}
            onChange={(e) => updateStyle('backgroundColor', e.target.value)}
            style={{ ...inputStyle, flex: 1 }}
          />
        </div>
      </div>

      {/* Border Radius */}
      <div style={{ padding: '0 16px 16px' }}>
        <div
          style={{
            color: '#888',
            fontSize: 10,
            textTransform: 'uppercase',
            marginBottom: 8,
          }}
        >
          Border Radius
        </div>
        <input
          type="number"
          value={parseFloat(element.style.borderRadius) || 0}
          onChange={(e) => updateStyle('borderRadius', `${e.target.value}px`)}
          style={inputStyle}
        />
      </div>

      {/* Text Color */}
      {element.text !== undefined && (
        <div style={{ padding: '0 16px 16px' }}>
          <div
            style={{
              color: '#888',
              fontSize: 10,
              textTransform: 'uppercase',
              marginBottom: 8,
            }}
          >
            Text Color
          </div>
          <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
            <input
              type="color"
              value={element.style.color || '#222222'}
              onChange={(e) => updateStyle('color', e.target.value)}
              style={{
                ...inputStyle,
                width: 40,
                height: 32,
                padding: 2,
                cursor: 'pointer',
              }}
            />
            <input
              type="text"
              value={element.style.color || '#222222'}
              onChange={(e) => updateStyle('color', e.target.value)}
              style={{ ...inputStyle, flex: 1 }}
            />
          </div>
        </div>
      )}

      {/* Font Size */}
      {element.text !== undefined && (
        <div style={{ padding: '0 16px 16px' }}>
          <div
            style={{
              color: '#888',
              fontSize: 10,
              textTransform: 'uppercase',
              marginBottom: 8,
            }}
          >
            Font Size
          </div>
          <input
            type="number"
            value={parseFloat(element.style.fontSize) || 16}
            onChange={(e) => updateStyle('fontSize', `${e.target.value}px`)}
            style={inputStyle}
          />
        </div>
      )}
    </div>
  );
}

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
