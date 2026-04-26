# edictum-schemas

edictum-schemas is the shared schema and conformance source for Edictum's
agency-control documents: Rulesets and Workflows.

Edictum is the agency control layer for production AI agents. Agent frameworks
build the agent. Edictum bounds the agency.

Edictum turns documented agent profiles into executable runtime boundaries. It
makes any agency level defensible; Medium Agency is the enterprise demand
center right now, not the whole product.

Rulesets are one primitive: they define single-call boundaries. Workflows define
stage, order, evidence, and approval boundaries. Workflow Gates enforce ordered
process with evidence and approvals. Together they make declared agent profiles
executable across Python, TypeScript, and Go.

Edictum measures behavioral conformance to a declared profile. It does not
replace output-quality evals such as accuracy, relevance, coherence, or answer
quality.

## Schema

The schema defines the structure for Edictum YAML Rulesets (`edictum/v1`
`Ruleset`), including pre/post/session/sandbox rule types, expression
operators, and observability configuration.

**v2 schema** is the canonical schema and uses the developer-facing terms:
- `rules:`
- `action:`
- `action: block`
- `action: ask`
- `kind: Ruleset`

`schemas/edictum-v2.schema.json` is the canonical file exported by this package and loaded by the Python helper.
`schemas/edictum-v1.schema.json` is retained only as a deprecated compatibility alias for consumers that still reference the historical v1 schema identifier. SDK-level backward compatibility lives in the language implementations, not in a separate canonical v1 schema.

## Conformance Fixtures

These fixtures prove behavioral conformance is the same across SDKs. They cover
stage progression, approval, evidence, reset, and blocked actions.

Shared workflow gate fixtures for Spec 008 live under
[`fixtures/workflow/`](fixtures/workflow/README.md).

Workflow-specific `coding-guard` fixtures for Spec 017 P7 live under
[`fixtures/workflow-coding-guard/`](fixtures/workflow-coding-guard/README.md).

## Install

### Node.js (pnpm)

```bash
pnpm add @edictum/schemas
```

```js
import schema from "@edictum/schemas";
```

### Python (pip / uv)

```bash
pip install edictum-schemas
# or
uv add edictum-schemas
```

```python
from edictum_schemas import load_schema, schema_path

schema = load_schema()       # dict
path = schema_path()         # pathlib.Path
```

## License

MIT
