# Edictum Shared Test Fixtures

Cross-language behavioral and adversarial test specs for `edictum/v1` contract evaluation.
Every language implementation (Python, TypeScript, Go) **must** pass all fixtures in this directory.

## Fixture Format

Each `.fixtures.yaml` or `.adversarial.yaml` file follows this structure:

```yaml
suite: <suite-name>          # Unique suite identifier
version: 1                   # Fixture format version
description: "..."           # What the suite tests

fixtures:
  - id: "<suite>-NNN"        # Unique fixture ID
    description: "..."       # What this single case tests

    contract:                 # A valid edictum/v1 ContractBundle
      apiVersion: edictum/v1
      kind: ContractBundle
      metadata:
        name: test-bundle
      defaults:
        mode: enforce
      contracts:
        - ...                 # One or more contracts

    envelope:                 # The tool call being evaluated
      tool_name: "ToolName"
      arguments:
        key: "value"

    # For session fixtures, supply session state instead of envelope:
    session:
      tool_calls: 5           # Current call count
      per_tool:               # Optional per-tool counts
        Bash: 3

    expected:
      verdict: allowed | denied | warned | redacted | error
      message_contains: "..."     # Optional: substring in verdict message
      audit_action: "..."         # Optional: expected audit action tag
```

## Fields

| Field              | Required | Description                                                |
| ------------------ | -------- | ---------------------------------------------------------- |
| `contract`         | yes      | Full `ContractBundle` — must validate against the schema   |
| `envelope`         | varies   | Tool call envelope; required for pre/post/sandbox fixtures |
| `session`          | varies   | Session state; required for session fixtures                |
| `result`           | varies   | Tool result; required for postcondition fixtures           |
| `expected.verdict` | yes      | The expected evaluation outcome                            |

## Verdicts

| Verdict    | Meaning                                            |
| ---------- | -------------------------------------------------- |
| `allowed`  | Tool call passes all contracts                     |
| `denied`   | Tool call blocked by a contract                    |
| `warned`   | Postcondition matched with `warn` effect           |
| `redacted` | Postcondition matched with `redact` effect         |
| `error`    | Evaluation itself failed (malformed input, etc.)   |

## How Each Language Runs These

Each implementation should:

1. **Discover** all `*.fixtures.yaml` and `*.adversarial.yaml` files under `fixtures/`.
2. **Parse** each file and iterate over the `fixtures` array.
3. **Load** the `contract` field as a `ContractBundle`.
4. **Evaluate** the contract against the `envelope` (and `result`/`session` where applicable).
5. **Assert** that the actual verdict matches `expected.verdict`.
6. **Assert** that `expected.message_contains` (if present) is a substring of the verdict message.
7. **Assert** that `expected.audit_action` (if present) matches the audit trail action.

### Python

```python
import yaml, glob, pytest

@pytest.mark.parametrize("fixture", load_all_fixtures())
def test_fixture(fixture):
    bundle = load_bundle(fixture["contract"])
    verdict = evaluate(bundle, fixture["envelope"])
    assert verdict.status == fixture["expected"]["verdict"]
```

### TypeScript

```typescript
import { describe, it, expect } from "vitest";
import { loadFixtures } from "./helpers";

for (const f of loadFixtures()) {
  it(f.id, () => {
    const bundle = loadBundle(f.contract);
    const verdict = evaluate(bundle, f.envelope);
    expect(verdict.status).toBe(f.expected.verdict);
  });
}
```

### Go

```go
func TestFixtures(t *testing.T) {
    for _, f := range loadFixtures(t) {
        t.Run(f.ID, func(t *testing.T) {
            bundle := loadBundle(t, f.Contract)
            verdict := evaluate(bundle, f.Envelope)
            assert.Equal(t, f.Expected.Verdict, verdict.Status)
        })
    }
}
```

## Contract Between Fixture and Implementation

1. **Fixtures are authoritative** — if a fixture says the verdict is `denied`, your implementation must produce `denied`. A failing fixture is a bug in the implementation, not the fixture.
2. **Fixtures are minimal** — each tests exactly ONE behavior. Do not infer additional behaviors.
3. **Contracts in fixtures are schema-valid** — every `contract` block validates against `schemas/edictum-v1.schema.json`.
4. **Adversarial fixtures test security boundaries** — implementations MUST handle malicious input safely (no crashes, no bypasses).
5. **New fixtures require all implementations to update** — adding a fixture is a cross-repo contract change.
