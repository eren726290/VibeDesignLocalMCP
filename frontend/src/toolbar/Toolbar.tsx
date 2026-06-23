import { useEditorStore } from '../store/editorStore';
import type { Tool } from '../types';

// ─── Fit to canvas handler ─────────────────────────────────────────────────────

import { computeFitAllTransform } from '../canvas/viewport';

function fitCanvas() {
  const { document, setTransform } = useEditorStore.getState();
  if (!document || document.pages.length === 0) return;

  const transform = computeFitAllTransform(document);
  if (!transform) return;

  setTransform(transform);
}

// ─── Fit icon: box with a centered dot ───────────────────────────────────────

function FitIcon() {
  return (
    <svg width={18} height={18} viewBox="0 0 18 18" fill="none" stroke="currentColor" strokeWidth={1.25}>
      <rect x={2.5} y={2.5} width={13} height={13} rx={1.5} />
      <circle cx={9} cy={9} r={1.5} fill="currentColor" stroke="none" />
    </svg>
  );
}

// ─── Tool icons ───────────────────────────────────────────────────────────────

const icons: Record<Tool, JSX.Element> = {
  select: (
    <svg width={24} height={24} viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeLinejoin="round">
      <path d="M6.5 20.2627V3.74142C6.5 3.65233 6.60771 3.60771 6.67071 3.67071L18.3293 15.3293C18.3923 15.3923 18.3477 15.5 18.2586 15.5H11.8285C11.698 15.5 11.5727 15.551 11.4793 15.6421L6.66983 20.3343C6.60649 20.3961 6.5 20.3512 6.5 20.2627Z" />
    </svg>
  ),
  pan: (
    <svg width={24} height={24} viewBox="0 0 24 24" fill="currentColor">
      <path d="M12 2C12.8725 2.00013 13.6126 2.55965 13.8857 3.33887C14.2041 3.12494 14.5876 3 15 3C16.1044 3.00016 17 3.89553 17 5V5.26953C17.2943 5.09913 17.6355 5 18 5C19.1044 5.00016 20 5.89553 20 7V9.71387C20 11.3138 19.804 12.9078 19.416 14.46L18.6553 17.5029C18.5524 17.9145 18.5 18.3375 18.5 18.7617C18.5 19.9976 17.4976 20.9999 16.2617 21H8.85059C7.82862 21 7 20.1714 7 19.1494C6.99998 18.6456 6.88284 18.1495 6.65918 17.7002L6.55664 17.5107L4.85449 14.5918C3.9102 12.9729 4.109 10.9309 5.34766 9.52441L5.95117 8.83887L7 7.62695V5C7 3.89543 7.89543 3 9 3C9.41211 3.00006 9.79506 3.12517 10.1133 3.33887C10.3864 2.55946 11.1273 2 12 2ZM12 3C11.4477 3 11 3.44772 11 4V10.5L10.9902 10.6006C10.9437 10.8285 10.7416 10.9999 10.5 11L10.3994 10.9902C10.2039 10.9504 10.0497 10.7961 10.0098 10.6006L10 10.5V5C10 4.48242 9.60653 4.05635 9.10254 4.00488L9 4C8.44772 4 8 4.44772 8 5V12C8 12.2761 7.77603 12.4999 7.5 12.5C7.22386 12.5 7 12.2761 7 12V9.15527L6.70215 9.5L6.09766 10.1855L5.92871 10.3945C5.12852 11.4643 5.03614 12.9191 5.71777 14.0879L7.4209 17.0068C7.80017 17.6571 7.99997 18.3966 8 19.1494C8 19.5898 8.3347 19.9527 8.76367 19.9961L8.85059 20H16.2617C16.9026 19.9999 17.4297 19.5128 17.4932 18.8887L17.5 18.7617C17.5 18.3821 17.5352 18.0036 17.6045 17.6309L17.6846 17.2607L18.4453 14.2178C18.7675 12.929 18.9505 11.6099 18.9912 10.2832L19 9.71387V7C19 6.48242 18.6065 6.05635 18.1025 6.00488L18 6C17.4477 6 17 6.44772 17 7V10.5L16.9902 10.6006C16.9437 10.8285 16.7416 10.9999 16.5 11L16.3994 10.9902C16.2039 10.9504 16.0497 10.7961 16.0098 10.6006L16 10.5V5C16 4.48242 15.6065 4.05635 15.1025 4.00488L15 4C14.4477 4 14 4.44772 14 5V10.5L13.9902 10.6006C13.9437 10.8285 13.7416 10.9999 13.5 11L13.3994 10.9902C13.2039 10.9504 13.0497 10.7961 13.0098 10.6006L13 10.5V4C13 3.48242 12.6065 3.05635 12.1025 3.00488L12 3Z" />
    </svg>
  ),
  frame: (
    <svg width={24} height={24} viewBox="0 0 24 24" fill="none">
      <path fillRule="evenodd" clipRule="evenodd" d="M4 10V4H10V5H5V10H4ZM20 10V4H14V5H19V10H20ZM20 14H19V19H14V20H20V14ZM10 20V19H5V14H4V20H10Z" fill="currentColor" />
    </svg>
  ),
  rectangle: (
    <svg width={16} height={16} viewBox="0 0 16 16" fill="none">
      <rect x={0.5} y={0.5} width={15} height={15} stroke="currentColor" />
    </svg>
  ),
  text: (
    <svg width={19} height={14} viewBox="0 0 19 14" fill="none">
      <path transform="translate(1, 0)" d="M0.618828 13.1143C0.267265 13.1143 0.0387497 12.9121 0.0387497 12.5781C0.0387497 12.4375 0.0651169 12.2969 0.117851 12.1475L3.89715 1.61816C4.07293 1.15234 4.31023 0.923828 4.74969 0.923828C5.18035 0.923828 5.42645 1.15234 5.60223 1.61816L9.37273 12.1475C9.42547 12.2969 9.46062 12.4375 9.46062 12.5781C9.46062 12.9033 9.22332 13.1143 8.87176 13.1143C8.53777 13.1143 8.34441 12.9561 8.20379 12.543L7.07 9.2207H2.42059L1.2868 12.543C1.15496 12.9561 0.952812 13.1143 0.618828 13.1143ZM2.77215 8.20996H6.71844L4.77605 2.52344H4.72332L2.77215 8.20996ZM16.9222 11.6992C16.4124 12.6133 15.3929 13.1582 14.1888 13.1582C12.3958 13.1582 11.1917 12.0244 11.1917 10.3545C11.1917 8.69336 12.387 7.67383 14.3821 7.67383H16.9398V6.66309C16.9398 5.38867 16.1751 4.7207 14.7601 4.7207C13.8987 4.7207 13.2923 5.0459 12.7562 5.75781C12.5716 5.99512 12.4046 6.06543 12.1673 6.06543C11.8773 6.06543 11.6839 5.87207 11.6839 5.56445C11.6839 5.08105 12.0706 4.55371 12.7474 4.14941C13.2747 3.83301 13.9515 3.65723 14.8304 3.65723C16.9661 3.65723 18.1527 4.71191 18.1527 6.62793V12.4023C18.1527 12.8242 17.9329 13.0791 17.5638 13.0791C17.1946 13.0791 16.9749 12.8242 16.9749 12.4023V11.6992H16.9222ZM12.4486 10.3281C12.4486 11.3828 13.2571 12.0947 14.4788 12.0947C15.8763 12.0947 16.9398 11.1279 16.9398 9.8623V8.72852H14.4085C13.1517 8.72852 12.4486 9.2998 12.4486 10.3281Z" fill="currentColor" />
    </svg>
  ),
};

const toolNames: Record<Tool, string> = {
  select: 'Move',
  pan: 'Pan',
  frame: 'Frame',
  rectangle: 'Rectangle',
  text: 'Text',
};

export function Toolbar() {
  const { activeTool, setActiveTool } = useEditorStore();

  const tools: Tool[] = ['select', 'pan'];

  return (
    <div
      style={{
        width: 40,
        background: '#1a1a1a',
        borderRight: '1px solid #333',
        display: 'flex',
        flexDirection: 'column',
        alignItems: 'center',
        paddingTop: 8,
        paddingBottom: 8,
        gap: 2,
      }}
    >
      {tools.map((tool) => (
        <button
          key={tool}
          title={toolNames[tool]}
          onClick={() => setActiveTool(tool)}
          style={{
            width: 36,
            height: 32,
            padding: 6,
            background: activeTool === tool ? '#0066ff' : 'transparent',
            border: 'none',
            borderRadius: 4,
            cursor: 'pointer',
            color: activeTool === tool ? '#fff' : '#888',
            display: 'flex',
            alignItems: 'center',
            justifyContent: 'center',
            transition: 'all 0.15s',
          }}
        >
          <div style={tool === 'rectangle' ? { width: 16, height: 16 } : tool === 'text' ? { width: 19, height: 14 } : { width: 20, height: 20 }}>{icons[tool]}</div>
        </button>
      ))}

      {/* Spacer pushes the fit button to the bottom */}
      <div style={{ flex: 1 }} />

      {/* Fit to canvas */}
      <button
        title="Fit all artboards in view"
        onClick={fitCanvas}
        style={{
          width: 36,
          height: 32,
          padding: 6,
          background: 'transparent',
          border: 'none',
          borderRadius: 4,
          cursor: 'pointer',
          color: '#666',
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          transition: 'all 0.15s',
        }}
        onMouseEnter={e => { e.currentTarget.style.color = '#aaa'; e.currentTarget.style.background = 'rgba(255,255,255,0.05)'; }}
        onMouseLeave={e => { e.currentTarget.style.color = '#666'; e.currentTarget.style.background = 'transparent'; }}
      >
        <FitIcon />
      </button>
    </div>
  );
}
