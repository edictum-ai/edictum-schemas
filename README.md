# edictum-schemas

Single source of truth for Edictum schema artifacts and shared conformance fixtures, consumed by the Go, Python, and TypeScript SDKs.

## Schema

The schema defines the structure for Edictum YAML contract bundles (`edictum/v1` `ContractBundle`), including pre/post/session/sandbox contract types, expression operators, and observability configuration.

## Conformance Fixtures

Shared workflow gate fixtures for Spec 008 live under [`fixtures/workflow/`](fixtures/workflow/README.md).

They define implementation-agnostic stage progression, approval, and evidence cases so each SDK can validate the same runtime semantics.

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
