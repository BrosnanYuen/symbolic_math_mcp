"""FastMCP server wiring."""

from __future__ import annotations

from fastmcp import FastMCP

from .config import ServerConfig
from .service import SymbolicMathService


def create_mcp_server(config: ServerConfig, service: SymbolicMathService | None = None) -> FastMCP:
    """Build the FastMCP server instance."""
    active_service = service or SymbolicMathService(
        max_requests=config.max_requests,
        total_timeout=config.total_timeout,
    )
    mcp = FastMCP(
        config.mcp_server_name,
        instructions=(
            "Use check_symbolic_math(filename) to synchronously validate a symbolic math YAML file. "
            "This server returns structured status, filename, and verifier result fields."
        ),
    )

    @mcp.tool(name="check_symbolic_math", description="Validate a .yaml symbolic math proof file.", run_in_thread=True)
    def check_symbolic_math(filename: str) -> dict[str, str]:
        return active_service.check_symbolic_math(filename)

    return mcp
