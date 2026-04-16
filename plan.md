# Paper Clone - 开发计划

## 项目概述

复刻 Paper 设计工具，做一个本地优先、可离线使用的设计软件。通过 MCP 协议让 AI Agent（如 Claude Code）可以读取和修改设计。

- **定位**：Paper 的开源本地 clone
- **核心特性**：基于 HTML/CSS 的真实画布渲染 + 标准 MCP Server
- **打包**：pywebview 打包成 macOS 应用

---

## 技术架构

```
┌─────────────────────────────────────────────────────────┐
│  Claude Code / AI Agent                                │
│  (connects via MCP: 127.0.0.1:3004/mcp)               │
└────────────┬────────────────────────────────────────────┘
             │  Streamable HTTP (MCP Protocol)
             ▼
┌─────────────────────────────────────────────────────────┐
│  Python FastAPI Backend (port 3004)                    │
│  ├── MCP Server (POST /mcp)                           │
│  └── Document Store (HTML 文件)                        │
└────────────┬────────────────────────────────────────────┘
             │  HTTP API + 轮询同步
             ▼
┌─────────────────────────────────────────────────────────┐
│  React Frontend (Vite dev server)                      │
│  ├── Canvas (position: absolute + inline styles)        │
│  ├── Toolbar (Move/Pan/Frame/Rectangle/Text)          │
│  ├── Layer Panel                                       │
│  ├── Property Panel                                   │
│  └── Page Tabs                                        │
└─────────────────────────────────────────────────────────┘
```

### 关键设计决策

- **渲染**：真实 HTML/CSS DOM，`position: absolute` + inline styles（和 Paper 完全一致）
- **文档格式**：`.html` 文件作为源格式，元数据存储在 `data-paper-*` 属性和 `<meta>` 标签
- **MCP 协议**：标准 Streamable HTTP transport，Claude Code 可直接连接
- **前端同步**：前端轮询后端每 1 秒同步文档状态
- **通信流**：MCP Tool Call → Python Handler → Frontend polling sync

---

## 功能清单

### 第一阶段（MCP + 核心渲染） ✅ 基本完成

- [x] 项目脚手架搭建（FastAPI + Vite + React + pywebview）
- [x] MCP Server 实现（19 个 tools）
- [x] 画布渲染引擎（position: absolute + inline styles）
- [x] 工具栏（Move/Pan/Frame/Rectangle/Text）
- [x] 前端轮询同步
- [ ] 文件打开/保存对话框（pywebview native dialog）
- [ ] 工具栏 SVG 图标

### 第二阶段（编辑器交互） ✅ 基本完成

- [x] 元素选中
- [x] 拖拽移动
- [x] 调整大小（resize handle — ArtboardFrame 8点缩放 + Element 4点缩放）
- [x] 画布缩放（鼠标滚轮 ⌘+ / ⌘-）
- [x] 画布平移（Pan 工具 + 空格拖拽）
- [x] 撤销/重做（Zustand history）
- [x] 右侧属性面板（颜色、字体、尺寸等）
- [x] 左侧图层面板（节点层级管理）
- [ ] 双击文本编辑
- [ ] 键盘快捷键完善（右键菜单 Copy/Paste/Duplicate 等）

### 第三阶段（完整功能）🔄 进行中

- [x] 多页面/多 Artboard 支持（canvas 同时展示所有 artboard，可拖拽/缩放，属性实时同步后端）
- [ ] 复制/粘贴
- [ ] 对齐辅助线
- [ ] 导出美化 HTML
- [ ] 工具栏 SVG 图标（复用 Paper 原图标）

### 第四阶段（打包与发布）

- [ ] pywebview 桌面打包配置
- [ ] macOS .app 打包

---

## MCP Tools 清单（19 个，全部实现）

### 文档操作
- `get_basic_info` — 获取文档信息
- `create_artboard` — 创建新页面
- `get_tree_summary` — 获取节点树摘要

### 节点查询
- `get_children` — 获取子节点
- `get_node_info` — 获取节点详细信息
- `get_selection` — 获取当前选中节点
- `get_screenshot` — 截图

### 节点创建
- `write_html` — 写入 HTML 片段创建节点
- `duplicate_nodes` — 复制节点

### 节点修改
- `update_styles` — 更新样式
- `set_text_content` — 设置文本内容
- `rename_nodes` — 重命名节点
- `finish_working_on_nodes` — 标记操作完成

### 样式导出
- `get_computed_styles` — 获取计算后样式
- `get_jsx` — 导出为 JSX 代码
- `get_font_family_info` — 获取字体信息

### 文件操作
- `save_document` — 保存文档
- `open_document` — 打开文档
- `export_html` — 导出 HTML

---

## 文件结构

```
paper_clone/
├── backend/
│   ├── main.py              # FastAPI 入口 (port 3004) + MCP Server
│   ├── document.py           # 文档存储 (HTML 文件)
│   ├── handlers/             # MCP handlers (已合并到 main.py)
│   │   └── mcp_handler.py
│   └── requirements.txt
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── canvas/
│   │   │   ├── Canvas.tsx
│   │   │   └── Element.tsx
│   │   ├── toolbar/
│   │   │   └── Toolbar.tsx
│   │   ├── panels/
│   │   │   ├── LayerPanel.tsx
│   │   │   └── PropertyPanel.tsx
│   │   ├── store/
│   │   │   └── editorStore.ts  (Zustand)
│   │   ├── bridge/
│   │   │   └── api.ts
│   │   └── types.ts
│   ├── vite.config.ts
│   └── package.json
├── desktop/
│   └── main.py              # pywebview 入口
└── plan.md
```

---

## 当前阶段任务

### 第一阶段完成情况

✅ MCP Server 在 127.0.0.1:3004/mcp 运行
✅ 前端在 http://localhost:5173 运行
✅ MCP write_html 创建元素成功
✅ 前端轮询同步元素到画布
✅ HTML 导出正常

**待完成**：
- pywebview 打包（需要 native dialog 支持）
- 文件打开/保存功能
- SVG 工具栏图标
- MCP update_artboard 工具（x/y/width/height/name/backgroundColor）

---

## 启动方式

```bash
# 后端
cd backend && python main.py

# 前端（开发模式）
cd frontend && npm run dev

# 桌面应用（打包后）
cd desktop && python main.py
```

### Claude Code MCP 配置

在 Claude Code 的 MCP 配置中添加：

```json
{
  "mcpServers": {
    "paper-clone": {
      "command": "curl",
      "args": ["-X", "POST", "-H", "Content-Type: application/json", "-d", "{\"jsonrpc\":\"2.0\",\"method\":\"initialize\",\"params\":{}}", "http://127.0.0.1:3004/mcp"]
    }
  }
}
```

或者直接使用 HTTP 方式调用 MCP 端点。
