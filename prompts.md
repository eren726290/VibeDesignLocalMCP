我的遇到的问题，我在使用paper mcp来进行设计，但是这个paper的Server需要链接国外网络经常不稳定，这个设计软件是基于HTML，提供mcp然后让Claude code可以调用mcp去生成HTML;

它的界面也非常简单，就是左边有几个TOOL icon：mouse,hand,frame, rectangle, text, sharders(这个先不管) mouse和hand是用来在界面上快速改变viewport和拖拽artbaord位置的，frame,reactangle, text本质就是HTML元素;

我想要做什么？ 我想要自己造一个paper这样的基于MCP的设计工具，后端用fastapi, 前端用vite + react实现，最后再用pywebview打包, 最后我就能够有一个自己的paper这样的UI设计软件了；

当前你有什么工具：1. paper mcp你可以通过和这个接口通信和交互了解他是怎么Work的，就能逆向工程；2.browseros的MCP，它可以用来控制浏览器，你还可以通过它的截图工具来截图，3.minimax MCP它提供了web搜索和image tool来解析图片内容，你通过browseros截图然后调用图片理解，就可以知道你开发的前端页面有什么问题，这样你就可以在不需要我人工介入的情况下，持续编写代码-》浏览器运行-》截图查看——》找到问题-》修改代码，这样持续循环的跑，直到必须要我介入或者得到阶段性成果时才停下来等待指令；

关于项目代码，你可以参考我的这个项目：/Users/teli/www/work/MinimaxApp 里面是之前我怎么用开发的；
后端Server端口建议默认用3004，防止我我的其他开发中的项目冲突；

好了接下来，你来问我问题，一个一个来不要一次性全部列出来，目的是澄清我的需求模糊的地方，我们交流完成的差不多了，你写下开发plan.md 用于追踪项目进度和目标；

-------------------------
1.整体最顶层的layout其实是4个column, 而你是3个column，tool bar是一个column而你是悬浮在最左边的，其二，的toolbar应尽量复用它的原来的图标，你直接复制它的svg代码不就好了？

2.第一个column的层级关系你也写的不够，不应该叫div element而paper是frame或者rectangle，

3.现在canvas还不能用快捷键移动，按住空格，拖拽来移动，cmd + plus来放大，cmd + - 来缩小；还没有鼠标右键功能，目前它的鼠标右键的菜单是这样的：
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
Show / hide ⇧⌘
HLock / unlock ⇧⌘L
ArrangeSelect parent  Escape
Select children Enter

