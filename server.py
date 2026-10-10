
import hashlib

from starlette.applications import Starlette
from starlette.requests import Request
from starlette.responses import JSONResponse, Response
from starlette.routing import Route

EMAIL = "24f3002050@ds.study.iitm.ac.in"


async def mcp_endpoint(request: Request):
    if request.method == "GET":
        return Response(status_code=405)

    try:
        body = await request.json()
    except Exception:
        return JSONResponse({"error": "Invalid JSON"}, status_code=400)

    method = body.get("method")
    request_id = body.get("id")
    params = body.get("params") or {}

    # MCP notifications do not require a JSON response body.
    if method == "notifications/initialized" or (
        isinstance(method, str) and method.startswith("notifications/")
    ):
        return Response(status_code=202)

    if method == "initialize":
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": request_id,
            "result": {
                "protocolVersion": params.get(
                    "protocolVersion", "2025-03-26"
                ),
                "capabilities": {"tools": {}},
                "serverInfo": {
                    "name": "exam-challenge-server",
                    "version": "1.0.0",
                },
            },
        })

    if method == "ping":
        result = {}

    elif method == "tools/list":
        result = {
            "tools": [{
                "name": "solve_challenge",
                "description": "Hash the current exam challenge.",
                "inputSchema": {
                    "type": "object",
                    "properties": {},
                },
            }]
        }

    elif method == "tools/call":
        if params.get("name") != "solve_challenge":
            return JSONResponse({
                "jsonrpc": "2.0",
                "id": request_id,
                "error": {"code": -32602, "message": "Unknown tool"},
            })

        # Read the header from THIS request, not from stored state.
        challenge = request.headers.get("x-exam-challenge", "")
        answer = hashlib.sha256(
            f"{challenge}:{EMAIL}".encode("utf-8")
        ).hexdigest()[:16]

        result = {
            "content": [{"type": "text", "text": answer}],
            "isError": False,
        }

    else:
        return JSONResponse({
            "jsonrpc": "2.0",
            "id": request_id,
            "error": {"code": -32601, "message": "Method not found"},
        })

    return JSONResponse({
        "jsonrpc": "2.0",
        "id": request_id,
        "result": result,
    })


app = Starlette(routes=[
    Route("/mcp", mcp_endpoint, methods=["POST", "GET"]),
])