The problem I ran into is that I use Paper MCP for design, but the Paper server needs an overseas network connection, which is often unstable. This design tool is based on HTML and exposes MCP so Claude Code can call it to generate HTML;

The interface is very simple: on the left there are several tool icons: mouse, hand, frame, rectangle, text, shaders (ignore that for now). Mouse and hand are used to quickly change the viewport and drag artboards around. Frame, rectangle, and text are essentially HTML elements;

What do I want to do? I want to build a Paper-like MCP-based design tool myself, with a FastAPI backend and a Vite + React frontend, then package it with pywebview so I end up with my own Paper-like UI design application;

The tools you currently have are: 1. Paper MCP, which you can inspect by communicating with the interface and learning how it works, then reverse engineer it; 2. BrowserOS MCP, which can control the browser and also take screenshots; 3. Minimax MCP, which provides web search and an image tool for understanding images. You can use BrowserOS screenshots and then call the image understanding tool to figure out what is wrong with the frontend you are building. That way you can keep writing code, running the browser, taking screenshots, finding problems, and fixing code without needing my intervention, until it is necessary for me to step in or until you have a meaningful checkpoint to report;

For project code, you can refer to this project: /Users/teli/www/work/MinimaxApp. It shows how I built things before;
The backend server should default to port 3004 to avoid conflicts with my other active projects;

Next, ask me questions one at a time instead of listing them all at once. The goal is to clarify the vague parts of my requirements. Once we have clarified enough, write a development plan.md to track project progress and goals;

-------------------------
1. The top-level layout should actually have 4 columns. Your version has 3. The toolbar should be its own column instead of floating on the far left. Also, the toolbar should reuse the original icons as much as possible. You can copy the SVG code directly.

2. The hierarchy of the first column is not specific enough. It should not be called "div element"; in Paper it is a frame or rectangle.

3. The canvas does not yet support keyboard-assisted movement. Hold Space and drag to move, use Cmd + plus to zoom in, and Cmd + - to zoom out. There is also no right-click menu yet. The current context menu should look like this:
Copy ⌘C
Copy link 
Copy as 
  - copy as png
  - copy as tailwind
  - copy as react css
Paste ⌘V
Paste on top ⇧⌘V
Paste to replace ⇧⌘R
Duplicate ⌘D
Copy styles ⌥⌘C
Paste styles ⌥⌘V
Frame selection ⇧F
Add flex layout ⇧A
Ungroup ⇧⌘G
Show / hide ⇧⌘H
Lock / unlock ⇧⌘L
Arrange
Select parent  Escape
Select children Enter

