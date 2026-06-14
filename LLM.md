# LLM Tool Calling Guide

Use the MCP tool `check_symbolic_math(filename)` when you need to validate a symbolic math YAML proof file.

## Tool Contract

- input: a filename ending in `.yaml`
- output: a JSON object with `status`, `filename`, and `result`
- success does not always mean the math is valid
  the MCP call itself is successful whenever the server returns a completion payload
  inspect `result`

## Prompt For OpenCode

```text
If you need to verify a symbolic math YAML proof, call the MCP tool check_symbolic_math(filename).
Pass the exact .yaml file path.
After the tool returns, report the result field verbatim and summarize whether the proof is valid.
```

## Prompt For Claude Code

```text
When a task involves a symbolic math proof in YAML format, use the MCP tool check_symbolic_math(filename) before reasoning further.
Treat the tool result as authoritative.
If result equals "Math proofs are valid", the proof passed validation.
Otherwise, quote the returned error string and explain that validation failed.
```

## Prompt For OpenAI Codex

```text
For symbolic math YAML verification tasks, use the MCP tool check_symbolic_math(filename).
Provide the file path exactly.
Wait for the synchronous tool response, then use the returned result string as the final verification outcome.
Do not re-implement the validator in the prompt.
```
