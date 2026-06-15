# symbolic_math_mcp Guide

Use the `symbolic_math_mcp` tool `check_symbolic_math(filepath)` when you need to validate a symbolic math YAML proof file.

## Tool Contract

- input: an ABSOLUTE filepath with filename ending in `.yaml`. DO NOT USE RELATIVE filepath
- output: a JSON object with `status`, `filename`, and `result`
Proof is valid
{
  "status": "Tool call completed!",
  "filename": "",
  "result": "Math proofs are valid"
}

Proof is invalid
{
  "status": "Tool call completed!",
  "filename": "",
  "result": "Error! Math proofs are invalid"
}
