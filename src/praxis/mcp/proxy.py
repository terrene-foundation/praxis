# Copyright 2026 Terrene Foundation
# Licensed under the Apache License, Version 2.0
"""
MCP proxy that mediates AI tool calls through the Praxis trust layer.

This proxy implements the "trust as medium" architecture:
1. Acts as an MCP server (what the AI connects to via stdio)
2. Connects to downstream MCP tool servers as a client
3. Intercepts every tool call from the AI
4. Evaluates constraints before forwarding or rejecting
5. Captures deliberation records and audit anchors for every call

Tool name namespacing: downstream server "server1" with tool "read_file"
becomes "server1__read_file" for the AI. The proxy splits on "__" to route.
"""

from __future__ import annotations

import asyncio
import json
import logging
import sys
from contextlib import AsyncExitStack
from dataclasses import dataclass, field
from typing import Any

from praxis.core.constraint import (
    ConstraintEnforcer,
    ConstraintVerdict,
    GradientLevel,
    HeldActionManager,
)

logger = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Tool name -> constraint dimension mapping
# ---------------------------------------------------------------------------

# Patterns used to classify tool names into constraint dimensions.
# Each pattern list is checked with substring matching against the tool name.
# ORDER MATTERS: operational is checked first because destructive actions
# (delete, deploy, exec) must be caught before the broader data_access
# patterns (which match "file" in "delete_file").
TOOL_DIMENSION_MAP: list[tuple[str, list[str]]] = [
    (
        "operational",
        [
            "exec",
            "shell",
            "bash",
            "run",
            "command",
            "terminal",
            "deploy",
            "install",
            "delete",
            "remove",
        ],
    ),
    (
        "data_access",
        [
            "read_file",
            "write_file",
            "read",
            "write",
            "edit",
            "list_dir",
            "search",
            "glob",
            "file",
            "directory",
            "path",
            "fs",
        ],
    ),
    (
        "communication",
        [
            "http",
            "fetch",
            "api",
            "request",
            "url",
            "web",
            "email",
            "send",
            "post",
            "get",
            "put",
            "patch",
        ],
    ),
    (
        "financial",
        [
            "token",
            "cost",
            "billing",
            "credit",
            "spend",
            "budget",
        ],
    ),
]


def classify_tool_dimension(tool_name: str) -> str:
    """Map a tool name to its primary constraint dimension.

    Uses substring matching against known tool name patterns. Returns the
    first matching dimension, or "operational" as the default.

    The dimension list is ordered so that operational (destructive) patterns
    are checked before the broader data_access patterns.

    Args:
        tool_name: The tool name (without server prefix).

    Returns:
        One of the five constraint dimension names.
    """
    lower = tool_name.lower()
    for dimension, patterns in TOOL_DIMENSION_MAP:
        for pattern in patterns:
            if pattern in lower:
                return dimension
    # Default: operational constraints cover general tool usage
    return "operational"


def _action_for_dimension(dimension: str, tool_name: str) -> str:
    """Derive the action string used for constraint evaluation.

    Maps the tool's dimension to an action that ConstraintEnforcer
    understands (e.g., "read", "write", "execute").

    Args:
        dimension: The constraint dimension.
        tool_name: The original tool name for fine-grained classification.

    Returns:
        Action string for constraint evaluation.
    """
    lower = tool_name.lower()

    if dimension == "data_access":
        if any(p in lower for p in ("write", "edit", "create", "save")):
            return "write"
        return "read"

    if dimension == "operational":
        if any(p in lower for p in ("delete", "remove")):
            return "delete"
        if any(p in lower for p in ("deploy",)):
            return "deploy"
        return "execute"

    if dimension == "communication":
        return "execute"

    if dimension == "financial":
        return "execute"

    return "execute"


def _resource_for_call(dimension: str, tool_name: str, arguments: dict) -> str | None:
    """Extract a resource identifier from tool call arguments.

    For data_access tools, looks for file path arguments.
    For communication tools, looks for URL/channel arguments.

    Args:
        dimension: The constraint dimension.
        tool_name: The tool name.
        arguments: The tool call arguments dict.

    Returns:
        Resource string, or None if no resource can be extracted.
    """
    if dimension == "data_access":
        # Common file path argument names
        for key in ("path", "file_path", "filename", "file", "uri"):
            if key in arguments:
                val = str(arguments[key])
                if val:
                    return val
        return None

    if dimension == "communication":
        for key in ("url", "uri", "endpoint", "channel"):
            if key in arguments:
                return str(arguments[key])
        return None

    return None


# ---------------------------------------------------------------------------
# Downstream server descriptor
# ---------------------------------------------------------------------------


@dataclass
class DownstreamServer:
    """Configuration for a downstream MCP tool server.

    Attributes:
        name: Short name used for tool namespacing (e.g., "filesystem").
        command: The command to launch the server process.
        args: Arguments passed to the command.
        env: Optional environment variables for the server process.
    """

    name: str
    command: str
    args: list[str] = field(default_factory=list)
    env: dict[str, str] | None = None


# ---------------------------------------------------------------------------
# ProxyResult — what the proxy returns for each tool call
# ---------------------------------------------------------------------------


@dataclass
class ProxyResult:
    """Result of a proxied tool call.

    Attributes:
        tool_name: The full namespaced tool name.
        server_name: Which downstream server handled this.
        original_tool: The tool name on the downstream server.
        verdict: The constraint verdict applied.
        held_action_id: If the action was held, the held action ID.
        forwarded: Whether the call was forwarded to the downstream server.
        response: The response from the downstream server (if forwarded).
        error: Error message (if the call was blocked or failed).
        audit_anchor_id: The audit anchor ID for this call.
    """

    tool_name: str
    server_name: str
    original_tool: str
    verdict: ConstraintVerdict
    held_action_id: str | None = None
    forwarded: bool = False
    response: Any = None
    error: str | None = None
    audit_anchor_id: str | None = None


# ---------------------------------------------------------------------------
# PraxisProxy
# ---------------------------------------------------------------------------


class PraxisProxy:
    """MCP proxy that mediates AI tool calls through the trust layer.

    Sits between an AI assistant (connected via stdio) and downstream MCP
    tool servers. Every tool call is intercepted, evaluated against the
    session's constraint envelope, and either forwarded, held, or blocked.

    Args:
        session_id: Active Praxis session for constraint evaluation.
        downstream_servers: List of downstream server configs. Each is a dict
            with keys: name, command, args (optional), env (optional).
        constraint_enforcer: Pre-configured ConstraintEnforcer. If None,
            one will be created from the session's constraint envelope.
        held_action_manager: Pre-configured HeldActionManager. If None,
            one will be created with in-memory storage.
        audit_chain: Pre-configured AuditChain. If None, audit anchors
            are tracked in memory only.
        deliberation_engine: Pre-configured DeliberationEngine. If None,
            deliberation records are not captured.
        key_manager: KeyManager for signing audit anchors. If None,
            audit anchors are not cryptographically signed.
        key_id: Signing key identifier.
    """

    def __init__(
        self,
        session_id: str,
        downstream_servers: list[dict],
        constraint_enforcer: ConstraintEnforcer | None = None,
        held_action_manager: HeldActionManager | None = None,
        audit_chain: Any | None = None,
        deliberation_engine: Any | None = None,
        key_manager: Any | None = None,
        key_id: str = "default",
    ) -> None:
        self.session_id = session_id
        self.key_manager = key_manager
        self.key_id = key_id

        # Parse downstream server configs
        self.downstream: list[DownstreamServer] = []
        for srv in downstream_servers:
            self.downstream.append(
                DownstreamServer(
                    name=srv["name"],
                    command=srv["command"],
                    args=srv.get("args", []),
                    env=srv.get("env"),
                )
            )

        # Core services
        self.enforcer = constraint_enforcer
        self.held_manager = held_action_manager or HeldActionManager(use_db=False)
        self.audit_chain = audit_chain
        self.deliberation_engine = deliberation_engine

        # Per-server client sessions (populated during start())
        self._client_sessions: dict[str, Any] = {}
        # Merged tool catalog: namespaced_name -> (server_name, original_tool, tool_schema)
        self._tool_catalog: dict[str, tuple[str, str, dict]] = {}
        # Exit stack for managing async context managers
        self._exit_stack: AsyncExitStack | None = None

    def _resolve_enforcer(self) -> ConstraintEnforcer | None:
        """Lazy-resolve the constraint enforcer from the session if not provided."""
        if self.enforcer is not None:
            return self.enforcer

        try:
            from praxis.core.session import SessionManager

            mgr = SessionManager()
            session = mgr.get_session(self.session_id)
            self.enforcer = ConstraintEnforcer(
                session["constraint_envelope"],
                session_id=self.session_id,
            )
            return self.enforcer
        except Exception as exc:
            logger.warning(
                "Could not resolve constraint enforcer for session %s: %s",
                self.session_id,
                exc,
            )
            return None

    # ------------------------------------------------------------------
    # Tool catalog management
    # ------------------------------------------------------------------

    def register_tools(self, server_name: str, tools: list[dict]) -> None:
        """Register tools from a downstream server into the merged catalog.

        Each tool is namespaced as ``server_name__tool_name``.

        Args:
            server_name: The downstream server name.
            tools: List of tool schema dicts (MCP Tool format).
        """
        for tool in tools:
            original_name = tool.get("name", "")
            if not original_name:
                continue
            namespaced = f"{server_name}__{original_name}"
            self._tool_catalog[namespaced] = (server_name, original_name, tool)
            logger.debug("Registered tool: %s -> %s/%s", namespaced, server_name, original_name)

    def get_tools(self) -> list[dict]:
        """Return the merged tool catalog as MCP-compatible tool dicts.

        Returns:
            List of tool schema dicts with namespaced names.
        """
        tools = []
        for namespaced, (server_name, original_name, schema) in self._tool_catalog.items():
            tool = dict(schema)
            tool["name"] = namespaced
            # Prefix the description with the server name for clarity
            desc = tool.get("description", "")
            tool["description"] = f"[{server_name}] {desc}" if desc else f"[{server_name}]"
            tools.append(tool)
        return tools

    def _parse_tool_name(self, namespaced_name: str) -> tuple[str, str]:
        """Split a namespaced tool name into (server_name, original_tool_name).

        Args:
            namespaced_name: The full tool name (e.g., "server1__read_file").

        Returns:
            Tuple of (server_name, original_tool_name).

        Raises:
            ValueError: If the tool name is not in the catalog.
        """
        if namespaced_name in self._tool_catalog:
            server_name, original_name, _ = self._tool_catalog[namespaced_name]
            return server_name, original_name

        # Fallback: try splitting on "__"
        if "__" in namespaced_name:
            parts = namespaced_name.split("__", 1)
            return parts[0], parts[1]

        raise ValueError(
            f"Unknown tool '{namespaced_name}'. "
            f"Available tools: {sorted(self._tool_catalog.keys())}"
        )

    # ------------------------------------------------------------------
    # Core interception logic (M04-02)
    # ------------------------------------------------------------------

    async def handle_tool_call(
        self,
        tool_name: str,
        arguments: dict,
    ) -> ProxyResult:
        """Intercept a tool call, evaluate constraints, forward or reject.

        This is the core of the "trust as medium" architecture. Every tool
        call from the AI flows through this method before reaching any
        downstream server.

        Steps:
            1. Parse the namespaced tool name
            2. Classify the tool into a constraint dimension
            3. Evaluate against the session's constraint envelope
            4. BLOCKED -> return error immediately, don't forward
            5. HELD -> queue the action, return held_action_id
            6. FLAGGED -> forward but include warning
            7. AUTO_APPROVED -> forward silently
            8. Capture audit anchor and deliberation record

        Args:
            tool_name: The namespaced tool name (e.g., "server1__read_file").
            arguments: The tool call arguments dict.

        Returns:
            ProxyResult with the verdict and response (if forwarded).
        """
        # Step 1: Parse tool name
        try:
            server_name, original_tool = self._parse_tool_name(tool_name)
        except ValueError as exc:
            verdict = ConstraintVerdict(
                level=GradientLevel.BLOCKED,
                dimension="operational",
                utilization=1.0,
                reason=str(exc),
                action="execute",
                resource=None,
            )
            return ProxyResult(
                tool_name=tool_name,
                server_name="unknown",
                original_tool=tool_name,
                verdict=verdict,
                error=str(exc),
            )

        # Step 2: Classify tool -> dimension
        dimension = classify_tool_dimension(original_tool)
        action = _action_for_dimension(dimension, original_tool)
        resource = _resource_for_call(dimension, original_tool, arguments)

        # Step 3: Evaluate constraints
        enforcer = self._resolve_enforcer()
        if enforcer is not None:
            verdict = enforcer.evaluate(
                action=action,
                resource=resource,
                context=arguments if dimension == "financial" else None,
            )
        else:
            # No enforcer available — default to auto_approved with warning
            verdict = ConstraintVerdict(
                level=GradientLevel.AUTO_APPROVED,
                dimension=dimension,
                utilization=0.0,
                reason="No constraint enforcer available — defaulting to auto_approved",
                action=action,
                resource=resource,
            )

        # Step 4-7: Act on verdict
        result = ProxyResult(
            tool_name=tool_name,
            server_name=server_name,
            original_tool=original_tool,
            verdict=verdict,
        )

        if verdict.level == GradientLevel.BLOCKED:
            result.error = f"BLOCKED by {verdict.dimension} constraint: {verdict.reason}"
            logger.info(
                "Proxy BLOCKED %s: %s (dimension=%s)",
                tool_name,
                verdict.reason,
                verdict.dimension,
            )

        elif verdict.level == GradientLevel.HELD:
            held = self.held_manager.hold(
                session_id=self.session_id,
                action=action,
                resource=resource,
                verdict=verdict,
            )
            result.held_action_id = held.held_id
            result.error = (
                f"HELD for human approval (id: {held.held_id}). "
                f"Dimension: {verdict.dimension}, reason: {verdict.reason}"
            )
            logger.info(
                "Proxy HELD %s: held_id=%s (dimension=%s)",
                tool_name,
                held.held_id,
                verdict.dimension,
            )

        elif verdict.level == GradientLevel.FLAGGED:
            # Forward but log warning
            logger.warning(
                "Proxy FLAGGED %s: %s (dimension=%s, utilization=%.0f%%)",
                tool_name,
                verdict.reason,
                verdict.dimension,
                verdict.utilization * 100,
            )
            response = await self._forward_to_downstream(server_name, original_tool, arguments)
            result.forwarded = True
            result.response = response

        else:
            # AUTO_APPROVED — forward silently
            response = await self._forward_to_downstream(server_name, original_tool, arguments)
            result.forwarded = True
            result.response = response

        # Step 8: Capture audit anchor and deliberation (M04-03)
        result.audit_anchor_id = self._capture_audit(
            tool_name=tool_name,
            action=action,
            resource=resource,
            verdict=verdict,
            held_action_id=result.held_action_id,
        )

        self._capture_deliberation(
            tool_name=tool_name,
            action=action,
            resource=resource,
            verdict=verdict,
            arguments=arguments,
        )

        return result

    async def _forward_to_downstream(
        self,
        server_name: str,
        tool_name: str,
        arguments: dict,
    ) -> Any:
        """Forward a tool call to the appropriate downstream MCP server.

        Args:
            server_name: The downstream server name.
            tool_name: The original (un-namespaced) tool name.
            arguments: The tool call arguments.

        Returns:
            The response from the downstream server, or an error dict.
        """
        session = self._client_sessions.get(server_name)
        if session is None:
            logger.warning(
                "No active client session for downstream server '%s'",
                server_name,
            )
            return {"error": f"Downstream server '{server_name}' is not connected"}

        try:
            result = await session.call_tool(tool_name, arguments)
            # Extract text content from MCP CallToolResult
            if hasattr(result, "content") and result.content:
                texts = []
                for block in result.content:
                    if hasattr(block, "text"):
                        texts.append(block.text)
                if texts:
                    return {"content": texts}
            return {"content": str(result)}
        except Exception as exc:
            logger.error(
                "Error forwarding %s to %s: %s",
                tool_name,
                server_name,
                exc,
            )
            return {"error": f"Downstream error: {exc}"}

    # ------------------------------------------------------------------
    # M04-03: Auto-capture deliberation and audit
    # ------------------------------------------------------------------

    def _capture_audit(
        self,
        tool_name: str,
        action: str,
        resource: str | None,
        verdict: ConstraintVerdict,
        held_action_id: str | None,
    ) -> str | None:
        """Create an audit anchor for this tool call.

        Args:
            tool_name: Namespaced tool name.
            action: The classified action.
            resource: The classified resource.
            verdict: The constraint verdict.
            held_action_id: If held, the held action ID.

        Returns:
            The audit anchor ID, or None if audit chain not available.
        """
        if self.audit_chain is None:
            return None

        try:
            extra_payload = {
                "tool_name": tool_name,
                "dimension": verdict.dimension,
                "utilization": verdict.utilization,
            }
            if held_action_id:
                extra_payload["held_action_id"] = held_action_id

            anchor = self.audit_chain.append(
                action=action,
                actor="ai",
                result=verdict.level.value,
                resource=resource,
                extra_payload=extra_payload,
            )
            return anchor.anchor_id
        except Exception as exc:
            logger.warning("Failed to capture audit anchor: %s", exc)
            return None

    def _capture_deliberation(
        self,
        tool_name: str,
        action: str,
        resource: str | None,
        verdict: ConstraintVerdict,
        arguments: dict,
    ) -> None:
        """Record a deliberation observation for this tool call.

        Observations are captured for every tool call that flows through
        the proxy, creating a rich deliberation trail of AI actions.

        Args:
            tool_name: Namespaced tool name.
            action: The classified action.
            resource: The classified resource.
            verdict: The constraint verdict.
            arguments: The original tool call arguments.
        """
        if self.deliberation_engine is None:
            return

        try:
            observation = (
                f"Tool call: {tool_name} -> {verdict.level.value} "
                f"(dimension={verdict.dimension}, action={action}"
            )
            if resource:
                observation += f", resource={resource}"
            observation += ")"

            self.deliberation_engine.record_observation(
                observation=observation,
                actor="ai",
            )
        except Exception as exc:
            logger.warning("Failed to capture deliberation record: %s", exc)

    # ------------------------------------------------------------------
    # MCP server lifecycle (M04-01)
    # ------------------------------------------------------------------

    async def _connect_downstream_servers(self) -> None:
        """Connect to all downstream MCP tool servers.

        For each configured server, launches the process and establishes
        an MCP client session. Discovers and registers all tools.
        """
        try:
            from mcp import ClientSession, StdioServerParameters, stdio_client
        except ImportError:
            logger.warning(
                "MCP Python SDK not available. Downstream server "
                "connections will not be established. Install with: "
                "pip install mcp"
            )
            return

        if self._exit_stack is None:
            self._exit_stack = AsyncExitStack()
            await self._exit_stack.__aenter__()

        for server in self.downstream:
            try:
                params = StdioServerParameters(
                    command=server.command,
                    args=server.args,
                    env=server.env,
                )

                # stdio_client is an async context manager that yields
                # (read_stream, write_stream)
                streams = await self._exit_stack.enter_async_context(stdio_client(params))
                read_stream, write_stream = streams

                # Create and initialize the client session
                session = await self._exit_stack.enter_async_context(
                    ClientSession(read_stream, write_stream)
                )
                await session.initialize()

                self._client_sessions[server.name] = session

                # Discover and register tools
                tools_result = await session.list_tools()
                tools = []
                for tool in tools_result.tools:
                    tool_dict = {
                        "name": tool.name,
                        "description": tool.description or "",
                        "inputSchema": (tool.inputSchema if hasattr(tool, "inputSchema") else {}),
                    }
                    tools.append(tool_dict)

                self.register_tools(server.name, tools)
                logger.info(
                    "Connected to downstream server '%s': %d tools discovered",
                    server.name,
                    len(tools),
                )

            except Exception as exc:
                logger.error(
                    "Failed to connect to downstream server '%s' (%s %s): %s",
                    server.name,
                    server.command,
                    " ".join(server.args),
                    exc,
                )

    async def start(self) -> None:
        """Start the proxy: connect to downstream servers and serve on stdio.

        The proxy runs an MCP server on stdin/stdout. The AI connects to
        this proxy, and the proxy forwards (filtered) tool calls to
        downstream servers.
        """
        # Connect to downstream servers first
        await self._connect_downstream_servers()

        # Start the MCP server on stdio
        try:
            from mcp.server import Server
            from mcp.server.stdio import stdio_server
            from mcp import types
        except ImportError:
            logger.error(
                "MCP Python SDK is required for stdio proxy mode. " "Install with: pip install mcp"
            )
            # Fall back to JSON-RPC stdio loop
            await self._jsonrpc_stdio_loop()
            return

        server = Server("praxis-proxy")

        proxy = self  # capture for closures

        @server.list_tools()
        async def handle_list_tools() -> list[types.Tool]:
            """Return the merged tool catalog."""
            result = []
            for tool_dict in proxy.get_tools():
                result.append(
                    types.Tool(
                        name=tool_dict["name"],
                        description=tool_dict.get("description", ""),
                        inputSchema=tool_dict.get("inputSchema", {}),
                    )
                )
            return result

        @server.call_tool()
        async def handle_call_tool(name: str, arguments: dict | None) -> list[types.TextContent]:
            """Intercept tool calls through the trust layer."""
            args = arguments or {}
            result = await proxy.handle_tool_call(name, args)

            if result.error:
                return [types.TextContent(type="text", text=result.error)]

            if result.response is not None:
                if isinstance(result.response, dict):
                    text = json.dumps(result.response, indent=2)
                else:
                    text = str(result.response)

                # Prepend warning for flagged actions
                if result.verdict.level == GradientLevel.FLAGGED:
                    warning = (
                        f"[WARNING: {result.verdict.dimension} constraint at "
                        f"{result.verdict.utilization:.0%} utilization]\n"
                    )
                    text = warning + text

                return [types.TextContent(type="text", text=text)]

            return [types.TextContent(type="text", text="Tool call completed.")]

        # Run the server with stdio transport
        async with stdio_server() as (read_stream, write_stream):
            init_options = server.create_initialization_options()
            await server.run(read_stream, write_stream, init_options)

    # Maximum allowed size for a single JSON-RPC line (10 MB)
    _MAX_LINE_SIZE = 10 * 1024 * 1024

    async def _jsonrpc_stdio_loop(self) -> None:
        """Fallback: simple JSON-RPC 2.0 loop over stdin/stdout.

        Used when the MCP Python SDK is not available. Reads JSON-RPC
        requests from stdin and writes responses to stdout.

        Lines exceeding _MAX_LINE_SIZE (10 MB) are silently dropped
        to prevent memory exhaustion from oversized input.
        """
        logger.info("Starting JSON-RPC stdio proxy (MCP SDK fallback)")

        reader = asyncio.StreamReader()
        protocol = asyncio.StreamReaderProtocol(reader)
        await asyncio.get_event_loop().connect_read_pipe(lambda: protocol, sys.stdin.buffer)

        transport, _ = await asyncio.get_event_loop().connect_write_pipe(
            asyncio.BaseProtocol, sys.stdout.buffer
        )

        while True:
            try:
                line = await reader.readline()
                if not line:
                    break

                if len(line) > self._MAX_LINE_SIZE:
                    logger.warning(
                        "JSON-RPC input line exceeds %d bytes (%d bytes) — dropping",
                        self._MAX_LINE_SIZE,
                        len(line),
                    )
                    continue

                request = json.loads(line.decode("utf-8").strip())
                response = await self._handle_jsonrpc_request(request)
                if response is not None:
                    output = json.dumps(response) + "\n"
                    transport.write(output.encode("utf-8"))

            except json.JSONDecodeError:
                continue
            except Exception as exc:
                logger.error("JSON-RPC loop error: %s", exc)
                break

    async def _handle_jsonrpc_request(self, request: dict) -> dict | None:
        """Handle a single JSON-RPC 2.0 request.

        Supports:
            - tools/list: Return the merged tool catalog
            - tools/call: Intercept and evaluate tool calls

        Args:
            request: The parsed JSON-RPC request dict.

        Returns:
            JSON-RPC response dict, or None for notifications.
        """
        req_id = request.get("id")
        method = request.get("method", "")
        params = request.get("params", {})

        if method == "tools/list":
            tools = self.get_tools()
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {"tools": tools},
            }

        if method == "tools/call":
            tool_name = params.get("name", "")
            arguments = params.get("arguments", {})

            result = await self.handle_tool_call(tool_name, arguments)

            if result.error:
                return {
                    "jsonrpc": "2.0",
                    "id": req_id,
                    "result": {
                        "content": [{"type": "text", "text": result.error}],
                        "isError": True,
                    },
                }

            content_text = ""
            if result.response is not None:
                if isinstance(result.response, dict):
                    content_text = json.dumps(result.response, indent=2)
                else:
                    content_text = str(result.response)

            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "content": [{"type": "text", "text": content_text}],
                },
            }

        if method == "initialize":
            return {
                "jsonrpc": "2.0",
                "id": req_id,
                "result": {
                    "protocolVersion": "2024-11-05",
                    "capabilities": {"tools": {}},
                    "serverInfo": {
                        "name": "praxis-proxy",
                        "version": "0.1.0",
                    },
                },
            }

        # Unknown method
        return {
            "jsonrpc": "2.0",
            "id": req_id,
            "error": {
                "code": -32601,
                "message": f"Method not found: {method}",
            },
        }

    async def shutdown(self) -> None:
        """Cleanly shut down the proxy and all downstream connections."""
        if self._exit_stack is not None:
            await self._exit_stack.aclose()
            self._exit_stack = None
        self._client_sessions.clear()
        logger.info("Proxy shut down for session %s", self.session_id)
