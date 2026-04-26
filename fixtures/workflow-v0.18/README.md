# Workflow v0.18 Fixtures

These fixtures prove behavioral conformance is the same across SDKs for the
four v0.18 shared-semantics additions.

Each file in this directory locks one semantic, keeping cases minimal and
portable across Python, Go, and TypeScript runtimes.

## Files

| File | Semantics locked |
| ---- | --------------- |
| `wildcard-tools.workflow-v0.18.yaml` | Wildcard prefix matching in `stage.tools` |
| `terminal-stage.workflow-v0.18.yaml` | `terminal: true` stage primitive |
| `mcp-result-evidence.workflow-v0.18.yaml` | MCP result evidence recording and `mcp_result_matches(...)` gate condition |
| `extends-inheritance.workflow-v0.18.yaml` | `extends:` ruleset inheritance |

## Format

Workflow fixture files follow the format documented in
[`workflow/README.md`](../workflow/README.md).

The `extends-inheritance` file adds a `rulesets:` top-level section, analogous
to the `workflows:` section used by workflow fixture files. Its fixture
document reference field may be either an inline Ruleset object or a string name
referencing a named entry in `rulesets:`. Runtimes resolve the `extends:`
field before evaluation.

## Evidence Extensions for MCP Results

The `mcp-result-evidence` file extends the evidence model with an
`mcp_results` map:

```yaml
evidence:
  reads: []
  stage_calls: {}
  mcp_results:
    mcp__ci__status:
      - outcome: passing
        branch: main
```

Step fixtures that drive an MCP call include a `mcp_result:` field specifying
what the tool returned. Runtimes must record the result as evidence only after
a `success` execution.

## Wildcard Syntax

Wildcards in `stage.tools` use fnmatch-style prefix patterns:

- `mcp__*` — any tool whose name starts with `mcp__`
- `mcp__ci__*` — any tool whose name starts with `mcp__ci__`
- Exact names like `Read`, `Edit`, and wildcard patterns may be mixed freely

## Terminal Stage Semantics

A stage with `terminal: true`:

- Has no implicit successor; the workflow ends when this stage is reached
- If `tools` is omitted, all tool calls while in this stage are blocked
- If `tools` is present, only those tools are allowed while the stage is active
- Once the stage's `exit` conditions are met (or the stage has no `exit`),
  any subsequent tool call is blocked with a "workflow complete" reason
- A prior no-exit stage that auto-advances into a terminal stage causes the
  triggering call to be blocked in the terminal stage context
