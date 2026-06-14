from __future__ import annotations

import asyncio
import json
import tempfile
import unittest
from pathlib import Path

from fastmcp.client import Client, PythonStdioTransport


PROJECT_ROOT = Path(__file__).resolve().parents[1]
RUNNER = PROJECT_ROOT / "run_server.py"
PYTHON_BIN = PROJECT_ROOT.parent / ".venv" / "bin" / "python"
FIXTURE_DIR = PROJECT_ROOT / "tests_yaml"


class TestMcpIntegration(unittest.TestCase):
    def test_check_symbolic_math_end_to_end(self) -> None:
        async def scenario() -> None:
            with tempfile.TemporaryDirectory() as tmpdir:
                config_path = Path(tmpdir) / "config.json"
                config_path.write_text(
                    json.dumps(
                        {
                            "mcp_server_name": "Integration Test Server",
                            "mcp_server_url": "stdio://local",
                            "max_requests": 2,
                            "total_timeout": 30,
                        }
                    ),
                    encoding="utf-8",
                )
                transport = PythonStdioTransport(
                    script_path=RUNNER,
                    args=["--config", str(config_path)],
                    cwd=str(PROJECT_ROOT),
                    python_cmd=str(PYTHON_BIN),
                )
                async with Client(transport) as client:
                    tools = await client.list_tools()
                    tool_names = {tool.name for tool in tools}
                    self.assertIn("check_symbolic_math", tool_names)

                    for yaml_path in sorted(FIXTURE_DIR.glob("valid_*.yaml")):
                        response = await client.call_tool(
                            "check_symbolic_math",
                            {"filename": str(yaml_path)},
                        )
                        payload = response.structured_content or response.data
                        self.assertIsInstance(payload, dict)
                        self.assertEqual("Tool call completed!", payload["status"])
                        self.assertEqual("Math proofs are valid", payload["result"])

                    for yaml_path in sorted(FIXTURE_DIR.glob("invalid_*.yaml")):
                        response = await client.call_tool(
                            "check_symbolic_math",
                            {"filename": str(yaml_path)},
                        )
                        payload = response.structured_content or response.data
                        self.assertIsInstance(payload, dict)
                        self.assertEqual("Tool call completed!", payload["status"])
                        self.assertNotEqual("Math proofs are valid", payload["result"])

        asyncio.run(scenario())
