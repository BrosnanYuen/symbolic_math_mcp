from __future__ import annotations

import asyncio
import json
import shutil
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
                    self.assertIn("check_symbolic_math_parallel", tool_names)

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

                    valid_dir = Path(tmpdir) / "parallel_valid"
                    invalid_dir = Path(tmpdir) / "parallel_invalid"
                    valid_dir.mkdir()
                    invalid_dir.mkdir()

                    for yaml_path in sorted(FIXTURE_DIR.glob("valid_*.yaml")):
                        shutil.copyfile(yaml_path, valid_dir / yaml_path.name)
                    for yaml_path in sorted(FIXTURE_DIR.glob("invalid_*.yaml")):
                        shutil.copyfile(yaml_path, invalid_dir / yaml_path.name)

                    valid_response = await client.call_tool(
                        "check_symbolic_math_parallel",
                        {"dir_path": str(valid_dir.resolve())},
                    )
                    valid_payload = valid_response.structured_content or valid_response.data
                    self.assertIsInstance(valid_payload, dict)
                    self.assertEqual("Parallel Tool call completed!", valid_payload["status"])
                    self.assertEqual(str(valid_dir.resolve()), valid_payload["dir_path"])
                    self.assertEqual(5, len(valid_payload["result"]))
                    self.assertTrue(
                        all(result == "Math proofs are valid" for result in valid_payload["result"].values())
                    )

                    invalid_response = await client.call_tool(
                        "check_symbolic_math_parallel",
                        {"dir_path": str(invalid_dir.resolve())},
                    )
                    invalid_payload = invalid_response.structured_content or invalid_response.data
                    self.assertIsInstance(invalid_payload, dict)
                    self.assertEqual("Parallel Tool call completed!", invalid_payload["status"])
                    self.assertEqual(str(invalid_dir.resolve()), invalid_payload["dir_path"])
                    self.assertEqual(5, len(invalid_payload["result"]))
                    self.assertTrue(
                        all(result != "Math proofs are valid" for result in invalid_payload["result"].values())
                    )

        asyncio.run(scenario())
