#!/usr/bin/env python3
"""Serve a fixture's frozen Linear issues as a stdio MCP server.

  fake-linear.py <linear.json>

linear.json maps issue IDs to the issue as it stood when the PR was opened,
with an optional "comments" list. get_issue and list_comments read only that
file, so a run can't see what happened to the ticket after the PR.
"""

import json
import sys
from pathlib import Path

ISSUES = json.loads(Path(sys.argv[1]).read_text(encoding="utf-8"))
TOOLS = [
    {"name": "get_issue", "description": "Get a Linear issue by its identifier, such as ENG-123.",
     "inputSchema": {"type": "object", "properties": {"id": {"type": "string"}}, "required": ["id"]}},
    {"name": "list_comments", "description": "List the comments on a Linear issue.",
     "inputSchema": {"type": "object", "properties": {"issueId": {"type": "string"}}, "required": ["issueId"]}},
]


def call(name, args):
    key = str(args.get("id") or args.get("issueId") or "").upper()
    issue = ISSUES.get(key)
    if issue is None:
        return {"content": [{"type": "text", "text": f"Entity not found: Issue {key}"}], "isError": True}
    if name == "list_comments":
        body = issue.get("comments", [])
    else:
        body = {k: v for k, v in issue.items() if k != "comments"}
    return {"content": [{"type": "text", "text": json.dumps(body, indent=2)}]}


def reply(request, result=None, error=None):
    message = {"jsonrpc": "2.0", "id": request["id"]}
    message.update({"error": error} if error else {"result": result})
    sys.stdout.write(json.dumps(message) + "\n")
    sys.stdout.flush()


for line in sys.stdin:
    if not line.strip():
        continue
    request = json.loads(line)
    method = request.get("method")
    if "id" not in request:
        continue
    if method == "initialize":
        reply(request, {"protocolVersion": request["params"].get("protocolVersion", "2025-06-18"),
                        "capabilities": {"tools": {}}, "serverInfo": {"name": "linear", "version": "1"}})
    elif method == "tools/list":
        reply(request, {"tools": TOOLS})
    elif method == "tools/call":
        params = request.get("params", {})
        if params.get("name") not in ("get_issue", "list_comments"):
            reply(request, error={"code": -32602, "message": f"unknown tool: {params.get('name')}"})
        else:
            reply(request, call(params["name"], params.get("arguments") or {}))
    elif method == "ping":
        reply(request, {})
    else:
        reply(request, error={"code": -32601, "message": f"unknown method: {method}"})
