# Paper Clone UI Reference
# Extracted from https://app.paper.design

## 1. TOOLBAR ICONS (7 tools)

### Move
```jsx
<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-linejoin="round">
  <path d="M6.5 20.2627V3.74142C6.5 3.65233 6.60771 3.60771 6.67071 3.67071L18.3293 15.3293C18.3923 15.3923 18.3477 15.5 18.2586 15.5H11.8285C11.698 15.5 11.5727 15.551 11.4793 15.6421L6.66983 20.3343C6.60649 20.3961 6.5 20.3512 6.5 20.2627Z"/>
</svg>
```

### Pan
```jsx
<svg width="24" height="24" viewBox="0 0 24 24" fill="currentcolor">
  <path d="M12 2C12.8725 2.00013 13.6126 2.55965 13.8857 3.33887C14.2041 3.12494 14.5876 3 15 3C16.1044 3.00016 17 3.89553 17 5V5.26953C17.2943 5.09913 17.6355 5 18 5C19.1044 5.00016 20 5.89553 20 7V9.71387C20 11.3138 19.804 12.9078 19.416 14.46L18.6553 17.5029C18.5524 17.9145 18.5 18.3375 18.5 18.7617C18.5 19.9976 17.4976 20.9999 16.2617 21H8.85059C7.82862 21 7 20.1714 7 19.1494C6.99998 18.6456 6.88284 18.1495 6.65918 17.7002L6.55664 17.5107L4.85449 14.5918C3.9102 12.9729 4.109 10.9309 5.34766 9.52441L5.95117 8.83887L7 7.62695V5C7 3.89543 7.89543 3 9 3C9.41211 3.00006 9.79506 3.12517 10.1133 3.33887C10.3864 2.55946 11.1273 2 12 2ZM12 3C11.4477 3 11 3.44772 11 4V10.5L10.9902 10.6006C10.9437 10.8285 10.7416 10.9999 10.5 11L10.3994 10.9902C10.2039 10.9504 10.0497 10.7961 10.0098 10.6006L10 10.5V5C10 4.48242 9.60653 4.05635 9.10254 4.00488L9 4C8.44772 4 8 4.44772 8 5V12C8 12.2761 7.77603 12.4999 7.5 12.5C7.22386 12.5 7 12.2761 7 12V9.15527L6.70215 9.5L6.09766 10.1855L5.92871 10.3945C5.12852 11.4643 5.03614 12.9191 5.71777 14.0879L7.4209 17.0068C7.80017 17.6571 7.99997 18.3966 8 19.1494C8 19.5898 8.3347 19.9527 8.76367 19.9961L8.85059 20H16.2617C16.9026 19.9999 17.4297 19.5128 17.4932 18.8887L17.5 18.7617C17.5 18.3821 17.5352 18.0036 17.6045 17.6309L17.6846 17.2607L18.4453 14.2178C18.7675 12.929 18.9505 11.6099 18.9912 10.2832L19 9.71387V7C19 6.48242 18.6065 6.05635 18.1025 6.00488L18 6C17.4477 6 17 6.44772 17 7V10.5L16.9902 10.6006C16.9437 10.8285 16.7416 10.9999 16.5 11L16.3994 10.9902C16.2039 10.9504 16.0497 10.7961 16.0098 10.6006L16 10.5V5C16 4.48242 15.6065 4.05635 15.1025 4.00488L15 4C14.4477 4 14 4.44772 14 5V10.5L13.9902 10.6006C13.9437 10.8285 13.7416 10.9999 13.5 11L13.3994 10.9902C13.2039 10.9504 13.0497 10.7961 13.0098 10.6006L13 10.5V4C13 3.48242 12.6065 3.05635 12.1025 3.00488L12 3Z"/>
</svg>
```

### Frame
```jsx
<svg width="24" height="24" viewBox="0 0 24 24" fill="none">
  <path fill-rule="evenodd" clip-rule="evenodd" d="M4 10V4H10V5H5V10H4ZM20 10V4H14V5H19V10H20ZM20 14H19V19H14V20H20V14ZM10 20V19H5V14H4V20H10Z" fill="currentcolor"/>
</svg>
```

### Rectangle
```jsx
<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
  <rect x="0.5" y="0.5" width="15" height="15" stroke="currentcolor"/>
</svg>
```

### Text
```jsx
<svg width="19" height="14" viewBox="0 0 19 14" fill="none">
  <path transform="translate(1, 0)" d="M0.618828 13.1143C0.267265 13.1143 0.0387497 12.9121 0.0387497 12.5781C0.0387497 12.4375 0.0651169 12.2969 0.117851 12.1475L3.89715 1.61816C4.07293 1.15234 4.31023 0.923828 4.74969 0.923828C5.18035 0.923828 5.42645 1.15234 5.60223 1.61816L9.37273 12.1475C9.42547 12.2969 9.46062 12.4375 9.46062 12.5781C9.46062 12.9033 9.22332 13.1143 8.87176 13.1143C8.53777 13.1143 8.34441 12.9561 8.20379 12.543L7.07 9.2207H2.42059L1.2868 12.543C1.15496 12.9561 0.952812 13.1143 0.618828 13.1143ZM2.77215 8.20996H6.71844L4.77605 2.52344H4.72332L2.77215 8.20996ZM16.9222 11.6992C16.4124 12.6133 15.3929 13.1582 14.1888 13.1582C12.3958 13.1582 11.1917 12.0244 11.1917 10.3545C11.1917 8.69336 12.387 7.67383 14.3821 7.67383H16.9398V6.66309C16.9398 5.38867 16.1751 4.7207 14.7601 4.7207C13.8987 4.7207 13.2923 5.0459 12.7562 5.75781C12.5716 5.99512 12.4046 6.06543 12.1673 6.06543C11.8773 6.06543 11.6839 5.87207 11.6839 5.56445C11.6839 5.08105 12.0706 4.55371 12.7474 4.14941C13.2747 3.83301 13.9515 3.65723 14.8304 3.65723C16.9661 3.65723 18.1527 4.71191 18.1527 6.62793V12.4023C18.1527 12.8242 17.9329 13.0791 17.5638 13.0791C17.1946 13.0791 16.9749 12.8242 16.9749 12.4023V11.6992H16.9222ZM12.4486 10.3281C12.4486 11.3828 13.2571 12.0947 14.4788 12.0947C15.8763 12.0947 16.9398 11.1279 16.9398 9.8623V8.72852H14.4085C13.1517 8.72852 12.4486 9.2998 12.4486 10.3281Z" fill="currentColor"/>
</svg>
```

### Shaders
```jsx
<svg width="24" height="24" viewBox="0 0 24 24" fill="none" stroke="currentcolor">
  <g transform="translate(1, 0)">
    <path d="M11.025 2.99819C11.3233 2.83556 11.6839 2.83556 11.9822 2.9982L19.4785 7.0844C19.7999 7.25959 19.9999 7.59638 19.9999 7.96243V16.0374C19.9999 16.4034 19.7999 16.7402 19.4785 16.9154L11.9822 21.0016C11.6839 21.1643 11.3233 21.1643 11.025 21.0016L3.52871 16.9154C3.20732 16.7402 3.00732 16.4034 3.00732 16.0374V7.96243C3.00732 7.59638 3.20732 7.25959 3.52871 7.0844L11.025 2.99819Z"/>
    <path d="M11.5034 20.7406V14.7234"/>
    <path d="M8.92457 10.9126L3.47803 7.76807"/>
    <path d="M14.0847 10.9126L19.5312 7.76807"/>
    <circle cx="11.5" cy="12.0" r="2.7"/>
  </g>
</svg>
```

### Image Generation
```jsx
<svg width="17" height="18" viewBox="0 0 17 18" fill="none">
  <path d="M3.01269 10.8234C3.18378 10.3934 3.81622 10.3935 3.9873 10.8234L4.0166 10.922L4.07422 11.1613C4.40717 12.3359 5.36961 13.2373 6.5791 13.4845L6.67773 13.5138C7.10763 13.6849 7.10764 14.3173 6.67773 14.4884L6.5791 14.5177C5.36957 14.765 4.40709 15.6662 4.07422 16.8409L4.0166 17.0802C3.90849 17.6061 3.1961 17.6391 3.01269 17.1788L2.9834 17.0802C2.73616 15.8706 1.83499 14.9082 0.660156 14.5753L0.420898 14.5177C-0.140352 14.4026 -0.140247 13.5997 0.420898 13.4845L0.660156 13.4269C1.83488 13.094 2.73606 12.1314 2.9834 10.922L3.01269 10.8234ZM3.22461 0.582159C3.41861 0.454046 3.68265 0.475933 3.85351 0.646612L16.8535 13.6466C17.0488 13.8419 17.0488 14.1584 16.8535 14.3536L13.8535 17.3536C13.6582 17.5488 13.3417 17.5489 13.1465 17.3536L0.146484 4.35364C-0.0485467 4.1584 -0.0486205 3.84181 0.146484 3.64661L3.14648 0.646612L3.22461 0.582159ZM4.20703 7.00013L13.5 16.2931L15.793 14.0001L6.5 4.70716L4.20703 7.00013ZM3.5 12.3624C3.11463 13.0484 2.54735 13.6158 1.86133 14.0011C2.54717 14.3863 3.11465 14.953 3.5 15.6388C3.88518 14.9533 4.45225 14.3863 5.13769 14.0011C4.45198 13.6158 3.88523 13.0482 3.5 12.3624ZM1.20703 4.00013L3.5 6.2931L5.79297 4.00013L3.5 1.70716L1.20703 4.00013ZM11.0215 0.817511C11.1895 0.394667 11.8103 0.39479 11.9785 0.817511L12.0078 0.914191L12.043 1.06165C12.248 1.78514 12.8411 2.33996 13.5859 2.49232L13.6826 2.52161C14.1057 2.68964 14.1057 3.31062 13.6826 3.47864L13.5859 3.50794C12.8411 3.66026 12.2481 4.21517 12.043 4.9386L12.0078 5.08607C11.9019 5.60383 11.2015 5.63595 11.0215 5.18275L10.9922 5.08607C10.8398 4.34118 10.285 3.74816 9.56152 3.5431L9.41406 3.50794C8.8622 3.39483 8.86216 2.60535 9.41406 2.49232L9.56152 2.45716C10.2851 2.25207 10.8399 1.65921 10.9922 0.914191L11.0215 0.817511ZM11.5 2.22083C11.29 2.52622 11.0261 2.79017 10.7207 3.00013C11.0258 3.20987 11.2901 3.47346 11.5 3.77845C11.7097 3.4736 11.9735 3.20984 12.2783 3.00013C11.9733 2.79028 11.7097 2.5259 11.5 2.22083Z" fill="currentcolor"/>
</svg>
```

---

## 2. LAYER PANEL STRUCTURE

### Layer item structure (tree-item)
```
.tree-item
├── .collapsible-indicator (if has children)
├── .flex.shrink-0 (icon, 48px height, 48px width)
│   └── <svg> (type-specific icon)
└── .ml-8.flex.grow.items-center.self-stretch (name label)
```

### Layer item icons by type:

**Page/Artboard icon:**
```jsx
<svg width="16" height="16" viewBox="0 0 16 16" fill="none">
  <path d="M12.5 5.5L9.5 2.5H4.5C3.948 2.5 3.5 2.948 3.5 3.5V12.5C3.5 13.052 3.948 13.5 4.5 13.5H11.5C12.052 13.5 12.5 13.052 12.5 12.5V5.5Z" fill="currentcolor" fill-opacity="0.125"/>
  <path d="M12.5 5.5L9.5 2.5M12.5 5.5V12.5C12.5 13.052 12.052 13.5 11.5 13.5H4.5C3.948 13.5 3.5 13.052 3.5 12.5V3.5C3.5 2.948 3.948 2.5 4.5 2.5H9.5M12.5 5.5H9.5V2.5" stroke="currentcolor"/>
</svg>
```

**Frame icon:**
```jsx
<svg width="16" height="16" viewBox="0 0 16 16" fill="currentcolor">
  <rect x="2" y="3" width="5" height="10.5" rx="1" fill-opacity="0.125"/>
  <rect x="2.5" y="3.5" width="4" height="9.5" rx="0.5" fill="none" stroke="currentcolor"/>
  <rect x="8.5" y="3" width="5" height="10.5" rx="1" fill-opacity="0.125"/>
  <rect x="9" y="3.5" width="4" height="9.5" rx="0.5" fill="none" stroke="currentcolor"/>
</svg>
```

**Rectangle/Card icon:**
```jsx
<svg width="16" height="16" viewBox="0 0 16 16" fill="currentcolor">
  <rect x="2" y="2.5" width="12" height="4.5" rx="1" fill="currentcolor" fill-opacity="0.1"/>
  <rect x="2.5" y="3" width="11" height="3.5" rx="0.5" fill="none" stroke="currentcolor"/>
  <rect x="2" y="8.5" width="12" height="4.5" rx="1" fill="currentcolor" fill-opacity="0.1"/>
  <rect x="2.5" y="9" width="11" height="3.5" rx="0.5" fill="none" stroke="currentcolor"/>
</svg>
```

**Text icon:**
```jsx
<svg width="16" height="16" viewBox="0 0 16 16" fill="currentcolor">
  <!-- T letter shape -->
</svg>
```

### Layer panel CSS:
- Width: 240px (left panel)
- Background: #1a1a1a
- Border-right: 1px solid #333
- Tree item height: 48px
- Tree item padding: 0 12px
- Selected item: background #0066ff, color #fff
- Collapsed chevron: 10x10 SVG arrow

---

## 3. PROPERTY PANEL (Inspector)

### Panel structure:
```
.editor-property-panel (width: 280px)
└── .panel-root (repeated)
    ├── .panel-header
    │   ├── .panel-header-label (section title)
    │   └── .panel-header-actions (action buttons)
    └── .panel-content
        └── .panel-row (repeated)
            └── field-root / button / checkbox
```

### Sections:

**1. Document header**
- Label: "Document"
- Actions: Zoom % button, Avatar buttons (collaborators)
- Content: "Copy link ⌘ L" button

**2. Layout section**
- Header: "Layout" (collapsible)
- Actions: Pin/unpin, distribute icons
- Content:
  - Row: X | Y | Rotation (°) inputs
  - Row: W (Fill) | H (Fill) | aspect lock/flip
  - Row: "Add flex ⇧ A" button
  - Checkboxes: "Absolute position", "Clip content ⌥ C"

**3. Radius section**
- Header: "Radius" + corner radius toggle
- Content: Slider + number input

**4. Blending section**
- Header: "Blending" + mode toggle
- Content: Opacity % | Blend mode dropdown

**5. Fill section** (dimmed if no fill)
- Header: "Fill" + toggle
- Content: Color picker + opacity

**6. Outline section** (dimmed)
**7. Border section** (dimmed)
**8. Shadow section** (dimmed)
**9. Inner shadow section** (dimmed)
**10. Filters section** (dimmed)

**11. Selection colors section**
- Header: "Selection colors"
- Content: List of color swatches with usage count

**12. Guides section** (dimmed)
**13. Video section** (dimmed)
**14. Export section** (dimmed)

### Field/input styles:
```css
/* field-root */
.field-root {
  display: flex;
  align-items: center;
  gap: 6px;
}

/* field-icon */
.field-icon {
  color: #666;
  font-size: 10px;
  width: 14px;
  flex-shrink: 0;
}

/* field-control */
.field-control {
  flex: 1;
  padding: 6px 8px;
  background: #2a2a2a;
  border: 1px solid #333;
  border-radius: 4px;
  color: #fff;
  font-size: 12px;
  outline: none;
}

/* number input with scrub area */
.field-scrub-area {
  width: 8px;
  cursor: ew-resize;
}
```

### Panel CSS:
```css
.panel-root {
  border-bottom: 1px solid #333;
}

.panel-header {
  display: flex;
  align-items: center;
  justify-content: space-between;
  padding: 12px 16px 8px;
}

.panel-header-label {
  font-size: 11px;
  font-weight: 600;
  color: #888;
  text-transform: uppercase;
  letter-spacing: 0.5px;
}

.panel-content {
  padding: 0 16px 16px;
}

.panel-row {
  margin-bottom: 8px;
}
```

---

## 4. KEY STYLES TO MATCH

### Color palette:
- Background dark: #1a1a1a
- Background panel: #1a1a1a
- Background canvas: #2a2a2a
- Border: #333
- Text primary: #fff
- Text secondary: #888
- Text muted: #666
- Accent blue: #0066ff
- Canvas grid: rgba(255,255,255,0.03)

### Spacing system:
- Panel header padding: 12px 16px
- Section content padding: 16px
- Field gap: 8px
- Border radius small: 4px
- Border radius medium: 8px

### Typography:
- Font: system-ui, -apple-system, sans-serif
- Panel label: 11px, uppercase, weight 600, color #888
- Input text: 12px, color #fff
- Layer name: 12px, color #aaa
