"""
MCP Server - Standard MCP Server using Streamable HTTP
"""
import asyncio
import json
from typing import Any
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from starlette.routing import Route
from starlette.middleware import Middleware
from starlette.applications import Starlette

from handlers.mcp_handler import handle_tool_call

# MCP Server configuration
MCP_VERSION = "1.0.0"
SERVER_NAME = "paper-clone"
SERVER_VERSION = "0.1.0"

# Sessions storage
sessions = {}


# =============================================================================
# MCP Protocol Handlers
# =============================================================================

async def list_tools(request: dict) -> dict:
    """Handle list_tools request"""
    return {
        "tools": [
            {
                "name": "get_basic_info",
                "description": "Get basic document information including file name, pages, and node count",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
            {
                "name": "get_selection",
                "description": "Get currently selected nodes in the canvas",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
            {
                "name": "get_tree_summary",
                "description": "Get a compact text summary of the document tree",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "nodeId": {"type": "string"},
                        "depth": {"type": "number", "default": 3},
                    },
                },
            },
            {
                "name": "get_children",
                "description": "Get direct children of a node",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "nodeId": {"type": "string"},
                    },
                },
            },
            {
                "name": "get_node_info",
                "description": "Get detailed information about a specific node",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "nodeId": {"type": "string"},
                    },
                },
            },
            {
                "name": "get_screenshot",
                "description": "Capture a screenshot of the canvas or a specific node",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "nodeId": {"type": "string"},
                        "scale": {"type": "number", "default": 1},
                        "transparent": {"type": "boolean", "default": False},
                    },
                },
            },
            {
                "name": "write_html",
                "description": "Write HTML to create new elements in the canvas",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "html": {"type": "string"},
                        "parentId": {"type": "string"},
                    },
                    "required": ["html"],
                },
            },
            {
                "name": "duplicate_nodes",
                "description": "Duplicate existing nodes",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "nodeIds": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["nodeIds"],
                },
            },
            {
                "name": "update_styles",
                "description": "Update styles of nodes",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "nodeIds": {"type": "array", "items": {"type": "string"}},
                        "styles": {"type": "object"},
                    },
                    "required": ["nodeIds", "styles"],
                },
            },
            {
                "name": "set_text_content",
                "description": "Set text content of nodes",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "nodeIds": {"type": "array", "items": {"type": "string"}},
                        "text": {"type": "string"},
                    },
                    "required": ["nodeIds", "text"],
                },
            },
            {
                "name": "rename_nodes",
                "description": "Rename nodes",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "nodeIds": {"type": "array", "items": {"type": "string"}},
                        "names": {"type": "object"},
                    },
                    "required": ["nodeIds", "names"],
                },
            },
            {
                "name": "finish_working_on_nodes",
                "description": "Mark work as finished, used to batch operations",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            },
            {
                "name": "get_computed_styles",
                "description": "Get computed styles of nodes",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "nodeIds": {"type": "array", "items": {"type": "string"}},
                    },
                    "required": ["nodeIds"],
                },
            },
            {
                "name": "get_jsx",
                "description": "Export nodes as React JSX code",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "nodeIds": {"type": "array", "items": {"type": "string"}},
                    },
                },
            },
            {
                "name": "get_font_family_info",
                "description": "Get information about available font families",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "fontFamily": {"type": "string"},
                    },
                },
            },
            {
                "name": "create_artboard",
                "description": "Create a new artboard/page",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "name": {"type": "string"},
                        "width": {"type": "number"},
                        "height": {"type": "number"},
                    },
                },
            },
            {
                "name": "save_document",
                "description": "Save the current document to a file",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "filePath": {"type": "string"},
                    },
                },
            },
            {
                "name": "open_document",
                "description": "Open a document from an HTML file",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "filePath": {"type": "string"},
                    },
                    "required": ["filePath"],
                },
            },
            {
                "name": "export_html",
                "description": "Export the document as HTML",
                "inputSchema": {
                    "type": "object",
                    "properties": {
                        "pretty": {"type": "boolean", "default": True},
                    },
                },
            },
        ]
    }


async def initialize(request: dict) -> dict:
    """Handle initialize request"""
    return {
        "protocolVersion": "2024-11-05",
        "capabilities": {
            "tools": {},
        },
        "serverInfo": {
            "name": SERVER_NAME,
            "version": SERVER_VERSION,
        },
        "instructions": """Paper Clone - A local-first design tool that exports real HTML/CSS.
Use this tool to create, edit, and export web designs. The canvas renders real HTML elements
with position: absolute and inline styles. You can export designs as HTML code.""",
    }


async def call_tool(request: dict) -> dict:
    """Handle call_tool request"""
    name = request.get("name", "")
    arguments = request.get("arguments", {})
    doc_id = arguments.pop("_doc_id", "default")

    try:
        result = await handle_tool_call(name, arguments, doc_id)

        # Format result as MCP response
        if isinstance(result, dict):
            if "error" in result:
                return {
                    "content": [{"type": "text", "text": json.dumps(result)}],
                    "isError": True,
                }
            return {
                "content": [{"type": "text", "text": json.dumps(result)}],
            }
        return {
            "content": [{"type": "text", "text": str(result)}],
        }
    except Exception as e:
        return {
            "content": [{"type": "text", "text": f"Error: {str(e)}"}],
            "isError": True,
        }


# =============================================================================
# Request Router
# =============================================================================

async def handle_mcp_request(request_data: dict, method: str) -> dict:
    """Route MCP requests to appropriate handlers"""

    if method == "initialize":
        return await initialize(request_data)
    elif method == "tools/list":
        return await list_tools(request_data)
    elif method == "tools/call":
        return await call_tool(request_data)
    else:
        return {"error": f"Unknown method: {method}"}


# =============================================================================
# FastAPI Endpoints
# =============================================================================

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
import uvicorn

app = FastAPI(title="Paper Clone MCP Server")


@app.get("/mcp")
async def mcp_get():
    """SSE endpoint for MCP"""
    return JSONResponse(
        content={"error": "not_found", "message": "Use POST for MCP requests"},
        status_code=404,
    )


@app.post("/mcp")
async def mcp_post(request: Request):
    """Handle MCP requests"""
    try:
        data = await request.json()
    except:
        return JSONResponse(
            content={"error": "invalid_request", "message": "Invalid JSON"},
            status_code=400,
        )

    method = data.get("method", "")
    params = data.get("params", {})

    # Add doc_id from header or default
    doc_id = request.headers.get("x-paper-doc-id", "default")

    try:
        result = await handle_mcp_request(params, method)
        return JSONResponse(content={"jsonrpc": "2.0", "id": data.get("id"), "result": result})
    except Exception as e:
        return JSONResponse(
            content={
                "jsonrpc": "2.0",
                "id": data.get("id"),
                "error": {"code": -32603, "message": str(e)},
            }
        )


@app.get("/health")
async def health():
    """Health check endpoint"""
    return {"status": "ok", "server": SERVER_NAME, "version": SERVER_VERSION}


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=3004)
