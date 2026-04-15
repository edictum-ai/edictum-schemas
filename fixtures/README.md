# Edictum Shared Test Fixtures

Cross-language shared fixtures for `edictum/v1` ruleset evaluation and workflow
conformance.

Every language implementation (Python, TypeScript, Go) should discover and run
the fixture classes that apply to its runtime surface.

## Directory Layout

- `behavioral/`: shared ruleset evaluation cases
- `adversarial/`: hostile input cases that must not bypass enforcement
- `rejection/`: malformed rulesets that loaders must reject
- `workflow/`: Spec 008 workflow runtime cases
- `workflow-adapter-conformance/`: Spec 017 P6 adapter audit and lineage cases
- `workflow-coding-guard/`: Spec 017 P7 coding-guard workflow cases
- `workflow-v0.18/`: v0.18 shared-semantics additions (wildcard tools, terminal stage, MCP result evidence, extends inheritance)

## Ruleset Evaluation Fixtures

The ruleset-evaluation suites use the established file classes:

- `*.fixtures.yaml`
- `*.adversarial.yaml`
- `*.rejection.yaml`

These suites keep their existing wire-format field names for compatibility.
That means some literal keys still use older names such as `contract`,
`bundle`, and `expected.verdict: denied`. Treat those as stable fixture keys,
not preferred prose.

Each `*.fixtures.yaml` or `*.adversarial.yaml` file follows this structure:

```yaml
suite: <suite-name>          # Unique suite identifier
version: 1                   # Fixture format version
description: "..."           # What the suite tests

fixtures:
  - id: "<suite>-NNN"        # Unique fixture ID
    description: "..."       # What this single case tests

    contract:                 # Existing field name; contains a valid Ruleset
      apiVersion: edictum/v1
      kind: Ruleset
      metadata:
        name: test-ruleset
      defaults:
        mode: enforce
      rules:
        - ...

    envelope:                 # The tool call being evaluated
      tool_name: "ToolName"
      arguments:
        key: "value"

    # For session fixtures, supply session state instead of envelope:
    session:
      tool_calls: 5
      per_tool:
        Bash: 3

    expected:
      verdict: allowed | denied | warned | redacted | error
      message_contains: "..."     # Optional stable substring
      audit_action: "..."         # Optional expected audit action tag
```

## Ruleset Evaluation Fields

| Field              | Required | Description                                           |
| ------------------ | -------- | ----------------------------------------------------- |
| `contract`         | yes      | Existing field name for the schema-valid `Ruleset`    |
| `envelope`         | varies   | Tool call input for pre/post/sandbox fixtures         |
| `session`          | varies   | Session counters for session-limit fixtures           |
| `result`           | varies   | Tool result for post-rule fixtures                    |
| `expected.verdict` | yes      | Expected outcome for the fixture                      |

## Ruleset Evaluation Verdicts

| Verdict    | Meaning                                                    |
| ---------- | ---------------------------------------------------------- |
| `allowed`  | Tool call passes the evaluated rules                       |
| `denied`   | Legacy fixture value meaning the call was blocked          |
| `warned`   | Post-rule matched with `action: warn`                      |
| `redacted` | Post-rule matched with `action: redact`                    |
| `error`    | Evaluation failed because the input was malformed          |

## Workflow Fixtures

Workflow runtime fixtures live under [`workflow/`](workflow/README.md) and use a
dedicated format for stage progression, approval gating, and evidence updates.

## Workflow Adapter Conformance Fixtures

Workflow adapter conformance fixtures live under
[`workflow-adapter-conformance/`](workflow-adapter-conformance/README.md).
They extend the workflow fixture model with approval loop inputs,
programmatic stage-move steps, session lineage, and ordered audit-event
expectations for Spec 017 P6.

## Workflow Coding-Guard Fixtures

Workflow-specific coding-guard fixtures live under
[`workflow-coding-guard/`](workflow-coding-guard/README.md).
They reuse the workflow fixture state model and add approval loop inputs plus
operator reset steps for Spec 017 P7.

## Workflow v0.18 Fixtures

v0.18 shared-semantics fixtures live under
[`workflow-v0.18/`](workflow-v0.18/README.md).
They cover four additions: wildcard prefix support in `stage.tools`, the
`terminal: true` stage primitive, MCP result evidence recording and the
`mcp_result_matches(...)` gate condition, and `extends:` ruleset inheritance.

## Shared Contract

1. Fixtures are authoritative. If a fixture says a call is blocked, paused, or
   allowed, the implementation should match it.
2. Fixtures are minimal. Each case should cover one behavior.
3. Rulesets embedded in fixtures should stay schema-valid.
4. Workflow fixtures should assert stable public behavior, not SDK-internal
   helper structure.
5. Adding or changing fixtures is a cross-repo contract change for the SDKs.
